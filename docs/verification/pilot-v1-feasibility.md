# Pilot v1 feasibility verification

Status on 2026-11-12: B1 evidence is complete and committed (`a91a8e3`), and the
preregistration is frozen and committed alone (`53ba190`), with the B2 step 4
workflow selections recorded (D21-24). On 2026-10-31, O6 was met: all 28 train and
dev gold files are signed and committed (D21-26). On 2026-11-11, the B3 train pass
exited with `status partial`, and the owner accepted it as the frozen train baseline
(D21-29); see the section "B3 train pass checkpoint". On 2026-11-11, B4
committed 70 train support labels that Codex made under the owner's override
(D21-32); see the section "B4 train labels checkpoint". On 2026-11-12, B5's
train calibration ended `no_candidate` and was committed alone (`0801704`); see the
last section. For B1, the fifth fixture pass, `s11-fixture-5`, completed all roles with verified
Metal all-layer startup evidence and measured both phases; the owner accepted it as
the 36 GB fit with an explicit swap/pressure limitation (D21-19, in the section
"Owner fit decision, 2026-10-17"). Earlier sections
are chronological and state status as of their dates; where a later section closes
an open item (Metal offload, build/phase evidence, fit), it governs. Whole-system
Memory Used and the extractor's local token counts remain unavailable. Final
baseline ceilings are owner-selected below. The only pilot operations recorded are
B3's input preparation and train pass, B4's train labels and B5's calibration. Stage 11 remains open. This record contains metadata and safe
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

### B2 step 4 selections, 2026-10-18 (D21-24)

The owner accepted seven workflow selections for Appendix C's owner JSON: the
bundle ID, the eight run IDs, the raw store root `data/raw/events`, one shared
`rules` block, mask policy `boilerplate` version `1`, issuer names as `publisher`,
and a null `event_at` for all 28 events. Evidence from committed inputs and invented
data only:

| Check | Result |
| --- | --- |
| The shared `rules` block against the approved final limits | Patching the committed provisional limits file with D21-12's ceilings and serializing it the same way reproduces SHA-256 `8fae7afbb60fe45e04e178c800f0ae87e5609423e0a65ad02840ead770d110cd`; the block parses as the limits model |
| A generated owner skeleton against Appendix C's `Owner` model, with invented event IDs | Validates once the 28 publishers are filled in; refuses while any is blank; refuses a naive `event_at`; refuses each fixed permission set to its opposite |
| Appendix C's script | Compiles, its imports resolve and its definitions execute; its `prepare` function has not been run |
| Prompts, lockfile, preregistration and codebook that Appendix C copies | All tracked in git |

Not done: the local owner JSON has not been generated or filled in, and Appendix C
has not been run. The final baseline ceilings are selected but not frozen into any
configuration until Appendix C writes the train and dev configs. B3 is blocked on O6,
the 28 signed train and dev gold files and the 8 dev ledger rows. As file counts
only, not validations, the default branch tracks 3 gold files and no dev ledger
file. No pilot operation is authorized.

## O6 gate, 2026-10-31 (D21-26)

O6 is met. All 28 train and dev gold files are signed and on `main` at `66d4e55`.
PR #30 merged the dev ledger and the other 17 train files. PR #31 merged the 8 dev
files, their signature fix and D21-25. Evidence is counts, IDs, hashes and times
only. No agent opened a release text, a draft, a working copy's items, a view or an
independent record.

| Check | Result |
| --- | --- |
| Gold files tracked under `evaluation/djia-2024q3-2026q2/pilot-v1/gold` | 28: 20 train and 8 dev, per split v1 |
| Rows in `independent-pass.toml` | 8, one per dev event, committed alone at `1439ff0` and unchanged since |
| Each dev independent record against its ledger row | SHA-256 matches, 8 of 8 |
| Ledger commit against the dev drafts | Ledger committed 2026-10-31 11:04:54 -0400; each dev draft file was created between 11:44 and 12:24 that day, after it |
| Dev gold commits | 8, each holding only its own file and citing `Independent pass: 1439ff0.` |
| `gold validate` over the 28 literal IDs | 28 valid and signed; exit 0 |
| `pilot recount` over the 28 literal IDs (D21-25) | 28 rebuilt from their kept drafts, no refusal; exit 0 |
| Recount totals, train (20 files) | accepted 3144, edited 93, rejected 1, added 6 |
| Recount totals, dev (8 files) | accepted 1068, edited 151, rejected 12, added 309 |

The two commands ran with the literal IDs from split v1, never the default all-gold
selection. The agent ran them in the main checkout with the owner's approval, not
through Appendix D's saved launcher.

Signature fix: the 8 dev files were first signed `"Lowell Mason"`, which `gold
validate` accepts because it checks only for a non-blank annotator. GS19 requires
`"Lowell Mason (independent pass, then verified a Claude draft)"`. On the owner's
choice, commit `26ae169` changes only that line in each file. The recount counts are
identical before and after, and no pass existed, so D21-22's post-exposure
disposition does not apply.

Not done: the agent did not run the Stage 6 wording gate. Appendix C has not been
run, and no pilot pass, run or label exists. B3 step 1's remainder, Appendix C and
the intake check, runs next in the owner's terminal.

## B3 train pass checkpoint, 2026-10-31 to 2026-11-11 (D21-27 to D21-29)

B3 steps 1 and 2 ran in the owner's terminal, in the main checkout. Evidence is IDs,
hashes, counts, closed codes and times only. No agent opened a release text, a
prompt, a reply or a judge's free-text field. Times are local (America/New_York).

### Step 1: input preparation and intake, 2026-10-31

| Check | Result |
| --- | --- |
| Code | `main` at `b94cfcc7a64129061c63da8b4baec70befe7d472` |
| Owner JSON (D21-24) | 28 events, 0 with `event_at`, bundle `pilot-v1-inputs-1`; each `publisher` is the issuer's SEC registrant name from the committed universe |
| Appendix C | `status prepared`, train 20, dev 8; the bundle holds 91 files |
| `settings.json` SHA-256 | `bf25bc24603d127746f54f04146f75b7388388cf055304f9a3379a07aeb732b4` |
| `train.json` SHA-256, the train pass's configuration hash | `0389368121cb7f499b85e0e2dec5c58ef4c3311a1c6485a214f9b787ecf9eff2` |
| `dev.json` SHA-256 | `d88b5c455b3f0afa17798e3d87f100e321873e4f60c3b783457c8a8ba502ce8a` |
| Runtime manifest `config/models/pilot-v1-runtime.toml` SHA-256 | `d74cdf30b37741a03e2c029346a8f44149ab0c860724085b29620762d92a035e`, unchanged since `a91a8e3` |
| Intake check | `visibility train 20 dev 8 committed_gold 28 ledger_rows 8` |
| Preregistration content hash | `09d51f7453fb3efda24d8f3e4ccf3310a8c4cb024f1af9d800b00cf967f90c04`, as frozen in B2 |

### Step 2: the train pass

Command, run without change at each start:

```bash
pilot21 pass --settings data/runs/pilot/config/settings.json --partition train --models-root "$EARNINGS_MODELS_ROOT"
```

| Time | Event |
| --- | --- |
| 2026-10-31 | A first launch was refused with `model_mismatch`: the models-root variable named the directory one level too high. The owner corrected the level. |
| 2026-10-31 13:44:56 | Attempt 1 starts at `b94cfcc`. The extraction and both support run records hold this time as `started_at` (17:44:56Z). |
| 2026-10-31 15:07 | Extraction completes and is stored. |
| 2026-10-31 | The agent mistook a stray typed `y` for the operator checkpoint, and the owner unloaded Gemma too early. The owner stopped the pass with Ctrl-C during claim resolution, before any classification request. No `proposals.json` and no coding-cache entry existed. |
| 2026-11-07 17:37:52 | Resume at `b94cfcc` with Gemma only. The stored extraction is reused, and claim resolution takes about 20 minutes. |
| 2026-11-07 17:57 | Classification starts. |
| 2026-11-09 03:17:48 | `proposals.json` is written. |
| 2026-11-09 about 08:36 | The owner unloads Gemma, starts both judges and confirms the checkpoint. The first support-cache entry is at 08:37:11. |
| 2026-11-09 about 08:39 | The pass stops with `Refused: assessment: malformed_record` after 6 support-cache entries. D21-27 records the cause and the correction, and D21-28 the printed reason. |
| 2026-11-09 | PR #34 pins the docs build runner, merged at `4bde871`. The owner's gates at `98a2c11`: 4911 passed, 3 skipped, 28 deselected and 1 warning in 906.50 s; `tests/integration/test_stage6_wording.py` 7 passed. PR #33 merges D21-27 and D21-28 at `7aac525`, which differs from `98a2c11` only in `.github/workflows/docs.yml`. |
| 2026-11-09 about 10:09 | The same command runs again at `7aac525`. The first new entry, at 10:10:06, is a judge B retry with roles `[system, user]`, and it is not refused. |
| 2026-11-10 05:39:42 | The last support-run cache entry; all support targets are evaluated. |
| 2026-11-10 09:52 | `support/` is written. |
| 2026-11-10 12:06 to 18:21:01 | The alternative run's scorer evaluations. |
| 2026-11-10 22:44 | `alternative/` is written. |
| 2026-11-11 00:58 | `pass.json` is written, and the pass exits. |

The phase times after 2026-10-31 are observed file and cache-entry times, not
record fields. The `support` and `alternative` records name `software.git_revision`
`b94cfcc`, but their phase ran at `7aac525` (D21-27's recorded deviation).

Elapsed time, from the observed times:

| Phase | Elapsed |
| --- | --- |
| Extraction, attempt 1 | About 1 h 22 min |
| Classification | About 33 h 21 min |
| Support run, from the rerun to its last entry | About 19 h 30 min |
| Support run write, then read-back and proposal validation | About 4 h 12 min, then 2 h 14 min |
| Alternative run evaluations | About 6 h 15 min |
| Alternative run write, then read-back and pass completion | About 4 h 23 min, then 2 h 14 min |

The four write and read-back periods took about 13 h. They used CPU only and sent no
request. Their cost comes from a store validation loop that grows with targets,
attempts and trials together. A correction will be proposed before the dev pass.

Memory and disk: during classification the reply time rose from about 80 s to about
155 s after a memory-pressure episode (swap about 11.8 GB, pressure level 2). During
the support run, swap used peaked at about 21.9 GB on 2026-11-10 at 01:05, above
D21-19's measured 13.2 GiB. Pressure reached level 2 (warning) and never level 4
(critical). The support cache holds 6,329 entries, about 81 GB, and 7,792 entries
after the alternative run. Each entry is about 13.7 MB because its key material
holds every bundle. Startup printed three library warnings: a Mistral tokenizer
regex warning, a T5 tied-weights notice and torch's `torch.jit` FutureWarning. None
is an error.

### The pass record

| Field | Value |
| --- | --- |
| Partition, mode, events | train, live, 20 |
| Status | `partial` (D21-29) |
| `stability_run_id` | null |
| Content hash | `44a9337fd45895c2473b0a69c88d891cc27a356855559f4ce2936148e6b5eb3b` |
| Configuration hash | `0389368121cb7f499b85e0e2dec5c58ef4c3311a1c6485a214f9b787ecf9eff2`, the `train.json` SHA-256 |
| `extraction.sha256` | `cb63593076b5d9429e2ef780da6ffe19f52238d287187532b7f2c16980a2dfc7` |
| `proposals.sha256` | `7f1fb15a9e09dbf541ad104d5b701c61fc54d79b48ded2fe38213eae454dec45` |
| `primary.sha256` | `35d6303c38e57122acc75f2f18085084315ae917be09a02c5eebbb04173d8257` |
| `alternative.sha256` | `d9eae54227cdb08ab4cf02db3c20bb2c96dc194815a88bd97d5bbdc8c64dd302` |

### Extraction and classification

Extraction run `pilot-v1-train-extraction`, cache mode `live`:

| Count | Value |
| --- | --- |
| Documents | 20, all `completed` |
| Windows | 109, none failed |
| Units | 2,701 |
| Candidates, claims, quotes | 1,171, 1,171, 1,248 |
| Rejections | 0 |
| Requests, cache hits | 109, 0 |
| Prompt and completion tokens | 121,516 and 45,783; 0 unreported |
| Exactness rate | 1.0 |

Classification, from `proposals.json`:

| Count | Value |
| --- | --- |
| Classifications | 1,171: 1,162 `completed`, 9 `incomplete` with `hierarchy_conflict` |
| Attempts | 1,181: 1,171 first and 10 second |
| Attempts with `hierarchy_conflict` | 19: both attempts of the 9 incomplete claims, and 1 first attempt whose retry completed |
| Proposals, attributes, novelty records | 1,170, 1,162, 278 |
| Prompt, completion and reserved tokens | 8,263,039, 33,927 and 10,681,727 |
| Claims per document | 22 to 110, against a ceiling of 128 requests per document; no ceiling bound |

### Support runs

| Field | `support` | `alternative` |
| --- | --- | --- |
| Run ID | `pilot-v1-train-support` | `pilot-v1-train-support-alternative` |
| Configuration hash | `82ad0e5c5ea69dded68a3668cb56b0cc657746c7257d11bdedc41777543ef47e` | `6ba02d7f4f3f64b50215767e252b95f57e6dada71fa7c0aa019cfa4f2a438966` |
| Source run hash | `4d86a0a8c2cd1eb7ab8422aa9a9557bb3e15f49363eb34fce999c6da5c0820af` | The same |
| Lock hash | `e2f8ec4d2ba556a51f30d8dcf9a3b122af4aaa5ed87ca4dc030b91e1930ddc16` | The same |
| Targets | 1,170 | 1,170 |
| Outcomes | 1 `assessed`, 1,105 `flagged`, 64 `incomplete`, 0 `refused` | The same |
| Trials | 4,680: 4,604 available, 76 unavailable | The same |
| Judge attempts | 4,866: 4,680 first and 186 second | 4,866 |
| Evaluations | 1,460 | 1,463 |
| Requests, cache hits | 4,863, 7 | 0, 4,867 |
| Prompt, completion and reserved tokens | 8,095,622, 615,887 and 17,948,144 | 95,834, 0 and 0 |
| Unreported usage | 0 | 0 |

The alternative run sent no judge request and replayed every judge reply from the
cache. Its `trials.parquet` is byte-identical to the support run's.

Retry evidence, support run: 262 judge attempts failed closed validation, 162 with
`invalid_references` and 100 with `malformed_reply`. Of the 186 trials that were
retried, 110 completed on the second attempt and 76 stayed unavailable.

The 76 unavailable trials, one row per judge and presentation (unit: trial):

| Judge | Presentation | Reason | Trials |
| --- | --- | --- | --- |
| Mistral-Nemo | `claim_theme_first` | `invalid_references` | 45 |
| Mistral-Nemo | `evidence_first` | `invalid_references` | 12 |
| Qwen | `claim_theme_first` | `malformed_reply` | 5 |
| Qwen | `evidence_first` | `malformed_reply` | 14 |

Unit: target. 52 of the 64 incomplete targets miss 1 trial and 12 miss 2. Their
`missing` codes are `invalid_references` for 47 targets and `malformed_reply` for 18
targets; one target has both.

### Disposition and open items

The owner accepted the partial pass as the frozen train baseline (D21-29). No
ceiling bound, and no transport error, crash or refusal occurred in the rerun at
`7aac525`. Only 1 of the 1,170 targets is `assessed`.

Not done:
- D21-29 leaves open how a partial dev pass and partial fresh dev runs are treated.
  The owner decides this before dev is exposed.
- D21-27's choice whether to prepare the dev settings again before the dev pass
  is still open.
- The validation loop correction is not yet proposed or applied.
- The agent did not run the Stage 6 wording gate or the default suite for this
  record.

## B4 train labels checkpoint, 2026-11-11 (D21-32)

B4 ran in the owner's terminal, in the main checkout. Evidence is IDs, hashes,
counts, closed codes and times only. The agent read no label view, no working file
and no release text. It counted only the closed fields of the committed labels file.

**The train labels are model-authored.** Codex, running the hosted model
gpt-6-astra, made both answers for all 70 train targets from the blinded view. The
owner overrode the rule that no agent helps answer, for train only (D21-32). No
human reviewed the answers. The answers counted below are Codex's. B5's train
figures therefore measure the judges' agreement with a model, not judge-to-human
agreement (R8.4). The 24 dev labels in B6 stay the owner's unaided answers.

### Code before B4

| Date | Event |
| --- | --- |
| 2026-11-11 | D21-30 (store validation) passes the owner's gates at `0cb2696`: 4913 passed, 3 skipped, 28 deselected and 1 warning in 948.15 s; `tests/integration/test_stage6_wording.py` 7 passed. |
| 2026-11-11 | D21-31 (processed partial runs) passes the owner's gates at `bd3d1dd`: 4929 passed, 3 skipped, 28 deselected and 1 warning in 930.67 s; the wording gate 7 passed. |
| 2026-11-11 | PR #36 merges both at `2fe1770`. |

`sample` and `view` ran at `2fe1770`. `check` ran at `2fe1770` or at `0dd492e`, the
labels commit's parent (PR #37), which adds only `specs/deferred_items.md`. The
code is the same at both.

The B3 section's open items are settled. D21-30 lands the validation correction
and keeps the current dev settings. D21-31 decides when a partial dev pass or a
partial fresh run counts.

### Commands and times

| Command (`pilot21 labels …`, `--partition train`) | Output | Time |
| --- | --- | --- |
| `sample` | `partition train targets 70`, then the 70 target IDs | 33 min 49.9 s |
| `view --labelled-on …` | `partition train targets 70 local_views 1 working_labels 1` | 35 min 45.7 s |
| `check` | `partition train targets 70 labels checked` | 2,138.51 s real (35 min 38.5 s), 2,128.60 s user, 6.64 s sys |

Each command loads the train pass through `load_pass` and sends no request. The
work is CPU-bound: `check`'s user time is 99.5% of its real time. `view` and `check`
each call `sample()` once more than `sample` does, and each took about 2 min
longer. So the load itself takes about 32 min, an estimate from these times. At
1 min 41 s into `sample`, the process's resident size was 591,088 KiB (`ps`), about
577 MiB. D21-30 estimated that, before its correction, the grouping loop alone
would have added at least about 1 h 45 min to each command.

### The sample

`sample` drew 70 targets, at most 5 from each of the 20 train events, from the
targets whose primary outcome is `assessed` or `flagged` (FP8). There was no
shortage. `view` and `check` drew the same sample, and `check` accepted the working
file against it.

### The committed labels

`b0b6005` (`data(pilot): commit blinded train support labels`, parent `0dd492e`)
adds only `evaluation/djia-2024q3-2026q2/pilot-v1/labels/support-labels-v1.toml`,
564 lines. Its body records the Codex authorship. The file has `schema_version` 1,
`train_extensions` 0 and the frozen preregistration's content hash
`09d51f7453fb3efda24d8f3e4ccf3310a8c4cb024f1af9d800b00cf967f90c04`. Each of its
70 labels holds only `target_id`, `target_input_hash`, `partition` (`train` for all
70), `claim_support`, `theme_fit` and `labelled_on` (2026-11-11 for all 70).

| `claim_support` / `theme_fit` | `fits` | `does_not_fit` | `unsure` | Total |
| --- | ---: | ---: | ---: | ---: |
| `supported` | 41 | 18 | 3 | 62 |
| `unsupported` | 2 | 0 | 0 | 2 |
| `unsure` | 4 | 2 | 0 | 6 |
| Total | 47 | 20 | 3 | 70 |

The joint label is positive for 41 targets and negative for 22 (18 + 2 + 2). It is
excluded for 7 (3 + 4), where one answer is `unsure` and neither is negative. The
owner's Appendix F reader printed `partition train labels 70 usable_joint 63
excluded_joint 7`, which agrees. 63 is at least FP8's minimum of 50, so Task 4
step 3's extension is not needed.

### Disposition and open items

B4 is complete. D21-32 is committed at `4562c8e`.

Not done:
- B5, the train calibration, is next.
- The agent did not run the Stage 6 wording gate, which reads the labels file, or
  the default suite for this record.

## B5 train calibration checkpoint, 2026-11-12

B5 ran in the owner's terminal, in the main checkout. Evidence is IDs, hashes,
counts, closed codes and times only. The agent read no label view, no working file
and no release text. The figures below come from the owner's run of Appendix F's
reader, which prints the typed calibration record.

Codex made the train labels (D21-32). So every agreement and AUC figure below
measures agreement with a model's answers, not with a person's (R8.4).

### Command and time

`calibrate` ran on the branch `data/train-calibration` at `8c14cd3`, the merge of
PR #38. Its code is the same as at `2fe1770`, where B4 ran: the commits between them
change only documents, specifications and the labels file.

| Command | Output | Time |
| --- | --- | --- |
| `pilot21 calibrate --settings data/runs/pilot/config/settings.json --partition train` | `calibration 221cc696baf42f16a7a7885358d29fa643c3f129aae33734e58b8a580c8a5394 outcome no_candidate` | 1 h 7 min 6.4 s |

The command loads the train pass, draws the sample again, validates the proposal
against both support runs and then calibrates. It sends no request and needs no
model server. From B4's times, the load and the sample take about 34 min. The other
33 min include the two validations and the bootstrap. Their split was not measured.

### The committed artifact

`0801704` (`data(pilot): freeze train calibration and baseline configuration`,
parent `8c14cd3`) adds only
`evaluation/djia-2024q3-2026q2/pilot-v1/calibration-v1.json`, one line of 3,102
bytes.

| Identity | Value |
| --- | --- |
| `content_hash` | `221cc696baf42f16a7a7885358d29fa643c3f129aae33734e58b8a580c8a5394` |
| `configuration_hash`, the frozen configuration | `1127f2be93d4173fe75f9960daa4aea9a926576ab0e7f7149a0d0e05053c94d1` |
| SHA-256 of the file's bytes | `3b57ff09fb89fdb23b0d3d70b95542576a4a042d456bab3acabbbb4cfea7e44a` |
| `preregistration_hash` | `09d51f7453fb3efda24d8f3e4ccf3310a8c4cb024f1af9d800b00cf967f90c04`, as frozen in B2 |
| `labels_hash` | `85bc7f3c65ab70056973ce373fc21a9dc7bdcb067cd49147e16491dea9f023b9` |

These are distinct identities. `configuration_hash` binds the models, prompts,
policies and ceilings together with the selection, which is null. It is not the
`settings.json` hash or the train pass's configuration hash in the B3 section.
`labels_hash` is the SHA-256 of `support-labels-v1.toml` as committed at `b0b6005`.
The agent hashed that committed file again and got the same value. The record has
`calibration_version` 1, `schema_version` 1, `train_labels` 70 and `usable_labels`
63, which agrees with B4.

### Outcome: `no_candidate`

The menu has one candidate, `minicheck-cutoff-v1`, with 20 cutoffs from 0.0 to 0.95
(D21-23). At every cutoff, Stage 9 accepts none of the 63 joint-labelled targets:
`accepted` is 0, recall is 0.0 and precision is undefined. No cutoff reaches the
recall floor ρ = 0.4, so the fitted cutoff and the selection are null.

Calibration counts a target as accepted only when Stage 9's `decision_vote` would
accept it. A flagged, incomplete or refused target is never accepted. The B3 pass
marked only 1 of the 1,170 train targets `assessed`. Even if that target were
labelled positive and accepted, recall would be 1/41, below ρ. So no cutoff could
reach ρ.

As the spec's §Calibration states, no policy is bound and every target stays in
review. This is a feasibility finding, not an error (Task 5 step 2).

### Judge agreement with the joint label

The κ floor is 0.4, judged on the 90% lower bound (D21-23). It is reported only and
changes no assignment (D19-1).

| Family | κ (90% interval) | AC1 (90% interval) | Labels | Uncertain | Meets floor |
| --- | --- | --- | ---: | ---: | --- |
| Mistral | 0.005 (−0.092, 0.101) | −0.163 (−0.464, 0.141) | 63 | 17 | no |
| Qwen | 0.344 (0.180, 0.476) | 0.496 (0.316, 0.670) | 63 | 9 | no |

Each interval used 10,000 event-clustered resamples, and none was undefined. An
uncertain verdict counts as not supporting in the floor population. Neither family
meets the floor. Mistral's κ is about 0 and its AC1 is below 0. These figures do not
show why.

### Scorer AUC against the claim label

| Scorer | View | AUC | Labelled | No claim label | Scored |
| --- | --- | ---: | ---: | ---: | ---: |
| MiniCheck | `minicheck_joint` | 0.540 | 64 | 6 | 70 |
| DeBERTa | `deberta_joint` | 0.895 | 64 | 6 | 70 |

The 64 claim labels are 62 `supported` and 2 `unsupported` (B4). AUC compares each
positive with each negative, which gives 124 pairs, and the two values are exactly
67/124 and 111/124. With only 2 negatives, one claim moves either value by a large
amount, and the artifact gives no interval for AUC. So the difference between the
two scorers is not a finding.

### Later steps under `no_candidate`

Task 5 step 2 asks that a step that cannot proceed under `no_candidate` be raised
as a protocol blocker. The agent read the code for B6 to B8 and found no step that
needs a selection. That is a code reading, not a run.

- `CalibratedPolicy` refuses an artifact with no selection, and `bind_policy` turns
  that refusal into no policy. Each later caller accepts no policy: `run`, the
  report's run loader, `finalize_coding`, `write_coding_run` and
  `reverify_coding_run`.
- B6's train and dev runs replay with a null `policy_reference`, so every target
  stays in review. `test_normal_run_reuses_live_pass_and_replays_without_dispatch`
  covers that path with a `no_candidate` artifact.
- B7's fresh runs decide with no policy through `finalize_coding`. At this
  checkpoint, no test ran that path with a `no_candidate` artifact:
  `test_fresh_policy_decides_without_changing_acquisition_state` used a selected
  one.
- B8's report loads each run with no policy and reads no selection. The agent did
  not trace the report's figures or gate dispositions when nothing is accepted. No
  test builds a report from a `no_candidate` artifact.

D21-33 (2026-11-12) adds three tests, which change no behavior. They pass at their
commit:
- `test_fresh_policy_decides_without_changing_acquisition_state` now runs B7's
  fresh path with both artifacts. Under `no_candidate`, every decision is `review`.
- `test_complete_normal_run_collects_live_labels_and_replay_decisions` now runs
  B8's run loader with both. Under `no_candidate`, it binds no policy and accepts no
  labelled target.
- `test_an_all_review_baseline_leaves_support_precision_ungated_and_fails` derives
  gates from an all-review dev report. Support precision is ungated as
  `undefined_point`, and the report fails its own gates on
  `zero_gold_evidence_recall`, so no configuration passes.

The report's other figures for an all-review run are still not traced.

### Disposition and open items

B5 is complete. No D21 entry is needed: the run followed Task 5 as written.

Not done:
- B6 is next: the train replay, then the dev pass and run, then the owner's unaided
  dev labels.
- No test covered B7's fresh path, B8's run loader or the gate rule under
  `no_candidate`. D21-33 adds them (above). B8's report figures are still not
  traced, and no test builds a report from a `no_candidate` artifact.
- The agent did not run the Stage 6 wording gate, which reads
  `calibration-v1.json`, or the default suite for this record.

## Plans 23 and 24 run-path performance, 2026-11-13 (D21-34)

D21-34 paused B6 because the train `pilot run` could not finish. Its goal is one
train-scale command in under 8 h. Plan 23 and plan 24 change the run path to meet
that goal. This section records their measured effect. All figures come from
invented text of real key size (20 documents of 1,850 paragraphs, 22 themes). The
agent read no pilot text and nothing under `data/`. The figures are floors: each is
the best of its runs. No stored record, hash, cache-key text, cache-key digest or
cache entry changes. Plan 23's known-answer test pins one key digest, and plan 24's
oracle pins the key check on 187 labelled materials.

### What changed

- Plan 23 (D23-1 to D23-9): each consuming gate shares one memo for its unchanged
  inputs. Every gate that a spec names still checks its inputs in full. The checks
  that repeated inside one gate now run once, and a change made in place during the
  gate is caught when the gate ends.
- Plan 24 (D24-1 to D24-6): a cache key's text is 12 to 13 MB, and 99.7% of it is
  three values that repeat in every key of one source. Each is now checked once per
  SHA-256 of its text, and only the small rest of the key is parsed. This path only
  accepts. When anything is in doubt, the old code runs and gives the old answer.

### Projected train `pilot run`

The harness is `expirements/run-path-performance/realsize.py 20 1850 --themes 22
--project`. It measures each unit cost on a 21-claim source and applies the plan's
formula for train: 1,171 claims, about 7,800 support entries, 12 raw-cache sweeps
and 9 decides. The "before" column applies the same formula to the unit costs that
plan 23's Task 1 measured. It is derived, not measured as one run.

| Unit cost | Before plan 23 | After plan 23 | After plan 24 |
| --- | --- | --- | --- |
| Proposal replay, per claim | 28.118 s | 5.308 s | 5.464 s |
| Support replay, per entry | 3.105 s | 0.690 s | 0.253 s |
| `artifact_hash`, per judge entry | 1.453 s | 0.334 s | 0.053 s |
| `decide_assignments`, per target | 20.267 s | 0.375 s | 0.392 s |

| Phase | Before plan 23 | After plan 23 | After plan 24 |
| --- | --- | --- | --- |
| Proposal replay (1,171 claims, 2 passes) | 18.29 h | 3.45 h | 3.55 h |
| Support replay (7,800 entries, 2 passes) | 13.46 h | 2.99 h | 1.10 h |
| Raw-cache sweeps (12 x 4,866 judge entries) | 23.57 h | 5.42 h | 0.85 h |
| Decides (9 calls x 1,170 targets) | 59.28 h | 1.10 h | 1.15 h |
| Load (measured before plan 23, an upper bound) | 0.53 h | 0.53 h | 0.53 h |
| Total | 115.13 h | 13.49 h | 7.19 h |

With the `reverify_support_run` calls scaled to train's targets, plan 24's total is
7.29 h. The classifier-cache sweeps add under 0.01 h. The margin under the 8 h goal
is about 0.7 h. Proposal replay is the largest term left, and plan 24 does not change
it (D24-2). Plan 23's gate counts over one tiny `make_run` are: 6 full checks, 12
raw-cache sweeps, 9 `_proposal_support_inputs`, 25 `_reverify_support_run` and 9
`decide_assignments`. Plan 23 aimed at 8 sweeps and reached 12 (D23-9).

### Key-path figures

The harness is `expirements/run-path-performance/keypath.py 20 1850 --themes 22`,
and again with `--every 1`, which makes 620 claims and a larger rest. Times are in
milliseconds, for one key and one judge entry.

| Phase | Before (21 / 620 claims) | After (21 / 620 claims) |
| --- | --- | --- |
| Key build, `scorer_key` on fresh text | 391.1 / 410.4 | 118.8 / 126.2 |
| `SupportCacheKey(material)` | 160.9 / 169.4 | 12.5 / 13.2 |
| `_binding_once` on fresh text | 134.3 / 140.0 | 12.7 / 13.3 |
| `_material_kind` on fresh text | 29.4 / 32.1 | 8.5 / 8.8 |
| `artifact_hash` on fresh text (a real sweep) | 343.4 / 360.6 | 51.0 / 53.7 |
| `artifact_hash` with warm text memos | 177.3 / 187.7 | 30.2 / 31.9 |
| Entry parse | 10.5 / 10.8 | 10.1 / 10.7 |

After the change, the 620-claim figures stay within 8 ms of the 21-claim figures
(the key build differs most, by 7.4 ms). The larger rest does not hide a cost that
grows with the claim count.

### Evidence that the key check is exact

- Task 1 of plan 24 froze the old key check in an oracle and built a corpus of 187
  labelled materials. It holds the real scorer and judge keys and mutations such as
  a changed byte in each big value, a nested key named like a marker, and an extra,
  dropped or duplicate key inside each part. Every later change must give the
  oracle's outcome on each label, with cold and warm memos.
- Differential fuzz against the oracle found no difference. The controller's runs
  after the last change to the split used about 34,000 inputs for the key
  constructor and about 23,500 for the binding and the kind read, with an
  eight-thread pass. A deliberately weakened check was caught.
- Opus reviews found one issue in Task 2 and none in Task 3. In Task 2, a nested key
  named like a marker could take the split (fixed, D24-5). For Task 3 the reviewer
  broke 17 parts of the fast path on purpose, and the tests caught every one.
- Two existing cost tests clear one memo in the middle of a test. A test-only
  fixture makes that clear also empty the new memo. No existing test is edited
  (D24-6).

### Tests run

At `f038233`, with a clean tree, the agent ran `uv run --locked --all-packages pytest
packages apps tests/contracts -m "not live and not browser" -q --tb=short`. The result
was 5,643 passed, 3 skipped and 17 deselected, in 6 min 54 s. `ruff check .` and
`ruff format --check .` were clean. No existing test is edited.

The owner then ran the gates in the main checkout, detached at `5804663`, on
2026-11-13. `pytest -q` (the root suite) gave 5,810 passed, 3 skipped and 28
deselected, with 1 warning, in 8 min 10 s. The warning is torch's `FutureWarning` in
`test_nli.py`. `pytest tests/integration/test_stage6_wording.py -q` gave 7 passed.

### What this section does not show

- The real train support cache (7,792 entries, about 107 GB) was not replayed here.
  The agent has no access to it. The key format is unchanged. B6's restart is the
  real check. `bind_policy` recomputes B5's configuration hash, so a changed record
  shape refuses before anything is written.
- These are floors on invented text. A real run can differ. Proposal replay (3.55 h)
  and the load (0.53 h, measured before plan 23) are the least certain terms.
- The agent did not run the root suite, the Stage 6 wording gate, the browser modes
  or any live test. The owner ran the root suite and the wording gate, as "Tests
  run" records.
