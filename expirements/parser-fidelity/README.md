# Parser-fidelity harness (Stage 1)

This harness measures which HTML parser yields faithful typed structural elements on
real earnings releases (V2), records what edgartools 5.58.0 returns (V1), and keeps
the fixture corpus in `tests/fixtures/releases/` checkable. The spec is
`specs/release-parser-fidelity.md`, and the plan is
`specs/plans/1-release-parser-fidelity.md`.

No package imports anything here. Scripts that declare dependencies are PEP 723 scripts
with committed locks (`<script>.py.lock`). Run them with `uv run --locked --script`.
Standard-library modules run in the workspace environment with
`uv run --locked --all-packages python`.

## Modules

| File | Role | Environment |
| --- | --- | --- |
| `pf_paths.py` | Repository paths and fixture identifiers | stdlib |
| `pf_decode.py` | Browser-equivalent decoding of saved bytes (frozen) | stdlib |
| `pf_space.py` | The primary and fallback matching spaces (frozen) | stdlib |
| `pf_text.py` | Position-mapped space text; the validator's `html.parser` text | stdlib |
| `pf_toml.py` | A minimal TOML writer for generated files | stdlib |
| `pf_fetch.py` | The live-fetch client: identity, throttle, retries, saving | httpx |
| `pf_classes.py` | Class tests and data-table helpers (frozen) | lxml |
| `pf_dump.py` | Element dumps, the network guard, the adapter entry point (frozen) | stdlib |
| `fetch_policy_pages.py` | Fetches and verifies the source register's SEC quotes | script lock |
| `discover.py` | Samples Item 2.02 exhibits and writes the shortlist | script lock |
| `promote_fixtures.py` | Copies approved exhibits into the corpus; writes the manifest | stdlib |
| `validate_gold.py` | Validates hand-marked gold | stdlib |
| `check_fixtures.py` | The exit-criterion-4 harness check | stdlib + git |
| `adapter_edgartools.py` | Candidate: edgartools 5.58.0 `edgar.documents.parse_html` (frozen) | script lock |
| `adapter_secparser.py` | Candidate: sec-parser 0.58.1 on Python 3.13 (frozen) | script lock |
| `walker.py` | Candidate: the bespoke lxml walker; rules in `walker-rules.md` (frozen) | script lock |
| `control.py` | Negative control: `get_text` lines as paragraphs (frozen) | script lock |
| `run_candidates.py` | Runs each candidate twice per release; determinism and network gates | stdlib + uv |
| `freeze.py` | Records and verifies the freeze (`FROZEN.toml`) | stdlib + git |
| `score.py` | Ranked metrics, diagnostics, and residual failures | stdlib |
| `lock_gate.py` | The lock gate, run in a `git archive` scratch copy | script lock |
| `select_parser.py` | Applies the fixed selection rule step by step | stdlib |
| `v1_return_types.py` | V1: declared and observed return types (live) | script lock |

## Tests

```bash
uv run --locked --all-packages pytest expirements/parser-fidelity --import-mode=prepend -q
```

The tests sit beside the modules and make no network calls. `--import-mode=prepend`
puts this directory on `sys.path` for the tests. Root pytest configuration belongs to
Stage 2.

## Policies

- **Live access.** Every network call goes through `pf_fetch.py`, or, for V1, through
  httpx transports wrapped by the same throttle:
  - `EDGAR_IDENTITY` must be set outside Git;
  - request starts are at least 0.5 s apart;
  - each run is capped at 500 requests by default;
  - only one live process runs at a time (`data/runs/parser-fidelity/live.lock`);
  - a 403 that persists stops the run.

  The identity is never written to disk.
- **Order.** No candidate parses a fixture until `FROZEN.toml` verifies and every
  `gold.toml` passes the validator. `run_candidates.py fixtures` enforces this.
- **Freeze.** After `freeze.py record`, a frozen file changes only to fix a crash or a
  network-guard trip caused by harness code. `freeze.py amend` records each such
  change. A change never alters a type mapping or a walker rule.
- **Outputs.** Everything generated goes to gitignored `data/raw/` and `data/runs/`.
