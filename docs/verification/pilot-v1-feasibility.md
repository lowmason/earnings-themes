# Pilot v1 feasibility verification

Status on 2026-10-18: B1 evidence is complete and committed (`a91a8e3`), and the
preregistration is frozen and committed alone (`53ba190`; see the last section).
For B1, the fifth fixture pass, `s11-fixture-5`, completed all roles with verified
Metal all-layer startup evidence and measured both phases; the owner accepted it as
the 36 GB fit with an explicit swap/pressure limitation (D21-19, in the section
"Owner fit decision, 2026-10-17"). Earlier sections
are chronological and state status as of their dates; where a later section closes
an open item (Metal offload, build/phase evidence, fit), it governs. Whole-system
Memory Used and the extractor's local token counts remain unavailable. Final
baseline ceilings are owner-selected below. No pilot operation is authorized or
recorded. Stage 11 remains open. This record contains metadata and safe
numeric/status evidence only.

## Code and engineering evidence

Merged Plan A baseline: `25c9f6a7d1c0dc53ea98fc65c6d2ecf7881c6d0e`.
Plan 21 owner approval was committed alone at
`95f0d206c53e355cbb4bb419d32d828ab53484f8`. The fixture-only smoke helper,
invented-input tests and dictionary appendix were committed at
`fa3240455e2183868a6f31183e213cd189c33a63` after task/spec and code-quality review.

The prescribed missing-helper RED produced one collection error. The exact
Appendix A body then produced 10 passes and one diagnostic-privacy failure.
The owner separately approved Python stream redirection alongside native
descriptor redirection, and an integrated pre-builder judge-panel regression.
The unchanged privacy regression passed; a controlled ordering mutation caused
two expected failures, then correct ordering was restored. Final changed-code
checks reported 13 smoke tests passed and 383 dictionary tests passed with one
skip; scoped Ruff lint, format and whitespace checks were clean. Re-review
returned spec PASS and code-quality PASS. These are invented-input engineering
results, not native model or pilot-quality evidence.

## B1 owner evidence

On 2026-10-13 the owner selected Qwen2.5-14B-Instruct and
Mistral-Nemo-Instruct-2407, both Q4_K_M, as the two pilot judge families. Gemma's
ADR 0004 weight checkpoint and extractor/classifier roles remain fixed. ADR 0005
remains authoritative for MiniCheck and the DeBERTa alternative. No production
model is selected here.

| Role | Owner-selected value |
| --- | --- |
| Judge A | Qwen; alias `pilot-v1-qwen2.5-14b-q4_k_m`; loopback port 8081 |
| Judge B | Mistral; alias `pilot-v1-mistral-nemo-12b-q4_k_m`; loopback port 8082 |
| Runtime | llama.cpp `0.5.0 (build 11146, commit 7fe450e19)` |
| Compiler/platform reported | AppleClang `21.0.0.21000334`; Darwin arm64 |
| Requested judge device/precision | Metal GPU offload; Q4_K_M |
| Requested context/slots | 8,192 tokens; one slot per judge |
| Requested input/output limits | 6,144 / 2,048 tokens per judge |
| Timeout/structured output | 300 seconds; JSON-schema structured output enabled |

The version/build identification is owner-terminal evidence. Requested device,
limits and structured-output settings had not then been established by native
smoke; the `s11-fixture-5` section below records them. Disk/file metadata does not establish resident-memory fit.

The owner confirmed review of applicable weight/base-model terms permitting this
local research use for both judges and the pinned DeBERTa alternative on
2026-10-13. The judge cards identify Apache 2.0; source rights and terms will be
cited in ADR 0006 alongside the completed runtime inventory and native evidence.
Primary metadata consulted on 2026-10-13: [Qwen's pinned card](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct/blob/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8/README.md),
[Mistral's pinned card](https://huggingface.co/mistralai/Mistral-Nemo-Instruct-2407/blob/04d8a90549d23fc6bd7f642064003592df51e9b3/README.md),
[pinned DeBERTa card](https://huggingface.co/MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli/blob/6f5cf0a2b59cabb106aca4c287eed12e357e90eb/README.md)
and [Microsoft base-model card](https://huggingface.co/microsoft/deberta-v3-base/blob/main/README.md).
The base-model card link is a dated read of a mutable page, not an immutable
checkpoint pin or a replacement for the owner's terms confirmation.

| Model | GGUF revision | Original/tokenizer revision |
| --- | --- | --- |
| Qwen2.5-14B-Instruct | `05244aa5d871c661c80082a15d3bce44714d068d` | `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8` |
| Mistral-Nemo-Instruct-2407 | `a2dd64a0a76ea1bdb2bb6ab6fa5496b003c7c908` | `04d8a90549d23fc6bd7f642064003592df51e9b3` |

The owner returned four inventory rows containing 13 files: two GGUF files and
11 tokenizer files. Both supplied weight hashes match the pinned upstream
values. Agents reviewed the returned metadata and did not open local model files.
The published weight hashes are available on the [pinned Qwen weight page](https://huggingface.co/bartowski/Qwen2.5-14B-Instruct-GGUF/blob/05244aa5d871c661c80082a15d3bce44714d068d/Qwen2.5-14B-Instruct-Q4_K_M.gguf)
and [pinned Mistral weight page](https://huggingface.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF/blob/a2dd64a0a76ea1bdb2bb6ab6fa5496b003c7c908/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf).

| Role | File | Owner-reported SHA-256 |
| --- | --- | --- |
| Judge A weights | `Qwen2.5-14B-Instruct-Q4_K_M.gguf` | `e47ad95dad6ff848b431053b375adb5d39321290ea2c638682577dafca87c008` |
| Judge A tokenizer | `config.json` | `0f2085dbbe2ee251bd6a6a0797d84a6ce34436044d629aa3cba793b43d311a9e` |
| Judge A tokenizer | `tokenizer.json` | `c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539` |
| Judge A tokenizer | `tokenizer_config.json` | `5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583` |
| Judge A tokenizer | `merges.txt` | `599bab54075088774b1733fde865d5bd747cbcc7a547c5bc12610e874e26f5e3` |
| Judge A tokenizer | `vocab.json` | `ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910` |
| Judge B weights | `Mistral-Nemo-Instruct-2407-Q4_K_M.gguf` | `7c1a10d202d8788dbe5628dc962254d10654c853cae6aaeca0618f05490d4a46` |
| Judge B tokenizer | `config.json` | `8a42669219f4caadedb891be88c34712572573d42b3d02d665d527f92d94ddfe` |
| Judge B tokenizer | `tokenizer.json` | `e11c71726323d33da7b8d6f6f269f1988931c0a52b7122bcdd8c05042974e0db` |
| Judge B tokenizer | `tokenizer_config.json` | `67f3aeef765b7d78012a081dba98efd4900cd2bac24eac182296841c7e2aef2a` |
| Judge B tokenizer | `merges.txt` | `4e4d41c64d2ed2e26713ae7af7c958b07df532a6f4498dffa9a2cf7f4c6c0aa6` |
| Judge B tokenizer | `vocab.json` | `8572e8853a6b2f2d830de4afa15d43c49257d367abf3c5fd2f6f7687bcd8f63d` |
| Judge B tokenizer | `special_tokens_map.json` | `6fa06efa2785e450051989a6f8fb4416b10149ded485ddd3f127a40734f5cfd0` |

The owner subsequently supplied the prerequisite inventory on 2026-10-13.
Together the two owner-terminal inventories enumerate 33 actual files: five
Gemma files (one weight and four tokenizer/configuration files), 13 judge files,
eight MiniCheck files and seven DeBERTa files. These are owner-reported hashes;
agents reviewed metadata only and did not read or independently hash model files.
The six prepared TOMLs enumerate these same files without missing or repeated
names. Native initialization must still verify their bytes against the manifests.
All MiniCheck and DeBERTa inventory hashes match ADR 0005's pinned checksum tables;
Gemma's weight hash and GGUF revision match ADR 0004.

Gemma's owner-reported original/tokenizer revision is
`842da3794eaa0b77d5f08bae87a17459d91ff475`, with `GemmaTokenizer` and an included
`chat_template.jinja`. The Gemma chat TOML's `revision` identifies its GGUF
checkpoint; its tokenizer identity is separately bound by the four file hashes.
The owner selected Metal, Q4_0, one slot, context 8,192, input 6,144, output 2,048,
300-second timeout and structured JSON-schema output for Gemma on 2026-10-13.
On 2026-10-14 the owner selected context and total input allowance 12,288 below.
These were approved serving choices, then awaiting native confirmation. Reasoning remains off and
serving remains text only, retaining ADR 0004.

Both scorers retain CPU float32 and complete input limit 512. The owner-reported
installed versions are torch `2.14.1`, transformers `5.18.0`, sentencepiece
`0.2.2`, tokenizers `0.23.2` and safetensors `0.8.0`, matching ADR 0005 and both
scorer TOMLs. MiniCheck retains encoding `minicheck-first-step/1` and mapping
`[3,209]`; DeBERTa retains `deberta-pair/1` and mapping `[0,1,2]`. No runtime,
encoding, mapping or immutable scorer revision changes are selected.

The following 20 prerequisite files complete the 33-file inventory alongside the
13 judge files above.

| Role | File | Owner-reported SHA-256 |
| --- | --- | --- |
| Gemma weights | `gemma-4-31B_q4_0-it.gguf` | `179cfb99212709597eae5929112cfca677e1bbf566178b479ae1da0c4772874b` |
| Gemma tokenizer | `config.json` | `e967dd38bc5cfd38bd09a995a7bf4a754075df2b46aba68f7fbb5a791e6d8dd1` |
| Gemma tokenizer | `tokenizer.json` | `cc8d3a0ce36466ccc1278bf987df5f71db1719b9ca6b4118264f45cb627bfe0f` |
| Gemma tokenizer | `tokenizer_config.json` | `9f4fec4b1dc6ecddf8f4a92e9caea5971c0e67d81309f3f9066a2bee8c362633` |
| Gemma tokenizer | `chat_template.jinja` | `ae53464bf3be25802b3a5b37def7fd89667067d7577049b3b2d74c4d8de4c6d4` |
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

The exact role mapping in `config/models/pilot-v1-runtime.toml` uses Gemma for
extractor and classifier, Qwen for judge A, Mistral for judge B, MiniCheck as the
primary scorer and DeBERTa as the explicit alternative. All six model/runtime
TOMLs are prepared. Their preparation and metadata agreement do not establish
native runtime compatibility. [ADR 0006](../adr/0006-select-the-pilot-baseline-models.md)
records the selected identities and rights evidence, and later the native
evidence and fit decision.

On 2026-10-13 the owner explicitly approved both O2 questions for **smoke only**:
the complete current `config/models/pilot-v1-smoke-limits.json`, SHA-256
`481394833468d21de0dff6b6c72d1fcfe0c53e67dee7fb7ee20da7449bf58bbd`,
including every generation parameter/default, window/claim budget and request/token
ceiling, the shipped two-attempt rules, and only run ID `s11-fixture-1`; and the
proposed operator procedure and evidence method. This authorization does not
select final pilot baseline budgets or establish that native smoke ran.

The approved procedure starts Gemma in the foreground, stops it after extraction/
classification, then starts both judges in the foreground and confirms readiness.
Python remains resident with both scorers and all tokenizers throughout. Servers
use all-layer GPU offload, automatic fitting disabled, reasoning off and the
pinned defaults. The approved evidence method samples Activity Monitor whole-system
memory usage, memory pressure and swap during both phases. These samples must be
reported as observations with their sampling limitations; no residency measurement
or fit result was recorded at this point.

For `s11-fixture-1`, the classifier/judge runtime checked `input_limit = 6144`
against prompt plus reserved completion. With `max_tokens = 2048`, those roles
permitted at most 4,096 prompt tokens; the 8,192 server context did not enlarge
that allowance. Following the owner selection below, Gemma's total allowance is
12,288 and its prompt allowance is 10,240. Judges retain total allowance 6,144,
prompt allowance 4,096 and server context 8,192.

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

### Fit interpretation and remaining limitations

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

## Pause checkpoint — 2026-10-15

After the reviewed D21-15 executable handoff, the owner requested a durable pause
for transfer to Codex app. Asked whether the corrected `s11-fixture-4` commands
had started, the owner answered **“Not started.”** No corrected-run result or
archive-2 execution is claimed. This is the latest owner-reported status, not an
agent process/filesystem inspection. Before a later start, confirm current owner
status so an intervening terminal action is not duplicated. Existing D21-15
approval remains recorded; the pause does not complete B1 or any later gate.

## Remaining checkpoint requirements, as of 2026-10-15

O1 identities, configurations, all-role native calls and the measured third
attempt's builds/phase transition/runtime presence are recorded. O2 numeric
baseline ceilings and rationale are owner-approved. Active process/system
measurements are now recorded; actual 36 GiB resident fit is not established.
Whole-system Memory Used and effective Metal confirmation remain unavailable.
Resolve fit and approve the B1 checkpoint before B2; native completion alone does
not discharge that requirement.

B2 has not started. O3/O4 must be resolved before its alone-commit preregistration,
and B3 onward remains blocked until O6. Root/wording gates, V6 acceptance and the
separate concrete Current state approval are outstanding. No protected source,
claim, quote, draft, independent record or local machine path is included here.

## Resume checkpoint — 2026-10-15

The owner explicitly resumed Plan 21 using subagent-driven-development and the
reviewed Codex app handoff. Asked about corrected attempt 4 and Archive-2 since
the pause, the current text-only owner answer was
**“Neither started since the pause”**. This is an owner report, not
process/filesystem proof; the historical pause above remains preserved.

The existing reviewed D21-15 handoff remains authoritative, with no new approval
pending for that named handoff. Independent safe-source/Git verification and the
controller's scoped recheck returned PASS for the named safe sources/pins and
unchanged Git guards/state. These are source-only results; the earlier 88-test
evidence remains historical. Archive-2 preservation, the corrected unused single
s11-fixture-4 pass, actual native simultaneous 36 GiB fit and B1 completion remain
pending. ADR 0006 remains Draft and B2 unstarted; all later owner gates are
unchanged. Hold B1 evidence for Task 1 step 5. This resume checkpoint records no
native result, task completion or new review round.

## Corrected attempt-4 launches and D21-16, 2026-10-16/17

Owner- and controller-reported events on 2026-10-16, not independently verified
by review: the D21-15 preservation step created `preflight-2`, and the loader then
refused `measurement_unavailable` before any prompt, because the shell lacked an
absolute `EARNINGS_MODELS_ROOT`. Relaunched with that value inline, it refused
`startup_evidence_unavailable` before any prompt, because an owner-started Gemma
had already written a startup log, which was preserved as `preflight-3`. A
reboot at 13:06 that day then erased the reboot-volatile scratch area. That
destroyed the `preflight-1` to `-3` archives, the scratch wrapper and the uv
cache; no copy of the archives is known. The wrapper was restored byte-identically
(`faf22a7e…`) from its durable git-ignored snapshot, and a fresh private startup
directory was recreated.

The 2026-10-17 closed loader output records four rows. The owner typed both
attestations, and baseline admission passed in its first window: 31 samples,
zero errors, pressure 1, swap used 0 to 0, zero swap-outs. Gemma reported ready.
The wrapper's startup projection then refused `startup_evidence_unavailable`
(`helper_status: refused`, `helper_reason: smoke_failed`, `phases` empty,
`measurement_status: partial`, `code_head` `74ddb33`). That was before runtime
construction, output creation or fixture inference. The controller reports
that no `s11-fixture-4` output directory exists.

A counts-only replay found every startup check passing except the required
`ggml_metal_device_init: GPU name:` line, which pinned build 11146 did not emit
under `--log-verbosity 4`. The context-level `ggml_metal_init` allocating and
picking-device lines were present, and the picked name equalled the selected
device description (checked as a boolean only).

D21-16 (plan-only commit `e194e265a9274b1ebde10a71d842e5978e8c2147`) accepts
proposal `1eb2d99f121a7ac4493f9bc2643e588b2481d9af1c88d3c56e0d7f7cdb1bfbc3`,
with preparation wrapper
`172e3dd1bae4ba87f52055ed0ef319636559acb855e6a6eb537d5f2b3cf6ef7f`. The corrected
Metal evidence requires one exact allocating line, and one picking-device line
whose name privately equals the selected description. The GPU-name line becomes
optional, index-matching when present, with `MTL0` required when it is absent.
The owner accepted the index-to-name link, single-device-only acceptance, and the
risk that no judge startup log has been observed under this build and verbosity.
Native archives now go under the owner-only, git-ignored
`.handoff/plan21-native-archives/`.

Proposal review found no Critical issues. The real-prefix replay and the minor
test, trigger and comment fixes were applied. Ordering checks were deliberately
not added, because the earlier code had none and adding them risked a new false
refusal. On the real refused Gemma prefix, the exact candidate projection returned
`verified` with device 0 and 61/61 layers.

The applied wrapper
`698d61801bf9693399b9fdbc872f7166d5ab2fc16ffcbf108e326fc5fea79314` passes 107
invented-input tests (`f6ff7e9094be3dc25dfc1e7b2bb64e69d46e25b43aebdcb4ac9a945b3c040f8c`).
Application review found no Critical issues. Its packet findings were addressed,
and a scoped re-review cleared the packet for owner handoff with no Critical or
Important findings. Its step-4 wording suggestion was applied. The final operator
packet is
`b8464518c1844adc41d212a6c1dca2fa1db59cbafc96b6e1d510a0b93a266b8d`. No corrected
run has started. ADR 0006 remains Draft, B1 is incomplete and B2 has not
started.

Later on 2026-10-17 the owner ran the superseded D21-15 loader by mistake, from
the controller's earlier instructions. That wrapper pins HEAD `74ddb33`, so at
HEAD `e194e26` it refused `measurement_unavailable` before any prompt, server or
inference. Its `tee`, which lacked `-a` in those instructions, overwrote the
agent-readable closed output of the baseline-admitted run.

The controller reconstructed that output from the owner's earlier paste, as a
separate file. It has 4 rows and 10,237 bytes, equal to the original's recorded
size, and re-serialized in the wrapper's canonical JSON form it is identical
(SHA-256 `61ddbe22b33b60e13dbc6054524b35a6627cc08047451e95dec9294b2cd41772`).
It is a reconstruction, not the original bytes. The stale scratch loader was
removed. No native state changed: the installed scratch wrapper is still the
D21-15 copy, and the D21-16 packet's step 1 replaces it.

## D21-16 launch and D21-17 birth-time correction, 2026-10-17

The owner ran the D21-16 packet. By the controller's report, step 1 archived the
prior startup directory (`preflight-4`) and installed `698d6180…`, which review
confirmed by the scratch-wrapper hash. The closed output records baseline
admission, then a refusal of `startup_evidence_unavailable` at Gemma's startup
projection, with `helper_reason: smoke_failed`, `phases` empty and `code_head`
`e194e265…`. That was before runtime construction or inference.

Gemma (PID 23526) was left running and the D21-16 step 4 was not run, so that
run's startup log remains in the scratch startup directory; the D21-17 packet's
step 1 preserves it as `preflight-5`.

Root cause: the run interpreter, CPython 3.14.0 on macOS, has no
`os.stat_result.st_birthtime_ns`. The projection's metadata read therefore
raised, the error was caught, and every startup projection refused. The D21-15
refusal shared this cause. D21-16's replay had bypassed the descriptor path, and
the invented tests had faked the missing field.

D21-17 (plan-only commit `f241501a21c4aad7f9d0d78393b2a8f0b890a389`) accepts
proposal `8d3d1ede399ed4aa914829bab7fccb599217b2cf4e85bed9161070360678154c`
(preparation wrapper `f02d0b57…`). Birth time is now
`round(st_birthtime * 1e9)` integer nanoseconds, accurate to about ±250 ns and
failing closed at that scale.

Controller-reported, not independently verified by review: the exact,
AST-extracted `startup_projection` was run on the real refused Gemma
log with closed fields only. The process witness and presence check were
stubbed, and the checkpoint was the startup directory's birth, a permissive
bound. The candidate returned `verified` (device 0, 61/61 layers); the D21-16
wrapper returned `refused`.

The applied wrapper
`953097b71f348f01ab914de377465047906c84414b0b8977ccc753b3b6683510` passes 111
invented-input tests, including real-`fstat` tests that fail against D21-16.
Preparation review found no Critical or Important issues, and its Minor notes
were addressed. The owner accepted that the ESRCH exit probe, the runtime
attribute chain and the judge-phase values remain unproven by real execution.
No corrected run has started. ADR 0006 remains Draft, B1 is incomplete and B2
has not started.

## D21-17 launch: judge B decoding refusal, 2026-10-17

The owner ran the D21-17 packet at HEAD `f241501a…` with wrapper `953097b7…`.
The owner pasted the closed output, which records:

- baseline admitted;
- the Gemma phase measured, about 1,804 s;
- Gemma resident memory up to about 26.6 GiB, swap from 0 to a maximum of
  3.7 GiB, and memory pressure up to 4;
- Gemma's exit at the judge switch proved by ESRCH.

That retires D21-17's open risks 1 (the exit probe) and 2 (the runtime attribute
chain) for Gemma. At the judges' startup projection, judge A (Qwen) verified
49/49 layers, and judge B (Mistral) refused `startup_evidence_unavailable`. The
`s11-fixture-4` output directory now exists, so that run ID is spent.

Root cause, from a counts-and-positions-only replay: line 48 of judge B's log
holds a lone `0xC4` byte, a UTF-8 lead byte without a continuation byte, on a
line that carries no evidence. Strict per-line decoding refused the whole role.

Proposal D21-18 (`.handoff/plan21-attempt4-utf8-correction/`, approved below) decodes
with replacement, refuses any evidence line that contains U+FFFD, and moves the
run to `s11-fixture-5`. Controller-reported: the exact `startup_projection`, run
on all three real logs with closed fields, verified Gemma 61/61, judge A 49/49
and judge B 41/41. The judge servers and the `s11-fixture-4` startup logs had not
yet been stopped and preserved when this was recorded. No D21-18 run has
started.

## D21-18 application and the `s11-fixture-5` pass, 2026-10-17

D21-18 (plan-only commit `59a7027b1698124fb99ae518b182fbe3f23df2af`) accepts
proposal `ac98aa91…` (preparation wrapper `783e28eb…`). The applied wrapper
`0bff17f1cea0f48f803a8c62ca9d322e09d3ca84f1be39ce76b4b2da03ba235f` passed 125
invented-input tests. Under the exact `startup_projection`, it verified all three
real `s11-fixture-4` logs: Gemma 61/61, judge A 49/49 and judge B 41/41.
Application review found no Critical issues; its one Important finding (the
inherited D21-15 fallback with the old run ID) was fixed in the packet
`b1-smoke-5-utf8-approved.md`.

The owner ran step 0, which preserved the D21-17 startup logs as
`s11-fixture-4-d21-17-run`, and step 1.

The first loader launch refused `phase_presence_mismatch` at Gemma's `ready`.
That was before the startup projection, runtime construction or any run output.
The closed output records only that reason. By the controller's process check
after the refusal, a Qwen judge server was listening on 8081 and nothing on 8080,
so the owner's prior-server attestation did not match the automatic check. The
owner archived that startup directory as `s11-fixture-5-preflight-1` and
relaunched from step 2.

The relaunch **completed** (`helper_status: complete`,
`measurement_status: measured`, `code_head 59a7027b…`), and the owner preserved
its startup logs as `s11-fixture-5-run`. Figures from the closed output
(`.handoff/plan21-fixture5-run/s11-fixture-5-loader-output.jsonl`):

- **Startup:** all three roles verified on Metal device 0 (build 11146,
  `7fe450e19`): Gemma 61/61, judge A 49/49, judge B 41/41. Gemma's exit was
  proved by ESRCH.
- **Calls:** 149, all returned. Extractor 2, classifier 23, MiniCheck 22,
  DeBERTa 22, judge A 40, judge B 40. Fixture
  `0bbccaa6…`, identities `c8b78f42…`.
- **Gemma phase:** 1,813 s, with 1,741 samples and zero errors. Gemma resident
  memory peaked at 26.38 GiB (footprint 13.44 GiB). Swap went from 0.75 to a
  maximum of 3.44 GiB. Peak pressure was 2.
- **Judges phase:** 699 s, with 676 samples and zero errors. Resident memory
  peaked at 12.93 GiB for judge A and 10.38 GiB for judge B (footprints 10.80
  and 10.31 GiB). The Python process peaked at 3.54 GiB resident. **Swap went
  from 1.97 to a maximum of 13.21 GiB**, the swap total grew to 14 GiB, and
  there were about 1.0 M swap-outs. Peak pressure was 2.
- **Timing:** the judges' `ready` came about 6,865 s after `switch_to_judges`.
  By the owner's report, that was idle time: the owner was not watching the run
  and typed `ready` late, so the interval is mostly waiting; the Gemma stop and
  judge load inside it were not timed separately. Continuous measurement: 9,455 s,
  including that wait; the two measured phases total about 2,512 s. The judges
  phase is measured from `ready`, so its swap figures (start 1.97 GiB) cover the
  699 s of active judging, not the wait.

These are measurements only; the wrapper makes no fit or approval decision.
ADR 0006 records the complete tables.

## Owner fit decision, 2026-10-17 (D21-19)

The owner answered: “I accept s11-fixture-5 as the measured 36 GB fit for both
phases, recording the judges-phase swap growth to 13.2 GiB and pressure 2 as an
explicit limitation.” ADR 0006 records the decision and the limitation's scope:
system-wide swap attribution, process-sum accounting, sampled rather than absolute
peaks, earlier passes that reached critical pressure, and a single fixture
document rather than unseen pilot workloads. With D21-10 to D21-12, this resolves
O2. The owner then approved the drafted ADR 0006 text (“Approve as drafted”), so
ADR 0006 is accepted for the pilot v1 baseline, and chose to commit the provisional
smoke-limits file with the model configuration. B1 is complete once its evidence
is committed. B2 has not started, and no pilot operation is authorized.

## B2 preregistration checkpoint, 2026-10-18 (D21-20 to D21-23)

Owner decisions, recorded in plan-only commits `864e92d` and `d7b6e0d`:
- O3 and O4 (D21-20, D21-21): the shipped tie-group evidence convention and the
  labelled-event bootstrap population are retained for this baseline. P19-3 and
  P19-4 stay open at their stated triggers, and neither changes any scoring code.
- D21-22 records the GS5 reconciliation route: no explanation-only path exists, and
  a mismatch is reconciled through Stage 6 re-signing before any share is published.
- O5 (D21-23): the nine values were entered unchanged from the proposal.

The preregistration was frozen through the shipped `freeze_preregistration` and
committed alone at `53ba1903c5dec15d66d3565fcb27e3c60d6b2107`
(`chore(pilot): preregister the feasibility baseline`). `git show --name-only` for
that commit lists exactly one path,
`evaluation/djia-2024q3-2026q2/pilot-v1/preregistration-v1.toml`, 60 lines.

| Check | Result |
| --- | --- |
| Content hash printed by the freeze | `09d51f7453fb3efda24d8f3e4ccf3310a8c4cb024f1af9d800b00cf967f90c04` |
| Hash printed earlier by the metadata constructor | The same value |
| `load_preregistration` on the committed file | Loads; the file hashes to its own `content_hash` |
| Committed values against D21-23 | Floor 0.4; one candidate with a 20-value grid from 0.0 to 0.95; recall floor 0.4; sampling seed 20261018, train 70 (cap 5), dev 24 (cap 3), minimum usable 50, extension step 10; bootstrap seed 20261019, 10000 resamples, level 0.9, `max_undefined_share` 0.1; `undefined_gate` `point_estimate`; the seven required gates |

Provenance: the file was committed before any pilot output existed. The local
`data/runs/pilot/` directory did not exist before the metadata constructor ran in
B2 step 2, and no pass, run or label has been produced. The local
`preregistration-fields.toml` is uncommitted, and no agent opened it.

Not done: B2 step 4 (the local workflow selections) is specified but not run, and
the final baseline ceilings (limits file `8fae7afb…`) are selected but not yet
frozen into any configuration. B3 is blocked on O6, the 28 signed train and dev
gold files and the 8 dev ledger rows. As a file count only, not a validation, the
default branch tracks 3 gold files. No pilot operation is authorized.
