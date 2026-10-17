# 0006. Select the pilot baseline models

- **Status:** Accepted 2026-10-17 for the pilot v1 baseline (D21-19): the owner
  accepted the measured 36 GB fit with an explicit swap/pressure limitation and
  approved this text.
- **Date:** 2026-10-13; attempts recorded 2026-10-14 to 2026-10-17
- **Reading order:** sections are chronological and record status as of their
  dates. Where a later section closes an earlier open item (Metal offload,
  build/phase evidence, the fit decision), the later section governs; items it
  does not close, such as whole-system Memory Used and the extractor's local
  token counts, stay open. "36 GB" and "36 GiB" both mean this host's
  38,654,705,664 bytes.
- **Decider:** Lowell Mason
- **Scope:** Stage 11 pilot v1 feasibility baseline; no production selection

## Context and decision boundary

Plan 21 B1 requires Gemma as extractor/classifier and two self-hosted judges from
different non-Gemma families. Both judges and MiniCheck must be resident together
within 36 GB; actual Python scorer/tokenizer residency must be measured. Gemma's
phase must also fit within 36 GB. No model comparison, prompt revision, hosted
call or concurrent pilot worker is authorized here. Structure-aware traversal
remains the baseline; whole-document processing is a later measured ablation.

The owner selected Qwen2.5-14B-Instruct and Mistral-Nemo-Instruct-2407, both
Q4_K_M, and supplied inventories and serving choices on 2026-10-13. This ADR
records that selection while retaining [ADR 0004](0004-use-a-local-open-weight-model-for-the-extractors-live-test.md)
and [ADR 0005](0005-adopt-local-minicheck-for-support-signals.md). Final numeric
baseline ceilings are owner-selected below. O2 provisional smoke authorization was
approved on 2026-10-13. Metadata and earlier stages' checks do not discharge the
fixture-smoke requirement; the measured `s11-fixture-5` pass below does, and the
owner accepted its fit on 2026-10-17.

**Decision.** Gemma 4 31B-it (Q4_0) is the extractor and classifier; Qwen2.5-14B-
Instruct and Mistral-Nemo-Instruct-2407 (both Q4_K_M) are the two judges; MiniCheck
is the raw support scorer and DeBERTa its explicit alternative; all are self-hosted
under llama.cpp build 11146 or CPU float32 as recorded below. This is the pilot v1
feasibility baseline only, not a production model selection.

## Selected identities and roles

| Role | Model / served ID | Weight revision | Original/tokenizer revision |
| --- | --- | --- | --- |
| Extractor and classifier | Gemma 4 31B-it / `gemma-4-31b-it-qat-q4_0` | `59dde24573e7e61570dba08b18a2e1fe246955ed` | `842da3794eaa0b77d5f08bae87a17459d91ff475` |
| Judge A | Qwen2.5-14B-Instruct / `pilot-v1-qwen2.5-14b-q4_k_m` | `05244aa5d871c661c80082a15d3bce44714d068d` | `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8` |
| Judge B | Mistral-Nemo-Instruct-2407 / `pilot-v1-mistral-nemo-12b-q4_k_m` | `a2dd64a0a76ea1bdb2bb6ab6fa5496b003c7c908` | `04d8a90549d23fc6bd7f642064003592df51e9b3` |
| Primary raw support scorer | `lytang/MiniCheck-Flan-T5-Large` | `96eafd01cee2d16cf81aaa2fb226b14f422a37b3` | Same pinned checkpoint |
| Explicit alternative raw support scorer | `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli` | `6f5cf0a2b59cabb106aca4c287eed12e357e90eb` | Same pinned checkpoint |

`config/models/pilot-v1-runtime.toml` assigns `pilot-v1-gemma.toml` to both
extractor and classifier, `pilot-v1-judge-a.toml` and `pilot-v1-judge-b.toml` as
judges, `pilot-v1-minicheck.toml` as scorer and `pilot-v1-deberta.toml` as
alternative scorer. A failed primary does not automatically select its alternative.
Gemma's GGUF revision/hash remain unchanged; its original/tokenizer revision is
owner-reported separately, with `GemmaTokenizer` and `chat_template.jinja`.

## Runtime and selected serving settings

The owner reports llama.cpp `0.5.0 (build 11146, commit 7fe450e19)`, built with
AppleClang `21.0.0.21000334` on Darwin arm64. All three chat configurations request
Metal GPU offload, one slot, context 8,192, input limit 6,144, output limit 2,048,
300-second timeout and JSON-schema structured output as selected on 2026-10-13.
The owner subsequently selected Gemma context/total input 12,288 on 2026-10-14;
judge contexts/total input remain 8,192/6,144. Gemma precision is Q4_0;
both judges use Q4_K_M. Loopback serving ports are 8080, 8081 and 8082 respectively.
Gemma remains text only, without a vision projector, and reasoning off per
ADR 0004. Actual server behavior was then measured by the fixture passes below.

Both scorers use CPU float32, input limit 512 and the owner-reported installed
versions torch `2.14.1`, transformers `5.18.0`, sentencepiece `0.2.2`, tokenizers
`0.23.2`, safetensors `0.8.0`. These preserve ADR 0005's pins. MiniCheck retains
`minicheck-first-step/1`, label mapping `[3,209]`, `predict: ` + premise + EOS +
hypothesis, and first-decoder-position raw softmax index 1. Its native
`pytorch_model.bin` loads with `use_safetensors=False`, `weights_only=True`.
DeBERTa retains `deberta-pair/1`, complete pair encoding, native safetensors,
mapping `[0,1,2]` (entailment, neutral, contradiction), and raw softmax index 0.
Remote/custom code stays disabled. These are raw signals, not theme decisions.

ADR 0005's Python 3.14 JIT warning and eager-path limitation remain applicable;
this selection does not establish MPS scorer compatibility or broader platform
support. No dependency change is selected.

## Rights evidence and approval boundary

The following is existing dated primary-source evidence, not a new license
verification in this metadata pass. The owner confirmed applicable weight and
base-model terms for intended local research use: Gemma and MiniCheck on
2026-10-05 (retained ADRs), both judges and DeBERTa on 2026-10-13. The prepared
TOMLs record these confirmations and local self-hosted earnings-theme feasibility
research as intended use. Free access and software licenses alone do not establish
weight rights or permission to redistribute underlying earnings documents.

| Model | Necessary license words | Primary evidence and recorded read date |
| --- | --- | --- |
| Gemma 4 | “Apache License 2.0” | [Google license page](https://ai.google.dev/gemma/docs/gemma_4_license), 2026-10-05; ADR 0004 also records its [model card](https://huggingface.co/google/gemma-4-31B-it), 2026-10-04 |
| Qwen2.5-14B-Instruct | “Apache 2.0” | [Pinned original card](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct/blob/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8/README.md), consulted 2026-10-13; recorded as Apache 2.0 in B1 evidence |
| Mistral-Nemo-Instruct-2407 | “Apache 2.0” | [Pinned original card](https://huggingface.co/mistralai/Mistral-Nemo-Instruct-2407/blob/04d8a90549d23fc6bd7f642064003592df51e9b3/README.md), consulted 2026-10-13; recorded as Apache 2.0 in B1 evidence |
| MiniCheck-Flan-T5-Large | `MIT` | [Pinned card](https://huggingface.co/lytang/MiniCheck-Flan-T5-Large/blob/96eafd01cee2d16cf81aaa2fb226b14f422a37b3/README.md), ADR 0005 metadata review and owner confirmation 2026-10-05; lineage google/flan-t5-large |
| DeBERTa alternative | `MIT` | [Pinned card](https://huggingface.co/MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli/blob/6f5cf0a2b59cabb106aca4c287eed12e357e90eb/README.md) and [Microsoft base-model card](https://huggingface.co/microsoft/deberta-v3-base/blob/main/README.md), read 2026-10-13 |

The Microsoft base-model link is mutable: the dated review does not make it an
immutable pin. Model-card license labels are limited evidence; the owner's
applicable model/base-model terms confirmation is separate. Published judge
weight hashes were checked through the [pinned Qwen GGUF page](https://huggingface.co/bartowski/Qwen2.5-14B-Instruct-GGUF/blob/05244aa5d871c661c80082a15d3bce44714d068d/Qwen2.5-14B-Instruct-Q4_K_M.gguf)
and [pinned Mistral GGUF page](https://huggingface.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF/blob/a2dd64a0a76ea1bdb2bb6ab6fa5496b003c7c908/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf)
in existing B1 evidence. This does not independently verify current local bytes.

For `s11-fixture-1`, the classifier/judge runtime checked `input_limit = 6144`
against prompt plus reserved completion. With `max_tokens = 2048`, those roles
permitted at most 4,096 prompt tokens; the 8,192 server context did not enlarge
that allowance. Following the owner selection below, Gemma's total allowance is
12,288 and its prompt allowance is 10,240. Judges retain total allowance 6,144,
prompt allowance 4,096 and server context 8,192.

## Owner-reported complete file identity

Two owner-terminal inventories dated 2026-10-13 enumerate 33 actual files:
Gemma five, Qwen six, Mistral seven, MiniCheck eight and DeBERTa seven. Agents
read returned metadata only; no model/tokenizer content was opened or independently
hashed. The five model TOMLs enumerate exactly these files without duplicates.
Gemma's weight matches ADR 0004 and all 15 scorer hashes match ADR 0005.
Native initialization still must check actual bytes against the manifests.

| Inventory role | File | Owner-reported SHA-256 |
| --- | --- | --- |
| Gemma weights | `gemma-4-31B_q4_0-it.gguf` | `179cfb99212709597eae5929112cfca677e1bbf566178b479ae1da0c4772874b` |
| Gemma tokenizer | `config.json` | `e967dd38bc5cfd38bd09a995a7bf4a754075df2b46aba68f7fbb5a791e6d8dd1` |
| Gemma tokenizer | `tokenizer.json` | `cc8d3a0ce36466ccc1278bf987df5f71db1719b9ca6b4118264f45cb627bfe0f` |
| Gemma tokenizer | `tokenizer_config.json` | `9f4fec4b1dc6ecddf8f4a92e9caea5971c0e67d81309f3f9066a2bee8c362633` |
| Gemma tokenizer | `chat_template.jinja` | `ae53464bf3be25802b3a5b37def7fd89667067d7577049b3b2d74c4d8de4c6d4` |
| judge a weights | `Qwen2.5-14B-Instruct-Q4_K_M.gguf` | `e47ad95dad6ff848b431053b375adb5d39321290ea2c638682577dafca87c008` |
| judge a tokenizer | `config.json` | `0f2085dbbe2ee251bd6a6a0797d84a6ce34436044d629aa3cba793b43d311a9e` |
| judge a tokenizer | `tokenizer.json` | `c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539` |
| judge a tokenizer | `tokenizer_config.json` | `5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583` |
| judge a tokenizer | `merges.txt` | `599bab54075088774b1733fde865d5bd747cbcc7a547c5bc12610e874e26f5e3` |
| judge a tokenizer | `vocab.json` | `ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910` |
| judge b weights | `Mistral-Nemo-Instruct-2407-Q4_K_M.gguf` | `7c1a10d202d8788dbe5628dc962254d10654c853cae6aaeca0618f05490d4a46` |
| judge b tokenizer | `config.json` | `8a42669219f4caadedb891be88c34712572573d42b3d02d665d527f92d94ddfe` |
| judge b tokenizer | `tokenizer.json` | `e11c71726323d33da7b8d6f6f269f1988931c0a52b7122bcdd8c05042974e0db` |
| judge b tokenizer | `tokenizer_config.json` | `67f3aeef765b7d78012a081dba98efd4900cd2bac24eac182296841c7e2aef2a` |
| judge b tokenizer | `merges.txt` | `4e4d41c64d2ed2e26713ae7af7c958b07df532a6f4498dffa9a2cf7f4c6c0aa6` |
| judge b tokenizer | `vocab.json` | `8572e8853a6b2f2d830de4afa15d43c49257d367abf3c5fd2f6f7687bcd8f63d` |
| judge b tokenizer | `special_tokens_map.json` | `6fa06efa2785e450051989a6f8fb4416b10149ded485ddd3f127a40734f5cfd0` |
| deberta | `added_tokens.json` | `dc046d04c9b0ada7ae6f1dc89c465801799acdf0c9a6aab8c15a1b2d5ca4e91f` |
| deberta | `config.json` | `a6c616d6dabeacf90fd0e776c741d3f0f30a05533ccf0bd3b5b62e94cfaa8d57` |
| deberta | `model.safetensors` | `06d6fd89edd4f97816831626daafbdb0b029cf63bae8edc0bccab1d64e2e7707` |
| deberta | `special_tokens_map.json` | `9463f61e1b109a8eb4688b829260d7c6b1e6dff04c98ff7269bb89e2b92369b9` |
| deberta | `spm.model` | `c679fbf93643d19aab7ee10c0b99e460bdbc02fedf34b92b05af343b4af586fd` |
| deberta | `tokenizer.json` | `05402ffae6dd382a8491b1d29bfc139bec5d332662e86a026f433ce54c25c202` |
| deberta | `tokenizer_config.json` | `557b3d33d3f41b81ad769244e506549e98a1857d41dd58160aacd4d98d710b5a` |
| minicheck | `added_tokens.json` | `4b1c1345a66fdd00264819c5adfc3142debfbd3b03767a04f95a39ac2277ca21` |
| minicheck | `config.json` | `d8e91aa8739d845d2572fa8db9cb6523d06208c14fedb8f7623f49283a305653` |
| minicheck | `generation_config.json` | `3c4ec6a75c47200afbecd413ee6719007f701821d07b6c11a6c30237d3f9c854` |
| minicheck | `pytorch_model.bin` | `41291881e13c6235ed47149cec903bee9493e45d9d7325587a9fa2e266c526c0` |
| minicheck | `special_tokens_map.json` | `47389dd56434a0d7d32f736ba34e895b331461980af760e955b62d5c39912626` |
| minicheck | `spiece.model` | `d60acb128cf7b7f2536e8f38a5b18a05535c9e14c7a355904270e15b0945ea86` |
| minicheck | `tokenizer.json` | `ece24e1e7d9b5a26f4e68a9519b6ea1451474811b52a9da419c9145f1f458fc0` |
| minicheck | `tokenizer_config.json` | `284a01dc7b81f159449b96cd0d8814f6da64bbdb59833fe3b8398ea36a860550` |

## Observed fixture attempt, 2026-10-14

The owner ran `s11-fixture-1` in iTerm and supplied closed statuses and numeric
output. The attempt observed two returned extractor calls, then refused with
`classification_incomplete_or_empty`. The support checkpoint was not reached.
This is an incomplete fixture smoke, not an all-role verification.

| Role | Call | Elapsed ms | Input tokens | Output tokens | Local input count | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Extractor | 1 | 47,766 | 1,633 | 636 | Unknown (`null`) | `returned` |
| Extractor | 2 | 24,390 | 894 | 305 | Unknown (`null`) | `returned` |

The two observed calls total 72,156 ms elapsed, 2,527 input tokens and 941 output
tokens (3,468 observed tokens). Owner-terminal wall time was 8 minutes 5.6 seconds.
The difference between call elapsed totals and wall time is unexplained; no
loading, throughput or other timing attribution is inferred.

Observed call counts are extractor 2; classifier 0; judge A 0; judge B 0;
MiniCheck 0; DeBERTa 0. These are observed dispatch counts, not evidence that
unexercised roles are unavailable. On 2026-10-14 the owner explicitly answered
“not captured” for the incomplete attempt's Gemma-phase memory measurement.
No measurement exists for that phase in this record; no fit result is inferred.
Actual server-build/phase confirmations remain absent. Tokenizer success, all-role
runtime compatibility, resident-memory fit and quality are not established by this
attempt. Both completed pure diagnostics are recorded below. The context gate
is the established classification-refusal cause. The owner-selected context and
single fresh attempt authorization are recorded below; later baseline ceiling
selection is recorded separately.

The attempt's local files are preserved; agents do not read them. The later pure
diagnostic establishes the context-gate cause below. No configuration, code or
budget change was applied by that diagnostic. The later owner-selected Gemma
context change and later baseline ceiling selection are recorded below.

### Pure source-resolution diagnostic, 2026-10-14

The owner supplied a completed pure resolution diagnostic for `s11-fixture-1`:
23 claims, one document, 24 quotes, 23 resolved, zero refused, and
`coding_error_reasons = {}`. Owner-terminal wall time was 10.2 seconds.
The supplied fixture SHA-256 is
`0bbccaa6c801a4eb354468c2f7320a33710f122f4d2b70219ce3c13fff185bdf`;
the supplied codebook SHA-256 is
`43f96f0e2a8aa58072eeee66a3ccad5bf8b34e90f39c2de87c75c8418c0ec49b`.
These are owner-reported diagnostic figures and identities; agents did not read
the attempt data.

This check rules out source-resolution refusal for the checked claims. The later
token/context/budget diagnostic establishes the classification-refusal cause below.
Pure resolution does not exercise native roles, establish memory fit or complete
B1. The owner's Gemma-phase memory answer remains “not captured”. No retry,
policy or budget change is authorized by this pure resolution check.

### Token/context/budget diagnostic and owner-selected context, 2026-10-14

The owner supplied the pure token/context/budget diagnostic for the same
`s11-fixture-1` artifacts: 23 claims, 23 counted, 23 failed, 23 over context and
zero within context. The context gate reported `input_too_long` for all 23.
Prompt-token minimum/maximum/sum were 6,736 / 7,975 / 160,238. With 2,048 reserved
output tokens per claim, required total minimum/maximum/sum were
8,784 / 10,023 / 207,342. Dry first-attempt reservations were zero requests and
zero tokens, confirming the context gate refused before request/token budgets.
Owner-terminal wall time was 34.7 seconds.

The context allowance is the established cause of classification refusal in this
attempt: the configured 6,144 total allowance permits only 4,096 prompt tokens,
and even the 8,192 server context is insufficient with reserved output. The
diagnostic retained the earlier fixture, codebook, limits and Gemma identities;
the supplied coding-prompt SHA-256 is
`c1e2bb1c2cb558ba2fc79fc5e088b1798a17c09b5086ae01e1d318e60ab0552c`.
This pure diagnostic does not exercise native classifier/judge/scorer calls or
establish quality, fit or completion. Gemma-phase memory remains “not captured”.

**Owner selection and single fresh attempt authorization, 2026-10-14:** the owner
selected Gemma server context 12,288 and total `input_limit` 12,288, retaining
output limit 2,048, and explicitly authorized one fresh `s11-fixture-2`.
That authorized attempt subsequently completed native fixture calls, as recorded
below; `s11-fixture-1` remains preserved. The reviewed Gemma TOML change has been applied: only `input_limit`
changes from 6,144 to 12,288. Its before SHA-256 is
`84339bbfaa1762db15a0aaf327a5fb1e8512f6c8d990cc09785e62e39e396a67`;
after SHA-256 is
`f9bdb3c65828e813f6ed85f64d996aa4253cd3695809d12ae6e959aa7abc2540`.
The selected 10,240-token prompt allowance leaves 2,265 tokens above the observed
maximum of 7,975. All other parameters, window budget 4,000, claim budget 500,
ceilings, prompts, codebook, model identity, judges and scorers remain unchanged.
Judge server contexts stay 8,192 and total allowances stay 6,144. The shipped
two-attempt rules and approved foreground-phase/memory evidence method are
retained. No server or smoke command has been executed by agents, and no plan or
limits input is changed.

The owner selection retains the same numeric limits input and SHA-256
`481394833468d21de0dff6b6c72d1fcfe0c53e67dee7fb7ee20da7449bf58bbd`.
For the observed 23 claims, first-attempt coding reservation accounting would be
207,342 tokens; two-attempt accounting is 414,684, below the existing 1,048,576
coding-token ceiling. These are diagnostic reservation calculations, not actual
native usage or final pilot workload estimates. Fresh generation may change the
claim count and prompts. No quality claim or final baseline budget approval
follows. Increased KV-cache residency requires actual owner measurement; no
memory fit is assumed. The focused owner O1/O2 choice authorizes only the selected
configuration and single fresh fixture attempt. Later baseline ceiling selection
is recorded separately; actual memory/build/phase evidence remains open.

## Completed native fixture smoke, 2026-10-14

The owner supplied safe terminal metadata for `s11-fixture-2`; its summary status
is `complete`. All six roles executed across 150 returned call rows, with no
failed call rows. The fixture SHA-256 is
`0bbccaa6c801a4eb354468c2f7320a33710f122f4d2b70219ce3c13fff185bdf`;
the returned identities snapshot SHA-256 is
`c8b78f428fae90dc045319326015b92ba7e14bc7bc34660ad06db5838c59d2e3`.
Agents read only safe metadata, not attempt payloads or model files.

| Role | Calls | Call elapsed range, ms | Total call elapsed, ms | Reported input tokens | Reported output tokens |
| --- | --- | --- | --- | --- | --- |
| extractor | 2 | 25,130–52,629 | 77,759 | 2,527 | 941 |
| classifier | 23 | 76,840–111,571 | 2,029,127 | 160,217 | 557 |
| judge_a | 41 | 6,813–20,440 | 566,876 | 65,016 | 4,976 |
| judge_b | 40 | 6,095–17,060 | 478,472 | 65,304 | 4,867 |
| minicheck | 22 | 175–12,252 | 117,587 | 1,317 | Unknown (`null`) |
| deberta | 22 | 29–2,291 | 9,903 | 1,292 | Unknown (`null`) |

Total measured call elapsed was 3,279,724 ms. Owner-terminal wall time was
1 hour 27 minutes 17.3 seconds (5,237.3 seconds). No explanation is assigned to
the difference. The 106 generative calls have complete usage: 293,064 input tokens
and 11,341 output tokens, totaling 304,405. The 44 non-generative NLI calls retain
`null` output usage; it is not fabricated as zero.

All 104 classifier/judge local prompt counts matched server-reported input
counts. The additional 44 NLI local input counts matched their reported counts.
Both extractor local input counts remain unknown (`null`). Qwen's 41 calls versus
Mistral's 40 may include an additional attempt, but no specific retry reason is
inferred. NLI call counts do not establish a target count. This fixture completion
is not a semantic-support, calibration or quality result.

B1 remains incomplete and ADR 0006 remains Draft. On 2026-10-14 the owner answered
“Not available” for `s11-fixture-2` memory evidence. The first attempt's Gemma-phase
memory remains “not captured”; both attempts lack measured memory evidence.
For the three server builds, Gemma stopped and both judges together question, the
owner answered exactly “None that I know of”. This records no known exceptions;
it is not affirmative build/phase proof. At that checkpoint, server-build/phase
confirmation and increased-context KV-memory fit remained open. Final baseline ceilings were
subsequently selected below. No further inference attempt is authorized by this
record. The owner subsequently selected one measured third fixture attempt,
recorded below; application review passed and native execution completed.

## Owner-selected final baseline ceilings, 2026-10-14

The owner explicitly selected the complete baseline limits JSON and approved its
rationale, SHA-256
`8fae7afbb60fe45e04e178c800f0ae87e5609423e0a65ad02840ead770d110cd`.
The approved copy exactly matches the reviewed proposal. This selects numeric
baseline ceilings; it does not close O1/O2 memory/build/phase evidence, accept this
ADR, complete B1, authorize pilot dispatch or begin B2. The fixture smoke limits
and their earlier hash remain separate historical execution input.

| Stage | Ceiling | Owner-selected value |
| --- | --- | --- |
| Extraction | `requests_per_document` | 32 |
| Extraction | `requests_per_run` | 640 |
| Extraction | `tokens_per_run` | 7,864,320 |
| Coding | `requests_per_claim` | 2 |
| Coding | `requests_per_document` | 128 |
| Coding | `requests_per_run` | 2,560 |
| Coding | `tokens_per_document` | 1,572,864 |
| Coding | `tokens_per_run` | 31,457,280 |
| Support | `scorer_per_target` | 16 |
| Support | `scorer_per_document` | 2,048 |
| Support | `scorer_per_run` | 40,960 |
| Support | `judge_per_target` | 8 |
| Support | `judge_per_document` | 1,024 |
| Support | `judge_per_run` | 20,480 |
| Support | `tokens_per_document` | 6,291,456 |
| Support | `tokens_per_run` | 125,829,120 |

All generation/traversal settings are retained: temperature 0, seed 0, maximum
output 2,048, structured output enabled, extraction window 4,000 characters and
claim limit 500 characters. Gemma context/total allowance stays 12,288; judge
contexts/total allowances stay 8,192/6,144; CPU float32 scorers retain input limit
512. Shipped two-attempt rules remain fixed.

The approved capacity rationale uses the larger 20-document train partition
for per-run ceilings; dev has eight documents, with one document per event.
Each stage/pass/fresh run has its own allowance; budgets are not pooled over the
lifetime of the study. Each of two support assessors has a separate allowance;
cache reuse is possible but not promised. Extraction capacity permits up to
16 planned windows at two attempts, with conservative context-sized accounting
640 × 12,288 = 7,864,320 tokens. Coding capacity covers 64 claims per document at
two attempts: 128 × 12,288 = 1,572,864 tokens per document and 31,457,280 per run.
Support capacity covers 128 targets per document at 16 scorer and eight judge
calls per target; reserved judge tokens are 1,024 × 6,144 = 6,291,456 per document
and 125,829,120 per run. Scorers charge zero allowance tokens while retaining
request counts and input figures; evidence is not truncated to make a cap fit.

These are hard configured capacities and owner choices, not measured pilot need,
worst-case timing guarantees or population throughput. The single fixture's 150
calls do not guarantee any unseen document fits. Oversized requests or more than
16 windows, 64 claims or 128 targets can produce visible incomplete/refused
outcomes. After the required O6 gate and before dispatch, source-window counts
must be checked against frozen ceilings; a mismatch blocks dispatch and requires
a focused freeze/commit disposition, rather than a silent increase. No pilot
text, target-count payloads, drafts or gold were read to size these caps. Native
fixture quality and calibration remain unmeasured.

The owner’s “Not available” memory answer and “None that I know of” build/phase
answer left actual residency, build identity and phase presence evidence open at
that checkpoint. Attempt 3 supplies measured build/phase evidence below.
The owner subsequently approved one measured third fixture attempt below.
The measured third attempt is complete below; actual 36 GiB fit and checkpoint
approval remain open. B1 remains incomplete and ADR 0006 remains Draft.

## Completed measured third fixture attempt, 2026-10-14

D21-13's owner-authorized `s11-fixture-3` completed after application review
returned no findings and 10 covering invented-input tests passed. Both helper and
measurement outcomes are complete (`helper_status = complete`,
`measurement_status = measured`), with 149 sequential returned calls and no failed
call rows. This supersedes the third attempt's prior unrun status. Code HEAD was
`ffc585a63de6a5b6a07ce3f35dd1fa594ba6fe7a`; approved wrapper SHA-256 was
`3a11e610f276d33e5881b209b4c5780575e9e1c076cd8edbef502daf779fd3f6`.
Fixture and identities hashes remain respectively
`0bbccaa6c801a4eb354468c2f7320a33710f122f4d2b70219ce3c13fff185bdf` and
`c8b78f428fae90dc045319326015b92ba7e14bc7bc34660ad06db5838c59d2e3`.
All six model/runtime pins, helper and provisional smoke limits remain unchanged;
selected final pilot ceilings were not substituted into the fixture attempt.

| Role | Calls | Call elapsed range, ms | Total call elapsed, ms | Reported input tokens | Reported output tokens |
| --- | --- | --- | --- | --- | --- |
| extractor | 2 | 25,520–50,114 | 75,634 | 2,527 | 941 |
| classifier | 23 | 69,759–119,027 | 2,077,024 | 160,205 | 541 |
| judge_a | 40 | 6,947–21,612 | 551,114 | 63,366 | 4,827 |
| judge_b | 40 | 6,064–17,193 | 462,687 | 65,232 | 4,881 |
| minicheck | 22 | 114–9,684 | 126,965 | 1,317 | Unknown (`null`) |
| deberta | 22 | 128–2,704 | 16,081 | 1,292 | Unknown (`null`) |

Call elapsed totals 3,309,505 ms; owner wall time was 4,138.5 seconds
(1 hour 8 minutes 58.5 seconds). The gap is not attributed. The 105 generative
calls reported 291,330 input and 11,190 output tokens (302,520 total). All 103
classifier/judge local prompt counts and 44 NLI input counts matched reported
counts. Two extractor local counts remain unknown; 44 non-generative NLI output
counts remain `null`. Counts are not target counts or semantic/calibration results.

### Proven runtime and phase evidence

All four runtime checkpoints (constructor, checkpoint, support start, final)
observed two NLI model references, two NLI tokenizer references and three chat
tokenizer references. The same Python PID 99,487 persisted across phases. Original
Gemma PID 98,917 exit was affirmatively verified by `ESRCH`; judges ran together
as distinct PIDs 30,325 and 30,390. Start/end server projections in both phases
confirmed build 11,146 / `7fe450e19`, expected aliases, context 12,288 for Gemma
and 8,192 for each judge, one slot, awake state and private weight-path equality.
There were zero metadata refusals, zero sample errors and zero unavailable pressure
samples. These establish the measured runtime/transition facts, while effective
all-layer Metal offload confirmation was not supplied; the owner's later uncertainty is recorded below.

Hardware memory was 38,654,705,664 bytes (36 GiB). Nominal sampling interval was
one second; Gemma construction markers were start 0.114070 s and loaded
20.760248 s relative to that phase.

| Active phase | Samples | Elapsed s | Largest sample gap s | Maximum sampled process RSS sum | Maximum sampled physical-footprint sum | Maximum raw pressure |
| --- | --- | --- | --- | --- | --- | --- |
| gemma | 2,628 | 2760.495064 | 2.244128 | 16,227,762,176 (15.113281 GiB) | 15,953,618,744 (14.857965 GiB) | 4 |
| judges | 1,162 | 1249.640375 | 1.889604 | 23,542,906,880 (21.926041 GiB) | 23,278,437,280 (21.679734 GiB) | 2 |

Process maxima, in bytes, are recorded separately. Maxima across different
processes need not occur at the same sample; do not add these maxima to infer a
phase sum.

| Phase | Process | Maximum sampled RSS bytes | Maximum sampled physical-footprint bytes |
| --- | --- | --- | --- |
| gemma | gemma | 16,202,858,496 | 14,315,822,240 |
| gemma | python | 763,084,800 | 1,641,646,768 |
| judges | judge_a | 10,969,317,376 | 11,622,710,440 |
| judges | judge_b | 9,474,916,352 | 10,811,012,656 |
| judges | python | 3,494,133,760 | 1,695,077,128 |

| Phase | System swap before, bytes | System swap after, bytes | Maximum sampled system swap, bytes | System swap delta, bytes |
| --- | --- | --- | --- | --- |
| gemma | 7,724,597,248 | 15,658,975,232 | 19,558,301,696 | 7,934,377,984 |
| judges | 10,567,876,608 | 25,849,626,624 | 29,021,831,168 | 15,281,750,016 |

Gemma swap before/after/maximum/delta correspond to 7.194092 / 14.583557 /
18.215088 / 7.389465 GiB; judge-phase figures are 9.842102 / 24.074341 /
27.028687 / 14.232239 GiB. System VM counter deltas are raw counters, with
16,384-byte pages; no model-only attribution is made.

| Phase | Pageins delta | Pageouts delta | Swapins delta | Swapouts delta | Raw pressure before → after |
| --- | --- | --- | --- | --- | --- |
| gemma | 3,963,132 | 18,901 | 6,498,579 | 8,782,565 | 2 → 2 |
| judges | 5,208,174 | 11,798 | 1,131,426 | 2,234,907 | 1 → 2 |

For this sysctl, Apple's [pressure handler](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_memorystatus_notify.c#L1754)
converts the internal enum into dispatch flags. The [public-facing flag definitions](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/event_private.h#L276)
map 1 to normal, 2 to warning and 4 to critical; the internal enum has different
numeric values. Applying this source mapping, the observed maxima indicate
critical pressure during the Gemma phase and warning during the judge phase.
These mutable primary-source pages were consulted on 2026-10-14; they are not a
pin of the running OS source.

### Owner clarification after attempt 3

For commands, effective Metal and offloaded layer counts, the owner answered
exactly “yes, not sure, not captured”: the approved commands were used, effective
Metal remained uncertain, and offloaded layer counts were not captured. For
unrelated memory-heavy work during the attempt, the owner answered “yes”;
categories and counts were not supplied. Whole-system Memory Used was not supplied.

Attempt 3's fit interpretation is confounded by the presence of unrelated heavy
work. The measured pressure/swap evidence does not establish how much paging was
caused by that work or by the model processes, and does not establish an intrinsic
model-capacity failure. It also does not establish resident fit. The 149 completed
calls, measured identities/phases, timings and memory figures remain unchanged.
The owner subsequently authorized one controlled fourth attempt below; it is
unrun and application review passed on 2026-10-15. Configurations and selected budgets remain unchanged;
ADR 0006 remains Draft, B1 incomplete and B2 unstarted.

### Attempt-3 fit interpretation and limitations, as of 2026-10-14

Native fixture calls and active measurements are complete, but **36 GiB resident
fit is not established**. Substantial system swap growth and pressure accompany
the run; small process sums do not prove adequate physical-memory headroom.
This is a qualified inference about fit from the observations, not attribution
of all paging to these models. System counters include unrelated processes.

Process RSS/physical-footprint sums are neither whole-system Memory Used nor unique
physical memory; shared accounting and sequential readings within a sample limit
interpretation. No Metal buffers are added again. Sampled maxima are not absolute
peaks; the server-switch interval was unsampled, and future/worst-case loads are
unmeasured. Activity Monitor whole-system Memory Used was not supplied. Effective
Metal offload confirmation also remains uncertain, and offloaded layer counts were
not captured. Unrelated heavy work was present, confounding fit interpretation
without establishing cause for all paging. Historical attempts 1 and 2
retain their missing memory observations; attempt 2's 150 calls remain a separate
completed attempt. No quality, calibration or production-selection finding follows.

ADR 0006 remains Draft and B1 incomplete; B2 remains unstarted. Selected final
baseline ceilings are unchanged. Actual fit interpretation, missing whole-system/
effective-offload evidence and checkpoint approval remain open. No new attempt,
policy/configuration change or evidence-bundle/model commit is authorized here.
Agents read only safe projected metadata and primary-source code metadata.


## Owner-authorized controlled fourth attempt, measurement launches stopped

On 2026-10-15 the owner answered “Authorize one controlled attempt 4” to proposal
SHA-256 `1362babee7bb7991a5e262d40fe3bdb0c0189a461bd1f99a27b8af6dd7409bfc`.
D21-14 records this named authorization in plan-only commit
`02e708f3465a57915b51f8bd3bf8cb27fdd142ae`. One fresh `s11-fixture-4` is
initially **authorized and unrun**; application review passed on 2026-10-15 before
executable handoff. Its actual preflight stop is recorded below. The proposal's preparation wrapper SHA-256 is
`0de63d48702e6f8dcc7c772e6a72e286443cf08e09cc9159eaf6f14053988d06`;
this historical preparation identity is not a claim of completed application
review or actual measurement. Attempts 1–3 remain preserved.

Application review passed on 2026-10-15 for authorization/spec conformance and
quality/safety. The applied wrapper SHA-256 is
`c6d0729fbd23793cc66bfec9526a9733975bb2042703922243dbdcf6ed2588f9`, bound to the exact
D21-14 commit above. Final published owner packet SHA-256 is
`adf5c373ee4eb57aea344bff1e9f41d36fc7ca5ed5ef4dec34696495d8fa6513`. Controller verification returned
66 invented-input tests passed, clean scoped lint/format and exact
body/pin/command-preservation checks. This is application evidence only;
the later preflight stopped before fixture inference and positive resident fit
remains open.

The approved controlled method stops prior servers and unrelated heavy work,
requires closed owner attestations of prior foreground exit and continued
heavy-work absence, and automatically verifies selected ports empty before
starting system/Python measurement ahead of Gemma. Initial server exit and other
load absence remain attestations, not automatic proof about all processes.

Baseline admission allows at most three scheduled 30-second windows, each with
all 31 samples available, no errors, integer normal pressure 1, nonpositive
swap-used endpoint delta (no endpoint growth), zero new swapouts and nonnegative
raw VM counter deltas. Existing swap stock is permitted. Swap-in flow, actual
elapsed time, probe overhead, sample gaps and errors must be reported. Failure
refuses before model construction or inference; the actual first-window admission
and subsequent first-checkpoint stop are recorded below.

Fresh private startup evidence must be bound to each server's PID and checked
against source-pinned Metal/all-layer expectations before that phase's inference,
with post-read file/identity checks. Original Gemma PID/start exit must be proved
automatically before both judges. Continuous system/Python and active process
measurements span the unchanged full helper pass, retaining both judges during
support, two NLI models, two NLI tokenizers and all three chat tokenizers as
specified. Missingness, shared accounting and sampling/source limitations remain
explicit; this method introduces no automatic fit or approval decision. The prior
roughly 69-minute pass is planning context, not a latency guarantee.

Fixture `0000877860-13-000100_ex-99-1`, model identities, contexts, every
generation/traversal setting, shipped retry rules and complete provisional smoke
limits SHA-256 `481394833468d21de0dff6b6c72d1fcfe0c53e67dee7fb7ee20da7449bf58bbd`
remain unchanged. Selected final pilot limits SHA-256
`8fae7afbb60fe45e04e178c800f0ae87e5609423e0a65ad02840ead770d110cd`
remain separate. No new native observation, positive resident fit or pilot
operation is established by this authorization. Attempt 3 remains confounded by
other load; its actual 149 calls and pressure/swap figures are unchanged.
ADR 0006 remains Draft, B1 incomplete and B2 unstarted.

### Actual fourth-attempt preflight stop, 2026-10-15

The owner supplied `s11-fixture-4` preflight metadata bound to code HEAD
`02e708f3465a57915b51f8bd3bf8cb27fdd142ae`, the unchanged helper hash
`039b75ec54074b9b5330a02c99079e3b23aab7fe95a7a267930e28e5db72d0c5` and provisional
limits hash above. Prior server exit and unrelated heavy-work absence were owner
attested. Baseline admission succeeded on the first window: 31 samples over
30.115706 seconds, zero sample errors, largest gap 1.011080 seconds, raw pressure
maximum 1 (normal), and swap unchanged at 1,614,020,608 bytes (1.503174 GiB).
Probe overhead was 0.115706 seconds. Raw VM deltas were pageins 3,751,
pageouts 0, swapins 4 and swapouts 0. Baseline Python maximum RSS was 113,344,512
bytes and maximum physical footprint 84,755,200 bytes.

Continuous system/Python observation collected 51 samples over 49.881838 seconds,
zero errors, largest gap 1.015939 seconds and raw pressure maximum 1, with no swap
endpoint growth. Raw VM deltas were pageins 5,911, pageouts 0, swapins 4 and
swapouts 0. Python maximum RSS was 113,393,664 bytes and maximum physical footprint
84,771,584 bytes. Shell-reported wall time was 93.1 seconds; its difference from
measurement durations is not attributed. Metadata refusals were zero.

The wrapper then stopped with `owner_not_ready` at the **first ready checkpoint**:
`helper_status = not_started`, `measurement_status = partial`, and empty active
phases, startup evidence and runtime observations. The checkpoint precedes the
helper/builder call, so neither fixture helper execution nor Python model-runtime
construction began; no fixture inference or operating-model residency evidence
was produced. The owner subsequently confirmed entering `start_gemma` at the
first checkpoint's exact `ready` read, and confirmed that external Gemma had not
been started and its startup log had not been created. The earlier two
acknowledgements passed, as recorded by the actual metadata; no claim is made
that extra narrative wording was accepted by those guards. This establishes the
owner-reported readiness mismatch, not a model/capacity failure.

The authorization and prior unrun designation are historical; preflight actually
ran and stopped before fixture inference. Existing artifacts are retained. These
observations supply no new model, setting, budget or inference-pass authorization.
All prior attempt figures, identities and selected ceilings remain unchanged.
ADR 0006 remains Draft, B1 incomplete and B2 unstarted; positive resident fit
remains unestablished.

Source/setup recovery review passed on 2026-10-15 for authorization/scope and
preservation/freshness. Recovery of this pre-inference setup remains within
D21-14's one still-unstarted fixture-4 pass: preserve the first preflight directory
under a new private archive identity `s11-fixture-4-preflight-1`, create a fresh
startup directory and repeat the unchanged baseline/acknowledgement sequence.
The first preflight result remains recorded above. The applied wrapper hash,
exact HEAD, model/settings/limits, run ID and ordinary output-refusal guards stay
unchanged. A failed archive/preservation step must stop, without deletion or
forcing through an existing archive. This is not permission to reuse a dispatched
fixture pass. Recovery instructions are ready for owner-terminal handoff; actual
recovery/native completion and positive fit are not established. No agent
inspected startup directories/logs or run artifacts.


### Second measurement launch: startup-evidence refusal, 2026-10-15

The owner followed the procedure correctly on the second measurement launch:
the two acknowledgements passed, the wrapper emitted `start_gemma`, the owner
launched Gemma externally in terminal A, then entered `ready` in terminal B.
The server loaded. This launch is distinct from the preserved first preflight
readiness stop above.

Baseline admission again succeeded in one window: 31 samples over
30.10802258271724 seconds, probe overhead 0.10802266700193286 seconds, largest
sample gap 1.0120455827564 seconds, zero errors and raw pressure maximum 1.
Swap remained 1,614,020,608 bytes, with zero endpoint growth. Raw VM deltas were
pageins 3,766, pageouts 0, swapins 0 and swapouts 0.

Continuous system/Python measurement collected 82 samples over
80.87452450022101 seconds, largest gap 1.0147821670398116 seconds, zero errors,
raw pressure maximum 1 and the same unchanged swap stock. Raw VM deltas were
pageins 1,094,358, pageouts 140, swapins 0 and swapouts 0. Python-only maximum
RSS was 113,344,512 bytes and maximum physical footprint 90,243,816 bytes; these
are neither Gemma nor whole-system memory figures. Shell wall time was 114.6
seconds, without attribution of the duration difference. Metadata refusals were
zero; hardware remained 36 GiB. HEAD, model/runtime configuration pins, helper
and provisional limits remained unchanged.

The helper outcome was `refused`, helper reason `smoke_failed`; measurement was
`partial`, with separate reason `startup_evidence_unavailable`. Gemma startup
projection refused; active phases and runtime observations were empty. The helper
and injected measured-builder callback were entered, but startup-evidence refusal
preceded underlying Python `build_runtime`, normal fixture output-directory/cache
creation and all extraction/classification/support calls. No actual run artifacts
were inspected. External server loading is separate from Python runtime
construction; this launch produced no fixture model calls or operating-model
residency evidence.

Source diagnosis identifies a capture/parser defect: the immutable applied wrapper
expects ready emitter `srv main`, while the pinned producer and owner-reported
emitter use `srv llama_server`. Default verbosity 3 also omits required library
INFO evidence gated at level 4; the pinned producer format and callback chain
have now been checked. The owner selected the reviewed ready-matcher correction
and explicit verbosity 4 in D21-15 below; its application review has passed. The
owner procedure was correct. Generic `smoke_failed` here is not an
inference or capacity failure, and no positive resident fit is established.

Wrapper SHA-256 remains
`c6d0729fbd23793cc66bfec9526a9733975bb2042703922243dbdcf6ed2588f9`, bound to HEAD
`02e708f3465a57915b51f8bd3bf8cb27fdd142ae`; those executed bytes remain preserved.
Capture-correction preparation review passed; the owner selected the focused O2
method in D21-15 below. Its application review subsequently passed. This
record does not instruct another execution of that wrapper or infer new native
authorization. Both measurement launches and attempts 1–3 remain preserved;
models, settings, budgets and run-ID selections are unchanged. ADR 0006 remains
Draft, B1 incomplete and B2 unstarted.

## Owner-selected corrected capture method, 2026-10-15

The owner answered “Select corrected capture method” to reviewed packet SHA-256
`84053fb0c32b7514f0a1baafa9688e45610f540a84f6e833019da7b76c3f877e`, with preparation
wrapper SHA-256
`93d618bca18aa4d6080cabf7e43ad840e4ba5a1576c95398d70950390407cf88`.
D21-15 records the actual O2 selection in plan-only commit
`74ddb33f00c5d0ec75c7265dff96c966eee62fd1`. The main-checkout approval branch was
fast-forwarded to that plan commit; the actual main-branch baseline
`25c9f6a7d1c0dc53ea98fc65c6d2ecf7881c6d0e` is unchanged.

The selected capture correction uses the exact `llama_server` ready emitter and
explicit `--log-verbosity 4` on all three server commands. Models, contexts,
generation/traversal settings, complete limits, shipped retries and parser bounds
are unchanged. This selects the corrected method for the same unused single
fixture-4 pass; it does not select a new run ID or an additional fixture pass.
The original c6 wrapper, both measurement-launch records and original logs must
remain preserved; the second archive procedure is owner-only and its instructions
are reviewed separately. No agent has inspected or archived those actual artifacts,
and this record does not claim that the second archive has occurred.

Preparation implementation and protocol reviews passed; a Minor source-URL locator
was corrected. D21-15's exact HEAD/status/hash bindings are applied. Independent
application review passed for spec/authorization and quality/safety with no findings.
The controller reran the unchanged invented-input suite: 88 passed in 0.11 seconds;
scoped Ruff lint and formatting passed. These checks establish the reviewed
application, while actual native capture and fit remain unverified.

Applied wrapper SHA-256 is
`faf22a7e150531b4e2ea17c307939508d4c41fdae216dcc05a40cc10abba1686`, requiring exactly
HEAD `74ddb33f00c5d0ec75c7265dff96c966eee62fd1`. Approved operator-packet SHA-256 is
`7266b036401374aa61cf18ae1443671cbd8698df5eeb29193b3dd62a0752ec56`; its archive and
all three server command blocks match selected preparation exactly, with only the
loader hash changing. Application-review SHA-256 is
`15e47d13c30c3b51c89854dd898ccc89fe018478d7f7bb68f39a21380496d9bd`.
Safe applied-source snapshots and their SHA manifest are preserved separately from
selected preparation and earlier executed sources. The exact reviewed owner
handoff is ready for the one authorized unused fixture-4 pass. No native execution
or second archive operation is claimed by this application record.

No new native observation, fixture completion or positive resident fit follows
from this selection. All earlier attempt figures and identities, both attempt-4
launch outcomes and selected final pilot ceilings remain unchanged. ADR 0006
remains Draft, B1 incomplete and B2 unstarted.

## Attempt-4 corrections and the fifth fixture pass, 2026-10-15 to 2026-10-17

Three further owner-approved, reviewed corrections to the measurement wrapper
followed D21-15. None changed a model, setting, limit or ceiling:

- **D21-16** (plan commit `e194e265a9274b1ebde10a71d842e5978e8c2147`): build 11146
  emits no `ggml_metal_device_init: GPU name:` line at verbosity 4, so Metal
  evidence now comes from one exact `ggml_metal_init: allocating` line and one
  `picking default device` line whose name equals the selected device's
  description. Single-device hosts only. Native startup archives moved to a
  private, git-ignored, reboot-durable location. A 2026-10-16 reboot had already
  destroyed the earlier `preflight-1` to `-3` archives, which were held in
  reboot-volatile scratch space; no copy exists, so the preservation statements
  in the attempt-4 sections above no longer hold for them.
- **D21-17** (plan commit `f241501a21c4aad7f9d0d78393b2a8f0b890a389`): CPython
  3.14.0 on macOS has no `st_birthtime_ns`; file birth time is now
  `round(st_birthtime * 1e9)` integer nanoseconds. The D21-17 pass measured the
  Gemma phase (raw pressure maximum 2) and proved Gemma's exit, then refused at
  judge B's startup check. Its whole-run continuous record reached raw pressure 4
  (critical) outside the Gemma phase's active window. Its output directory exists,
  so `s11-fixture-4` is spent.
- **D21-18** (plan commit `59a7027b1698124fb99ae518b182fbe3f23df2af`): judge B's
  log held a lone `0xC4` byte on a non-evidence line. Startup logs now decode with
  replacement, any evidence line containing U+FFFD refuses, and the content hash
  still covers the raw bytes. The run moved to the new ID `s11-fixture-5`.

The applied D21-18 wrapper,
`0bff17f1cea0f48f803a8c62ca9d322e09d3ca84f1be39ce76b4b2da03ba235f`, passed 125
invented-input tests and an independent application review. The first
`s11-fixture-5` launch refused `phase_presence_mismatch` at Gemma's `ready`, before
any startup check, runtime construction or run output. The closed output records
only that reason; by the controller's check after the refusal, a judge server was
listening on 8081 and nothing on 8080, so the owner's prior-server attestation did
not match the automatic check, as the loader's attestation limitation allows.
Its startup logs were archived and the loader relaunched.

## Completed measured fifth fixture pass, 2026-10-17

The relaunched `s11-fixture-5` **completed**: `helper_status = complete`,
`measurement_status = measured`, 149 sequential returned calls and no failed call
rows. Code HEAD was `59a7027b1698124fb99ae518b182fbe3f23df2af`. Helper, provisional
limits, six configuration pins, fixture
`0bbccaa6c801a4eb354468c2f7320a33710f122f4d2b70219ce3c13fff185bdf` and identities
`c8b78f428fae90dc045319326015b92ba7e14bc7bc34660ad06db5838c59d2e3` are unchanged
from attempt 3. Selected final pilot ceilings were not substituted.

| Role | Calls | Call elapsed range, ms | Total call elapsed, ms | Reported input tokens | Reported output tokens |
| --- | --- | --- | --- | --- | --- |
| extractor | 2 | 22,723–46,345 | 69,068 | 2,527 | 941 |
| classifier | 23 | 49,454–58,806 | 1,206,408 | 160,325 | 562 |
| judge_a | 40 | 6,429–12,055 | 343,400 | 63,372 | 4,840 |
| judge_b | 40 | 5,351–10,426 | 292,271 | 65,316 | 4,852 |
| minicheck | 22 | 81–4,039 | 19,260 | 1,317 | Unknown (`null`) |
| deberta | 22 | 28–1,103 | 1,857 | 1,292 | Unknown (`null`) |

Call elapsed totals 1,932,264 ms. The 105 generative calls reported 291,540 input
and 11,195 output tokens (302,735 total). All 103 classifier/judge local prompt
counts and all 44 NLI input counts matched reported counts; the two extractor local
counts remain unknown. The owner was not watching the run and confirmed the judges'
`ready` late, so the continuous measurement's 9,455 s (about 6,865 s of it between
`switch_to_judges` and the judges' `ready`, mostly waiting, with the Gemma stop and
judge load not timed separately) is not a timing figure. Counts are not target counts or
semantic/calibration results.

### Startup, runtime and phase evidence

Baseline admission passed in its first window: 31 samples over 30.133262 s,
probe overhead 0.133321 s, largest gap 1.018383 s, zero errors, raw pressure 1,
swap unchanged at 800,260,096 bytes (0.745300 GiB). VM deltas were pageins 1,628,
pageouts 0, swapins 8 and swapouts 0. Owner attestations covered prior server exit
and absence of other heavy work.

Continuous system/Python measurement spanned the whole run, including the server
switch: 9,258 samples over 9,454.961311 s, largest gap 1.170562 s, zero errors,
raw pressure maximum 2 and maximum sampled swap 14,192,869,376 bytes
(13.218140 GiB). VM deltas were pageins 4,276,396, pageouts 2,428, swapins 330,164
and swapouts 1,196,940. Server processes were sampled only inside the active
phases.

Each server's startup projection verified from a fresh, PID-bound, private log:
Metal device 0, build 11146 / `7fe450e19`, all layers offloaded (Gemma 61/61,
judge A 49/49, judge B 41/41). This establishes all-layer Metal offload for this
host and build in `s11-fixture-5`; attempt 3's own offload stays unconfirmed. The
scorers run on CPU and have no startup projection. Start and end server projections in both phases confirmed
the expected aliases, context 12,288 for Gemma and 8,192 for each judge, one slot,
awake state and weight-path equality. Original Gemma's exit was proved by `ESRCH`
before the judges; the judges ran as distinct processes alongside the same Python
process. All four runtime checkpoints observed two NLI models, two NLI tokenizers
and three chat tokenizers. Metadata refusals, sample errors and unavailable
pressure samples were all zero.

| Active phase | Samples | Elapsed s | Largest sample gap s | Maximum sampled process RSS sum | Maximum sampled physical-footprint sum | Raw pressure before → after (max) |
| --- | --- | --- | --- | --- | --- | --- |
| gemma | 1,741 | 1813.437923 | 1.407585 | 28,978,167,808 (26.988022 GiB) | 16,064,636,992 (14.961359 GiB) | 1 → 1 (2) |
| judges | 676 | 699.016487 | 1.232540 | 28,561,981,440 (26.600418 GiB) | 23,585,834,344 (21.966020 GiB) | 1 → 2 (2) |

| Phase | Process | Maximum sampled RSS, bytes (GiB) | Maximum sampled physical footprint, bytes (GiB) |
| --- | --- | --- | --- |
| gemma | gemma | 28,325,199,872 (26.379898) | 14,427,856,224 (13.436988) |
| gemma | python | 847,478,784 (0.789276) | 1,643,006,688 (1.530169) |
| judges | judge_a | 13,882,408,960 (12.929001) | 11,599,576,280 (10.802947) |
| judges | judge_b | 11,142,397,952 (10.377167) | 11,067,668,232 (10.307569) |
| judges | python | 3,805,544,448 (3.544189) | 1,685,541,664 (1.569783) |

Process maxima need not coincide, so they are not added to form a phase sum.

| Phase | Swap before, bytes (GiB) | Swap after | Maximum sampled swap | Delta | Swap total before → after (GiB) |
| --- | --- | --- | --- | --- | --- |
| gemma | 800,260,096 (0.745300) | 2,299,068,416 (2.141174) | 3,696,951,296 (3.443054) | 1,498,808,320 (1.395874) | 2 → 3 |
| judges | 2,114,519,040 (1.969299) | 14,002,225,152 (13.040588) | 14,184,480,768 (13.210327) | 11,887,706,112 (11.071289) | 3 → 14 |

| Phase | Pageins delta | Pageouts delta | Swapins delta | Swapouts delta |
| --- | --- | --- | --- | --- |
| gemma | 1,298,837 | 708 | 42,106 | 195,904 |
| judges | 801,667 | 1,083 | 276,590 | 1,001,036 |

Raw pressure 1 is normal and 2 is warning, per the source mapping cited for
attempt 3. Both phases reached warning; critical pressure (4) was not observed
anywhere in this pass, including the continuous record. Earlier passes did reach
it: attempt 3's Gemma phase (with unrelated heavy work present) and the D21-17
pass's continuous record outside its Gemma phase.

## Owner fit decision, 2026-10-17 (D21-19)

The owner answered: “I accept s11-fixture-5 as the measured 36 GB fit for both
phases, recording the judges-phase swap growth to 13.2 GiB and pressure 2 as an
explicit limitation.” The phases are those FP22 and Task 1 require: Gemma with the
Python runtime holding both scorers and all tokenizers, then both judges with
MiniCheck, DeBERTa, both NLI tokenizers and all three chat tokenizers resident
together. The judges-phase swap growth, from 1.97 to a maximum of 13.21 GiB (the
swap total expanding from 3 to 14 GiB, with about one million swap-outs), and raw
pressure 2 (warning) are recorded as an **explicit limitation** of that fit. The
Gemma phase also reached warning pressure, with swap from 0.75 to a maximum of
3.44 GiB.

The limitation's scope:

- **Attribution.** System swap and paging counters include every process. Other
  heavy work was attested absent, but the measurements do not say how much of the
  swap belongs to the model processes and how much to the rest of the system.
- **Accounting.** RSS and physical-footprint sums are neither whole-system memory
  used nor unique physical memory; Metal buffers are not added separately.
  Sampled maxima are not absolute peaks. Server processes were not sampled
  between the active phases; the system and Python were.
- **Earlier passes.** Critical pressure was not seen in this pass, but attempt 3's
  Gemma phase (with other heavy work present) and the D21-17 pass's continuous
  record did reach it, with the same models and fixture.
- **Workload.** One fixture document was run. Larger pilot documents, more claims
  or more support targets were not measured and may need more memory; the
  selected ceilings bound them, but no unseen document is guaranteed to fit.
- **Consequence.** Pilot runs may page during either phase, which can slow them.

## B1 evidence and consequences

- **Native fixture smoke:** attempt 1 incomplete; attempts 2 and 3 complete
  (150 and 149 calls); attempt 4 (`s11-fixture-4`) spent after a judge-startup
  refusal; attempt 5 complete with 149 calls and sampled startup, runtime, phase
  and memory evidence. Fixture ID is `0000877860-13-000100_ex-99-1`.
- **Residency:** the owner accepted `s11-fixture-5` as the 36 GB fit for both
  phases, with the swap growth and warning pressure as an explicit limitation
  (D21-19).
- **O2:** provisional smoke limits (SHA-256
  `481394833468d21de0dff6b6c72d1fcfe0c53e67dee7fb7ee20da7449bf58bbd`) were
  approved for the fixture attempts only. Final baseline ceilings (SHA-256
  `8fae7afbb60fe45e04e178c800f0ae87e5609423e0a65ad02840ead770d110cd`) are
  owner-selected above and are frozen through B2's preregistration, not by this
  ADR. The foreground Gemma-then-judges procedure, all generation and traversal
  settings and the shipped retry rules are retained.
- **Not claimed:** no pilot result, quality or calibration finding, worst-case
  timing, population throughput, MPS scorer support or production model
  selection. B2 starts only after this ADR and the B1 evidence are committed.

The [B1 verification record](../verification/pilot-v1-feasibility.md) separates
engineering results from native evidence. No local machine paths, source/claim/
quote text, responses or kept drafts are part of this ADR.
