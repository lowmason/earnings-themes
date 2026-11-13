# Run-path performance harness

These scripts measure how long the `pilot run` path takes per unit of work.
Plan 21 B6 stopped after 8 h 15 min (D21-34). Plan 23
(`specs/plans/completed/23-run-path-performance.md`) corrects the path. The scripts here
produced D21-34's figures, and they give plan 23 its before and after numbers.
Plan 24 (`specs/plans/completed/24-cheaper-key-check.md`) makes the support-cache key check
cheaper. `keypath.py` measures that check for one key.

## Invented text only

Each script builds its own documents, claims and codebook from invented text
(GS13). They read no file under `data/`, no pilot view and no cache entry.
They send no request and load no model. Scripted adapters answer every call.
They write only to a temporary directory, which they delete at the end.
The output is phase names, counts, sizes and seconds. It holds no text.

## How to run

Run each from the worktree root. Each takes the `--themes N` option. It sets the
number of invented themes in the codebook. The default is 22, the size of
codebook v0. The first two themes are `capacity` and `demand`, the same as
`tests/coding/cases.py::invented_codebook`. Use `--themes 2` to reproduce the
two-theme figures that D21-34 was planned from.

`realsize.py` builds documents of real length. Its arguments are the number of
documents and the number of one-sentence paragraph elements per document.
Each document gives about one claim. The support-cache key holds every bundle,
claim and quote, so the key size follows the documents and not the claim count.

```bash
uv run --locked --all-packages python expirements/run-path-performance/realsize.py 20 1850 --themes 22
```

`20 1850` is about train's size. The run takes several minutes. It prints one
line per phase as `<phase> n=<count> <seconds> s`. At the end it prints the
per-unit costs:

- proposal replay, per claim
- support replay, per support entry
- `artifact_hash`, per judge entry
- `decide_assignments`, per target

Add `--project` to print the projected time of one train `pilot run`. It prices
plan 23 Task 7's terms from these costs: proposal replay and support replay over
2 passes, the raw-cache sweeps of 4,866 judge entries, the decide calls over 1,170
targets, and a 32 minute load. The gate counts are constants in the script (12
sweeps and 9 decides over one tiny `make_run`). It then prints two costs that the
plan's formula leaves out, with their own totals: the classifier-cache sweeps, and
the `reverify_support_run` calls that sit outside `decide_assignments`.

`keypath.py` builds the same invented source as `realsize.py`: its arguments are
the number of documents and the number of one-sentence paragraph elements per
document. It builds the cache key of one claim and one judge cache entry, and no
entry for any other claim. So it runs in about a minute. It prints one line per
phase for that one key, in ms, best of 3:

- the key build (`scorer_key`)
- `SupportCacheKey(material)`
- `_binding_once` on a fresh key text
- `_material_kind` on a fresh key text
- `artifact_hash` of the judge entry, on a fresh key text and with the per-text
  memos warm
- the entry parse

It ends with the byte size of each top-level value of the key. "Fresh key text"
means that the per-text memos (`_binding_once`, `_material_kind`) are emptied
before each run. A sweep over many entries meets this case for every entry.
The other memos stay as they are. `--every N` makes a claim in every Nth
extraction window. `--every 1` gives about 620 claims, so the key holds more
source claims and quotes. The default is about one claim per document.

```bash
uv run --locked --all-packages python expirements/run-path-performance/keypath.py 20 1850 --themes 22
uv run --locked --all-packages python expirements/run-path-performance/keypath.py 20 1850 --themes 22 --every 1
```

`scaling.py` builds small documents and many claims. Its arguments are the
number of documents, then one or more claim counts per document. It runs once
for each claim count and times each phase that `pilot run` repeats: replay of
proposals and support, support write and read, proposal-support validation,
decisions, and the coding run's write, read and reverify.

```bash
uv run --locked --all-packages python expirements/run-path-performance/scaling.py 20 2 4 8 --themes 22
```

## The costs are floors

Read every figure as a floor, not as a forecast. This holds for `keypath.py` too.
Its keys hold invented text, so a real key can be larger and slower to check. Real releases hold longer
sentences, more quotes per claim and larger prompts. The invented codebook has
short themes with one example each. Real cache entries can be larger, so real
reads and hashes can take longer. Scripted adapters answer at once. Real model calls
are not part of these figures. A projection from these costs is a lower bound.
Compare a run only with another run of the same arguments on the same machine.
Do not run another heavy job while a measurement runs.
