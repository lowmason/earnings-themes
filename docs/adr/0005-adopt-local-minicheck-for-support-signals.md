# 0005: Adopt local MiniCheck for raw support signals

Date: 2026-10-05. Status: implementation adopted; required V4 inference pending.

Stage 8 exposes raw uncalibrated support probabilities on unchanged evidence and
claims. The primary is `lytang/MiniCheck-Flan-T5-Large`, immutable revision
`96eafd01cee2d16cf81aaa2fb226b14f422a37b3`; the explicitly selected alternative is
`MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli`, revision
`6f5cf0a2b59cabb106aca4c287eed12e357e90eb`. Neither adapter accepts evidence or
assigns a theme. A failed primary never selects the alternative.

## Verified primary metadata

The exact revision's [config](https://huggingface.co/lytang/MiniCheck-Flan-T5-Large/blob/96eafd01cee2d16cf81aaa2fb226b14f422a37b3/config.json),
[tokenizer metadata](https://huggingface.co/lytang/MiniCheck-Flan-T5-Large/blob/96eafd01cee2d16cf81aaa2fb226b14f422a37b3/tokenizer_config.json),
[tokenizer vocabulary](https://huggingface.co/lytang/MiniCheck-Flan-T5-Large/blob/96eafd01cee2d16cf81aaa2fb226b14f422a37b3/tokenizer.json),
and [file inventory](https://huggingface.co/api/models/lytang/MiniCheck-Flan-T5-Large/tree/96eafd01cee2d16cf81aaa2fb226b14f422a37b3)
were read as metadata, without acquiring weights. They specify T5 conditional
generation, decoder/pad ID 0, EOS ID 1 and `</s>`. Vocabulary IDs 3 and 209 map to
`▁` and `▁1`. These are first-step scoring positions, not an assertion that
encoding the strings `0` and `1` produces those IDs.

Pinned [upstream inference](https://github.com/Liyan06/MiniCheck/blob/b58b9fa69acbd1015ec970fa65dd752413a053d2/minicheck/inference.py)
uses the first decoder position and two logits at IDs [3,209]. The adapter uses
`predict: ` + premise + EOS + hypothesis, then raw softmax probability for index 1.
It never imports the MiniCheck wrapper, chunks, generates, argmaxes or applies a
label cutoff. Tokenizer metadata declares 512 while upstream wrapper defaults to
2048. We explicitly choose complete encoder input ≤512; this is a conservative
policy requiring V4 validation, not an architectural claim about T5 positions.

The primary inventory contains `pytorch_model.bin`, not safetensors. It is loaded
explicitly with `use_safetensors=False`, `weights_only=True`. This metadata-driven
serialization choice was surfaced to and approved by the controller before
changing the provisional assumption. The exact [Transformers 5.18 loader source](https://github.com/huggingface/transformers/blob/v5.18.0/src/transformers/modeling_utils.py)
exposes `weights_only` on `from_pretrained` and forwards it into `torch.load`.
Installed source was checked for that path. Remote/custom code stays disabled.

## Alternative metadata

The exact alternative [config](https://huggingface.co/MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli/blob/6f5cf0a2b59cabb106aca4c287eed12e357e90eb/config.json)
sets DebertaV2ForSequenceClassification and 0=entailment, 1=neutral,
2=contradiction, max_position_embeddings=512. Its [tokenizer metadata](https://huggingface.co/MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli/blob/6f5cf0a2b59cabb106aca4c287eed12e357e90eb/tokenizer_config.json)
has an enormous sentinel maximum. Pair encoding counts complete inputs and uses
min(caller limit, verified model positions); raw softmax index 0 is the signal.
The alternative explicitly loads the checkpoint's native safetensors file.

## Runtime packaging and observed checks

Official [torch 2.14.1 packaging](https://pypi.org/pypi/torch/2.14.1/json),
[transformers 5.18.0 packaging](https://pypi.org/pypi/transformers/5.18.0/json),
[sentencepiece 0.2.2 packaging](https://pypi.org/pypi/sentencepiece/0.2.2/json),
[tokenizers 0.23.2 packaging](https://pypi.org/pypi/tokenizers/0.23.2/json), and
[safetensors 0.8.0 packaging](https://pypi.org/pypi/safetensors/0.8.0/json)
were checked before adding the extra. Torch supplies cp314 macOS14 arm64 wheels,
SentencePiece cp314 macOS11 arm64, Transformers a Python universal wheel, and
tokenizers/safetensors cp310 ABI3 macOS11 arm64 wheels. Transformers requires
tokenizers≥0.23.1,<0.24 and safetensors≥0.8.0. No prerelease or Python downgrade.
The chosen versions imported on workspace Python3.14.0 arm64; both concrete model
classes imported and a real tensor softmax executed. Mocked adapters execute in
both baseline and optional environments without weights. No claim of real
checkpoint inference follows from these runtime checks.

PyTorch emitted a FutureWarning from `torch/jit/_script.py:1485`:
`torch.jit.script` is not supported in Python 3.14+ and may break. Please switch to
`torch.compile` or `torch.export`. The adapter uses eager evaluation and
`torch.inference_mode`, not JIT. V4 has not established real weight compatibility. This warning remains an explicit
compatibility limitation until the actual primary gate verifies the eager path;
it alone does not establish an inference defect or justify changing approved pins.
Lock changes are limited to the extra, new SentencePiece package, required
Torch2.14.0→2.14.1 and Transformers5.17.0→5.18.0 updates; unrelated pins preserved.

## Upstream checksums and local verification boundary

These are upstream metadata/content checksums, not checksums of locally acquired
weights. Every supplied local file must be independently hashed and matched to its
immutable revision. The loader checks the entire manifest before heavyweight
imports; unknown/unmanifested files and symlink files refuse initialization.

| Primary inference file | Upstream SHA-256 |
| --- | --- |
| config.json | d8e91aa8739d845d2572fa8db9cb6523d06208c14fedb8f7623f49283a305653 |
| tokenizer_config.json | 284a01dc7b81f159449b96cd0d8814f6da64bbdb59833fe3b8398ea36a860550 |
| tokenizer.json | ece24e1e7d9b5a26f4e68a9519b6ea1451474811b52a9da419c9145f1f458fc0 |
| generation_config.json | 3c4ec6a75c47200afbecd413ee6719007f701821d07b6c11a6c30237d3f9c854 |
| special_tokens_map.json | 47389dd56434a0d7d32f736ba34e895b331461980af760e955b62d5c39912626 |
| added_tokens.json | 4b1c1345a66fdd00264819c5adfc3142debfbd3b03767a04f95a39ac2277ca21 |
| spiece.model (LFS object ID) | d60acb128cf7b7f2536e8f38a5b18a05535c9e14c7a355904270e15b0945ea86 |
| pytorch_model.bin (LFS object ID) | 41291881e13c6235ed47149cec903bee9493e45d9d7325587a9fa2e266c526c0 |

| Alternative inference file | Upstream SHA-256 |
| --- | --- |
| config.json | a6c616d6dabeacf90fd0e776c741d3f0f30a05533ccf0bd3b5b62e94cfaa8d57 |
| tokenizer_config.json | 557b3d33d3f41b81ad769244e506549e98a1857d41dd58160aacd4d98d710b5a |
| tokenizer.json | 05402ffae6dd382a8491b1d29bfc139bec5d332662e86a026f433ce54c25c202 |
| special_tokens_map.json | 9463f61e1b109a8eb4688b829260d7c6b1e6dff04c98ff7269bb89e2b92369b9 |
| added_tokens.json | dc046d04c9b0ada7ae6f1dc89c465801799acdf0c9a6aab8c15a1b2d5ca4e91f |
| spm.model (LFS object ID) | c679fbf93643d19aab7ee10c0b99e460bdbc02fedf34b92b05af343b4af586fd |
| model.safetensors (LFS object ID) | 06d6fd89edd4f97816831626daafbdb0b029cf63bae8edc0bccab1d64e2e7707 |

## Weight rights and setup

The primary's pinned [model card](https://huggingface.co/lytang/MiniCheck-Flan-T5-Large/blob/96eafd01cee2d16cf81aaa2fb226b14f422a37b3/README.md)
and alternative's pinned [model card](https://huggingface.co/MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli/blob/6f5cf0a2b59cabb106aca4c287eed12e357e90eb/README.md)
mark the model artifacts MIT. Primary lineage is google/flan-t5-large; alternative
lineage is Microsoft DeBERTa-v3. The user must independently confirm applicable
weight/base-model terms and intended research use on their acquisition date.
These observations do not assert local rights verification or substitute the
software licenses for weight terms. The user has supplied no weights or config.

Acquire the chosen immutable inference files externally into a dedicated absolute
local directory outside `data/`. No import/test downloads weights. A minimal
primary directory contains config.json, tokenizer_config.json, tokenizer.json and
pytorch_model.bin; include the ancillary files above for the original complete
checkpoint configuration/tokenizer, and list every file actually present.
Exclude upstream Python serving scripts; no custom pipeline is loaded. Keep the
JSON config external and uncommitted. This complete example uses upstream metadata
hashes; replace the directory and fill rights verification after actual local
verification. It does not make a supplied directory verified by example alone.

```json
{
  "kind": "minicheck",
  "local_directory": "/absolute/external/checkpoints/minicheck",
  "revision": "96eafd01cee2d16cf81aaa2fb226b14f422a37b3",
  "files": [
    {"relative_path": "config.json", "sha256": "d8e91aa8739d845d2572fa8db9cb6523d06208c14fedb8f7623f49283a305653"},
    {"relative_path": "tokenizer_config.json", "sha256": "284a01dc7b81f159449b96cd0d8814f6da64bbdb59833fe3b8398ea36a860550"},
    {"relative_path": "tokenizer.json", "sha256": "ece24e1e7d9b5a26f4e68a9519b6ea1451474811b52a9da419c9145f1f458fc0"},
    {"relative_path": "pytorch_model.bin", "sha256": "41291881e13c6235ed47149cec903bee9493e45d9d7325587a9fa2e266c526c0"}
  ],
  "runtime_versions": [["torch","2.14.1"],["transformers","5.18.0"],["sentencepiece","0.2.2"],["tokenizers","0.23.2"],["safetensors","0.8.0"]],
  "device": "cpu",
  "precision": "float32",
  "input_limit": 512,
  "encoding_version": "minicheck-first-step/1",
  "label_mapping": [3,209],
  "weight_license": {
    "source_url": "https://huggingface.co/lytang/MiniCheck-Flan-T5-Large/blob/96eafd01cee2d16cf81aaa2fb226b14f422a37b3/README.md",
    "terms_reference": "REPLACE with verified model and base-model weight terms",
    "intended_use": "REPLACE with approved research use",
    "verified_on": "2026-10-05",
    "permits_use": true
  }
}
```

The alternative uses kind `deberta`, its revision/hashes above, native
`model.safetensors`, encoding `deberta-pair/1`, mapping `[0,1,2]`, independently
verified license and `EARNINGS_SUPPORT_ALTERNATIVE_CONFIG`. The supported device
choice is cpu or mps and precision is float32; actual device behavior awaits its
own local execution. Runtime identity binds all file hashes, ordered runtime
versions, device, precision, encoding plus serialization and effective input limit;
these fields already participate in scorer caches and support-run manifests.

## Required V4 runner and unmet gate

After configuring `EARNINGS_SUPPORT_PRIMARY_CONFIG` to the external JSON, sync the
optional extra before entering the network-denied runner. Then execute only:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /usr/bin/sandbox-exec \
  -p '(version 1) (allow default) (deny network*)' \
  uv run --offline --locked --all-packages --extra support-nli pytest \
  packages/earnings-themes/tests/support/test_nli_live.py::test_minicheck_local_primary \
  -m live -q -rs --tb=short
```

The controller verified the actual macOS process denial mechanism separately:
loopback C curl baseline exit0 versus sandbox exit7, and an unpatched child Python
socket connected baseline versus EPERM under this policy. The live test checks an
unpatched socket syscall for PermissionError before adding socket trip assertions.
The two offline environment settings and local-only loaders remain mandatory.
Python socket monkeypatches alone do not establish process-wide network denial.
The smoke refuses absolute or resolved configuration/model paths containing a
`data` component before reading or hashing them. A missing supplied config or
checkpoint visibly skips with V4 pending; an existing invalid/mismatched checkpoint
fails and is never converted into a missing-checkpoint skip.
Never run a whole `-m live` suite; SEC tests have independent live dispatch paths.

The required named primary test has not run: no external config or weights were
supplied. Real checkpoint compatibility, locally verified weight checksums/rights,
complete-input real inference, actual finite score and actual runtime identity in
an executed primary run remain unmet V4 evidence. A missing-config skip cannot
satisfy this gate. Mocked manifest binding is verified independently. Stage 11
retains calibration, pooling, thresholds and stability; V4 remains a Stage8 gate.
