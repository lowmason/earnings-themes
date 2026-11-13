# Cheaper Exact Key Check Implementation Plan

**Status:** DRAFT for the owner's review (2026-11-13). Not yet approved.

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut the cost of the support-cache key check so that one train-scale `pilot21` replay command projects to under 8 h, without changing any key, record, hash, cache entry or refusal reason.

**Architecture:** A support-cache key's text is 12 to 13 MB, and about 99.7% of it is three values that are the same in every key of one source: `bundles`, `source_claims` and `source_quotes`. Today each key is parsed and dumped about five times per entry. The change splits the text at its fixed canonical markers, checks each big value once per SHA-256 of its text, parses only the small rest, and falls back to today's code for anything the fast path does not accept. The fast path only accepts. Every refusal still comes from today's body.

**Tech Stack:** Python 3.14.0, stdlib `json` and `hashlib`, pydantic, pytest; uv workspace (`earnings-themes`).

**Spec:** none. The requirements are D23-3 in `specs/plans/23-run-path-performance.md` (one train-scale replay command within 8 h), D23-5 there (the 13.49 h projection), and D24-1 and D24-2 below. Read plan 23's Decisions first.

**Evidence (planning session, invented text at real key size, 20 documents x 1850 paragraphs, 22 themes, 21 claims; a floor):**
- One key's material is 12.04 MB. `bundles` is 12,004,141 bytes of it. `json.loads` takes 30.7 ms, `canonical_json` 51.1 ms and a SHA-256 3.9 ms.
- `SupportCacheKey(material)` takes 159 ms (two loads and two dumps). `_validate_binding` takes about 132 ms. Building one key's material takes about 90 ms. `artifact_hash` takes 178 ms per judge entry, of which the entry parse is 10.6 ms.
- Support replay is 0.69 s per entry and one sweep entry costs 0.33 s. At train scale these two terms are 2.99 h and 5.42 h of the 13.49 h projection.
- Proposal replay (3.45 h) has another cause, about 800 `resolve_target` calls per claim. It is out of scope (D24-2).

## Global Constraints

- No stored record, Parquet table, manifest, hash, `configuration_hash`, cache-key text, cache-key digest, cache entry byte, version string or refusal reason may change. Train's support cache (7,792 entries, about 107 GB, P21-1) must still replay. The pinned tests of plan 23 Task 1 (`packages/earnings-themes/tests/support/test_cache_known_answer.py`, `apps/earnings-pipeline/tests/test_pilot_run_bytes.py`) pass after every task.
- Every existing test passes unchanged. If one fails, stop and report its name and failure. Do not edit, skip or loosen an existing test.
- The fast path only accepts. When the text does not split, or any fragment check, parse or compare fails, the call runs today's body unchanged, and that body raises today's refusal. So an accept or a refusal never depends on the memo.
- The fragment memo is process-wide, content-keyed and exact: its key is the level plus the SHA-256 of the fragment's UTF-8 bytes, its value holds no text, and only a fragment that passed is remembered. It holds at most 64 entries. It is not a gate scope memo. `assess_run` and its scorer/judge path still get no scope memo.
- `SupportCache.artifact_hash` still reads the entry bytes and hashes them on every call (plan 15 Task 3, plan 23 Global Constraints).
- Each memoized body is a module-level function called through its module's globals, so a test can count its calls with `monkeypatch.setattr`.
- Tests and helpers use invented text only (GS13). No agent opens `data/`, `/private/tmp/earnings-plan21`, or `.handoff/plan21-native-archives`. No agent runs the root suite, `tests/integration/test_stage6_wording.py`, browser or user-only modes, or `-m live`.
- Commands: `uv run --locked --all-packages pytest <paths> -m "not live and not browser" -q --tb=short`; `uv run --locked ruff check .`; `uv run --locked ruff format --check .`.
- Review of Tasks 2 and 3 runs at Opus, because they decide exactness.

## Review Focus

1. One changed character anywhere in a big fragment must never be served by the memo. The changed text has another hash, so it is checked in full and refused as today (Tasks 2 and 3, `test_a_changed_fragment_is_checked_anew_and_refused`).
2. A split that lands inside a fragment must behave as today: a nested key named `claim`, and the marker text inside an escaped string (Task 1 corpus, checked in Tasks 2 and 3).
3. A memoized good fragment with a bad rest (wrong `kind`, an extra or a missing key, a blank `claim`, a bad `provenance_hash`) is refused as today (Tasks 2 and 3, `test_a_good_fragment_with_a_bad_rest_is_refused`).
4. Non-canonical encodings of an otherwise identical material (whitespace, `\u` escapes, `1.0` for `1`, reordered or duplicate keys, trailing text, truncation) are refused as today (Task 1 corpus, checked in Tasks 2 and 3).
5. The memo keeps digests only, stays bounded, and gives the same results under concurrent use (Task 2, `test_the_fragment_memo_keeps_digests_only` and `test_concurrent_key_construction_agrees`).

## Decisions

- **D24-1** (owner, brief, 2026-11-13): after plan 23 Task 7's projection of 13.49 h, plan a cheaper exact key check (answer “Plan cheaper key check”). Applied in: Goal, Tasks 2 and 3.
- **D24-2** (owner, brief, 2026-11-13): the scope is the key check only. The `resolve_target` memo for proposal replay stays out (answer “Key check only”). If Task 4's projection is still 8 h or more, Task 4 stops and reports; it adds no further lever. Applied in: Task 4.

---

### Task 1: Pin the key check against an oracle and add the key-path harness

**Files:**
- Create: `packages/earnings-themes/tests/support/test_key_check_equivalence.py`
- Create: `expirements/run-path-performance/keypath.py`
- Modify: `expirements/run-path-performance/README.md`

**Interfaces:**
- Produces, in the test file:
  - `oracle_key(material: str) -> str`: a frozen copy of today's `SupportCacheKey.__new__` logic. It returns the digest text or raises `SupportError("malformed_record")`.
  - `oracle_binding(key_text: str, material: str, kind: str) -> tuple`: a frozen copy of today's `_validate_binding` body, which calls the unmemoized `_check_records`.
  - `oracle_kind(material: str) -> str`: `json.loads(material)["kind"]`.
  - `outcome(call) -> tuple`: `("ok", value)` or `("refused", type name, str(error))`.
  - `corpus() -> list[tuple[str, str]]`: labeled materials. The real scorer and judge materials of the invented `assessed_case` (the fixture path `test_cache_known_answer.py` uses), plus one labeled mutation for each of: a character changed inside the document text, an element `end` changed, whitespace added after a comma in the rest, two top-level keys swapped, a duplicate key, `kind` changed to the other valid kind and to an invalid one, an extra key sorted first (`"a"`) and one sorted last (`"zzz"`), a dropped key, a `é` escape for a raw character, `1.0` for an integer, trailing text, truncation, an extra `"claim"` key inside the first element, the text `,"claim":` inside an escaped document string, an empty `bundles` list, `bundles` as `null`, one `source_claims` and one `source_quotes` record changed, and a `provenance_hash` in upper case.
- Produces `expirements/run-path-performance/keypath.py`: `uv run --locked --all-packages python expirements/run-path-performance/keypath.py <docs> <paragraphs> [--themes N] [--every N]` builds the realsize invented source and prints one line per phase for one key, in ms: key build (`scorer_key`), `SupportCacheKey(material)`, `_binding_once` on a fresh key text, `_material_kind`, `artifact_hash`, and the entry parse. It also prints the byte size of each top-level value. `--every N` makes a claim every N windows, so `--every 1` gives about 620 claims. It builds no cache entries for any claim but one.

- [ ] **Step 1: Write `test_the_oracle_accepts_the_real_materials` and `test_every_mutation_gets_the_oracles_outcome`.** The first asserts that `oracle_key`, `oracle_binding` and `oracle_kind` accept every real material, and that today's `SupportCacheKey`, `_validate_binding` and `_material_kind` return the same values. The second is parametrized over `corpus()`: for each material and each of the three functions, `outcome(today's)` equals `outcome(oracle)`. Use the oracle's digest as `key_text` when it accepts, and the SHA-256 of the material's bytes when it does not.
- [ ] **Step 2: Run** `pytest packages/earnings-themes/tests/support/test_key_check_equivalence.py`. Expected: PASS (today's code is the oracle). Check that the corpus has at least 25 labels, and that at least 5 are refused by the oracle at each of the three functions (assert it).
- [ ] **Step 3: Write `keypath.py`** to the interface above, in the style of `realsize.py`. Invented text only. Add its usage and the plain statement that its figures are floors to the README.
- [ ] **Step 4: Run** `keypath.py 20 1850 --themes 22`, and again with `--every 1`. Keep both outputs for Task 4 (they are the before figures; the planning figures above are the reference).
- [ ] **Step 5: Run ruff and the new test; commit** `test(perf): pin the key check against an oracle and add the key-path harness (plan 24)`.

### Task 2: The fragment check and the constructor fast path

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/support/cache.py` (`SupportCacheKey.__new__` and new module-level helpers)
- Test: `packages/earnings-themes/tests/support/test_key_check_cost.py`

**Interfaces:**
- Consumes: Task 1's `oracle_*`, `outcome` and `corpus` (import them from the test module, or move them to `tests/support/cases.py` in this task and import from there).
- Produces in `cache.py`, as module-level functions:
  - `_split_material(material: str) -> tuple[tuple[str, str, str], str] | None`. The canonical key order puts `bundles` first and `source_claims`, `source_quotes` after `schema_version`. The three fragments are: the text between `{"bundles":` and the first following `,"claim":`; the text between `,"source_claims":` and the first following `,"source_quotes":`; the text between `,"source_quotes":` and the first following `,"source_run":`. It returns the three fragments and the placeholder, which is the material with each fragment replaced by `[]`. It returns `None` when a marker is missing or out of order.
  - `_check_fragment(level: Literal["canonical", "valid"], name: Literal["bundles", "source_claims", "source_quotes"], fragment: str) -> None`. `canonical` parses the fragment and requires that `canonical_json` of the parse equals the fragment. `valid` also requires the parse to be a list and applies, for `bundles`, today's per-bundle checks, and for `source_claims` and `source_quotes`, `_check_records_once(Claim | Quote, parsed)`. Any failure raises `ValueError`.
  - `_fragment_checked(level, name, fragment) -> None`. It looks up `(level, sha256_hex(fragment.encode()))` in a bounded `OrderedDict` behind a lock. On a miss it calls `_check_fragment` and remembers the key only on success. The size is `_FRAGMENT_MEMO_SIZE = 64`.
  - `_light_material(material: str, level) -> dict | None`. It splits, checks the three fragments through `_fragment_checked`, parses the placeholder, and returns the parse only if `canonical_json` of it equals the placeholder. Any `ValueError` or `TypeError` gives `None`.
- `SupportCacheKey.__new__` tries `_light_material(material, "canonical")`. On a dict it builds the key with the digest `sha256_hex(material.encode())` (equal to `digest(json.loads(material))` whenever the material is canonical). On `None` it runs today's body unchanged.

- [ ] **Step 1: Write the failing tests** in `test_key_check_cost.py`, over the invented `assessed_case`:
  - `test_the_big_texts_of_one_source_are_checked_once_for_all_its_keys`: build every scorer and judge key of the case. Counting `_check_fragment` through `monkeypatch.setattr`, assert 3 calls at level `canonical`, one per fragment name, and not more as more keys are built.
  - `test_a_changed_fragment_is_checked_anew_and_refused`: for each of the three names, change one character so that the text stays canonical JSON but differs (an element `end`, a claim text, a quote span). Assert `_check_fragment` runs again for that name, and that `outcome(SupportCacheKey(changed))` equals `outcome(oracle_key(changed))`. Add a change that breaks canonical form (a space after a comma): it is refused as the oracle refuses it.
  - `test_a_material_that_does_not_split_takes_todays_path`: a minimal canonical material with no markers gets the oracle's outcome, and `_check_fragment` is not called.
  - `test_the_fragment_memo_keeps_digests_only`: after building keys, every memo key is a pair of short strings, no value is text, and after 80 distinct fragments the memo holds at most 64 entries.
  - `test_concurrent_key_construction_agrees`: 8 threads build the same key 20 times each. All digests equal the oracle's.
  - `test_every_mutation_gets_the_oracles_outcome_for_the_constructor`: parametrized over Task 1's `corpus()`, constructor only.
- [ ] **Step 2: Run them.** Expected: FAIL on the counts (`_check_fragment` does not exist yet).
- [ ] **Step 3: Implement** the four helpers and the constructor fast path to the interfaces above. A fragment is a `str`; never keep it after the call returns.
- [ ] **Step 4: Run** `pytest packages/earnings-themes/tests/support`, Task 1's two pinned tests, and `tests/contracts`. Expected: PASS, with every existing test unchanged.
- [ ] **Step 5: Measure** `keypath.py 20 1850 --themes 22`. Record `SupportCacheKey(material)` (reference before: 159 ms; target: 25 ms or less with a warm memo) in the commit body.
- [ ] **Step 6: Commit** `perf(themes): check a key's big constant texts once per content hash (plan 24)`.

### Task 3: The binding and kind fast paths

**Files:**
- Modify: `packages/earnings-themes/src/earnings_themes/support/cache.py` (`_validate_binding`, `_material_kind`)
- Test: `packages/earnings-themes/tests/support/test_key_check_cost.py`

**Interfaces:**
- Consumes: Task 2's `_light_material`, `_fragment_checked`, `_check_fragment`.
- Produces:
  - `_check_material(material: dict, fragments_checked: bool) -> tuple[request, identity]`: every check of today's `_validate_binding` except the canonical-text and hash comparisons. When `fragments_checked` is true, the `bundles`, `source_claims` and `source_quotes` checks are skipped, because `_check_fragment("valid", …)` did them. The set-of-fields, `kind`, version, record, policy, `source_run`, `evidence`, `contexts`, `claim`, `provenance_hash`, `request` and `identity` checks stay in it.
  - `_validate_binding(key_text, material_text, kind)` keeps its signature. It tries `_light_material(material_text, "valid")`. On a dict it requires `sha256_hex(material_text.encode()) == key_text`, then calls `_check_material(parsed, True)`. On `None`, or on any `ValueError`, `TypeError`, `KeyError` or `AttributeError` from the fast path, it runs today's body (parse, canonical compare, hash compare, `_check_material(material, False)`), which raises today's `SupportError("malformed_record")`.
  - `_material_kind(material_text)` returns `_light_material(material_text, "canonical")["kind"]` when that is a dict, else `json.loads(material_text)["kind"]`.

- [ ] **Step 1: Write the failing tests** in `test_key_check_cost.py`:
  - `test_the_big_texts_are_validated_once_across_bindings`: count `_check_fragment` at level `valid` over every key of the case. Expected: 3, one per name.
  - `test_a_good_fragment_with_a_bad_rest_is_refused`: with the memo warm, five materials that keep the three big fragments and break the rest (kind changed to the other valid kind, an extra key, a dropped key, a blank `claim`, a bad `provenance_hash`) each get `outcome(_validate_binding(...)) == outcome(oracle_binding(...))`, and the memo does not change.
  - `test_a_changed_fragment_is_validated_anew_and_refused`: as Task 2's, at level `valid`, for an element `end`, a claim record, a quote record.
  - `test_the_kind_of_a_material_is_read_without_parsing_the_big_texts`: with the memo warm, `_material_kind` on a second key of the same source calls `json.loads` only on text under 100 KB (patch `json.loads` in `cache.py` to record sizes).
  - `test_every_mutation_gets_the_oracles_outcome` (Task 1's) extended to all three functions: it must still pass unchanged.
- [ ] **Step 2: Run them.** Expected: FAIL on the counts.
- [ ] **Step 3: Implement** to the interfaces. Move today's checks into `_check_material`, once, so the fast and the slow path share one body.
- [ ] **Step 4: Run** `pytest packages/earnings-themes/tests/support packages/earnings-themes/tests/analysis packages/earnings-themes/tests/coding`, Task 1's two pinned tests, and `tests/contracts`. Expected: PASS, with `test_cache_cost.py`, `test_cache.py` and every other existing test unchanged.
- [ ] **Step 5: Measure** `keypath.py 20 1850 --themes 22` and with `--every 1`. Record `_binding_once` on a fresh key (reference before: about 132 ms; target: 40 ms or less), `artifact_hash` per entry (178 ms; target 60 ms or less), and whether the `--every 1` figures stay within 10 ms of the 21-claim figures. Put them in the commit body.
- [ ] **Step 6: Commit** `perf(themes): validate a key's binding with one parse of its small rest (plan 24)`.

### Task 4: Project the budget and record it

**Files:**
- Modify: `docs/verification/pilot-v1-feasibility.md`, `specs/plans/21-feasibility-pilot-and-threshold-calibration-plan-b.md` (Status line only), `specs/plans/23-run-path-performance.md` (Status line only)

**Interfaces:**
- Consumes: `realsize.py --project` (plan 23 Task 7) and `keypath.py` (Task 1).

- [ ] **Step 1: Run** `uv run --locked --all-packages python expirements/run-path-performance/realsize.py 20 1850 --themes 22 --project` in the background, and wait for it. It prints the projected train `pilot run` time from the measured costs.
- [ ] **Step 2: Decide.** If the plan's total, or the total with the extra terms, is 8 h or more, STOP. Report the per-phase figures to the owner. Add no lever (D24-2). If both are under 8 h, go on.
- [ ] **Step 3: Record** a section “Plans 23 and 24 run-path performance, <date>” in `docs/verification/pilot-v1-feasibility.md`: a before/after table per phase (before: plan 23 Task 1's baseline; middle: plan 23 Task 7's 13.49 h figures; after: this run), the gate counts (6 full checks, 12 sweeps, 9, 25, 9 decides), the key-path figures from `keypath.py` before and after, the note that these are invented-text floors, and one sentence that the sweep bound of 8 was not met (plan 23, D23-9). Match the style of the file's existing sections.
- [ ] **Step 4: Update** the Status lines: in plan 21 add that plans 23 and 24 are implemented on their branch and await merge, and that B6 may resume once they merge (D21-34). In plan 23, say that Task 7 is complete through plan 24.
- [ ] **Step 5: Run** `uv run --locked ruff check .`, `uv run --locked ruff format --check .` and `uv run --locked --all-packages pytest packages apps tests/contracts -m "not live and not browser" -q --tb=short`. Expected: clean, all pass. Then ask the owner to run the root suite and `tests/integration/test_stage6_wording.py` in the main checkout at the branch head.
- [ ] **Step 6: Commit** `docs(pilot): record the run-path performance correction (plans 23 and 24)`. Open the PR only on the owner's go-ahead. It carries plan 23's commits and D21-34 too.
