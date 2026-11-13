# Run-path performance harness

These two scripts measure how long the `pilot run` path takes per unit of work.
Plan 21 B6 stopped after 8 h 15 min (D21-34). Plan 23
(`specs/plans/23-run-path-performance.md`) corrects the path. The scripts here
produced D21-34's figures, and they give plan 23 its before and after numbers.

## Invented text only

Both scripts build their own documents, claims and codebook from invented text
(GS13). They read no file under `data/`, no pilot view and no cache entry.
They send no request and load no model. Scripted adapters answer every call.
They write only to a temporary directory, which they delete at the end.
The output is phase names, counts, sizes and seconds. It holds no text.

## How to run

Run both from the worktree root. Each takes the `--themes N` option. It sets the
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

`scaling.py` builds small documents and many claims. Its arguments are the
number of documents, then one or more claim counts per document. It runs once
for each claim count and times each phase that `pilot run` repeats: replay of
proposals and support, support write and read, proposal-support validation,
decisions, and the coding run's write, read and reverify.

```bash
uv run --locked --all-packages python expirements/run-path-performance/scaling.py 20 2 4 8 --themes 22
```

## The costs are floors

Read every figure as a floor, not as a forecast. Real releases hold longer
sentences, more quotes per claim and larger prompts. The invented codebook has
short themes with one example each. Real cache entries can be larger, so real
reads and hashes can take longer. Scripted adapters answer at once. Real model calls
are not part of these figures. A projection from these costs is a lower bound.
Compare a run only with another run of the same arguments on the same machine.
Do not run another heavy job while a measurement runs.
