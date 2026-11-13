# Recover Unusable Saved Responses Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An operator can recover a saved SEC response that is present but unusable, through an explicit, counted, opt-in refetch, and the append-only store only ever moves damaged bytes aside.

**Land before Stage 15's live acquisition.** The roadmap's Stage 15 entry (`specs/evidence-linked-theme-extraction-roadmap.md`, Consumes) says a run of this size makes this recovery worth landing first. **This plan sends no request, so its approved request count is 0.** Every test serves saved fixtures through a fake fetch. The first live use of `--refetch` is a Stage 15 gate, at the count that the command states first.

**Architecture:** Three layers. (1) `fetch/store.py` syncs a new file before it links it, and moves a changed artifact into a `quarantine/` folder beside it when a rewrite needs its name. (2) The readers (`events/filings.py`, `events/release.py`) report each unusable response by URL, apart from each missing one, and every such problem line ends with a remedy. (3) `events discover --refetch URL` and `events acquire --refetch URL` plan their count offline, state it first, refuse any URL that is not unusable, and fetch exactly the planned URLs through the shared SEC client. A refetch is a newer retrieval of the URL. `SavedResponses` already reads the newest retrieval, so no record is edited.

**Tech Stack:** Python 3.14.0, Pydantic, Typer, httpx (CLI only), pytest, Ruff, uv.

**Spec:** none. The requirement is the open item "Recover a saved response that is present but unusable (PR #6's review, P2.1 and P2.2)" under `## PR #6 review (plan 7) — 2026-09-27` in `specs/deferred_items.md`. The plan also argues from `specs/completed/event-discovery-eligibility-and-acquisition.md`: §Store, client, and readers, EV2 (discovery fetches no exhibit) and §Commands ("The plan settles their names and flags").

## Global Constraints

- SEC access: "descriptive User-Agent with a real contact configured outside committed code; project-wide default **2 req/sec shared across all adapters and workers**. Persistent 403 → stop and report, never rotate identity." Every request goes through `open_sec_client`, and only the CLI opens it (P6-22).
- The approved request count is the client's cap, and each retry counts against it. Every command states its count first and prints "requests sent" on every exit (plan 8, F31/F35).
- The store is append-only. Nothing in this plan deletes a file or replaces a valid one. A damaged file is renamed into `quarantine/`.
- EV2: discovery never fetches an exhibit. An exhibit is refetched only by `events acquire`.
- Default tests make "no network and no billable calls — saved fixtures and fake model adapters only". Tests damage copies of the synthetic fixtures under `tmp_path`, never `tests/fixtures/` itself.
- `packages/earnings-ingestion/tests/test_events_discover.py::test_stage_5_has_no_client_or_throttle_of_its_own` forbids `httpx`, `requests`, `urllib`, `socket`, `Throttle(` and `time.sleep` in `events/*.py`. `events/recover.py` takes a `fetch` callable and imports none of them.
- "No downloads, writes, or global state at import time."
- This repository is public. Committed files hold no source text, only synthetic fixtures. Do not open `data/`, `/private/tmp/earnings-plan21` or `.handoff/plan21-native-archives`.
- Do not edit `CLAUDE.md`, the Stage 5 spec, or the roadmap in this plan (see "For the owner's review"). Do not change `uv.lock` or `.python-version`.
- Agents run only the targeted commands in each task. The root suite, the Stage 6 wording gate and the browser modes are owner-only (Task 8).

## Review Focus

Each line below has its test, in the task whose code a person would see fail.

- **SEC serves other bytes on a refetch.** The new retrieval has a new hash and wins, the old damaged file stays where it is, and the build may then read different bytes. The open item `Decide what identifies the event manifest when a store is rebuilt` (F27) owns the identity question. Expected: the command prints a `changed:` line telling the operator to compare `events build`'s content hash with the frozen one. Test: Task 5.
- **A refetch is named for a response that reads fine, that is not saved, or that is an exhibit given to `discover`.** Expected: refused before any client opens, with a message that names the right command. Tests: Tasks 4, 5 and 6.
- **A crash between the move and the rewrite.** Expected: the damaged bytes are in `quarantine/`, the URL is unusable ("bytes are gone"), and the next refetch works. Test: Task 2.
- **The same artifact is damaged twice, with the same bytes and then with other bytes.** Expected: no collision and no lost copy. Test: Task 2.
- **The `quarantine/` folder sits inside a source directory.** Expected: no reader treats it as a saved response, and the top-level `*.html` scan in `tests/integration/test_corpus_quotes.py` still sees only artifacts. Test: Task 2.

## Decisions

- **D1** (owner, brief, 2026-11-13): No brainstorming and no spec. The recorded item is the requirements. Applied in: Spec line.
- **D2** (owner, brief, 2026-11-13): This plan lands before Stage 15's live acquisition. Applied in: Header.
- **D3** (owner, brief, 2026-11-13): Plan id 25, file `specs/plans/25-recover-unusable-saved-responses.md`. Applied in: Header.

---

## Premise check

Checked against `590c2cf` (main), by reading code only.

| Item premise | Result |
| --- | --- |
| The store has no quarantine. | Holds. `grep -ri quarantine packages/earnings-ingestion` finds nothing, and `fsync` appears nowhere in `packages` or `apps`. |
| Discovery fetches only URLs with no retrieval record. | Holds. `_Run.phase` filters on `url not in saved` (`events/discover.py:87`). |
| `issuer_filings` reports a gone or changed file as a problem, never as missing. | Holds. `_Reader.get` (`events/filings.py:151`) adds only to `problems`. |
| `--filing` cannot refetch a saved index page, and `discover_filing`'s hint cannot help. | Holds. `discover_filing` calls `run.phase`, which skips a saved URL. Its hint "run events discover" (`discover.py:222`) cannot fetch what is saved. |
| `write_new` treats changed bytes as a conflict. | Holds (`fetch/store.py:165`). It raises `FileExistsError`, and the artifact's record is never written, so each rerun spends a request and ends the same way. |
| "…ends in an uncaught `FileExistsError`." | **Stale.** Plan 8 added `OSError` to `STOPS` (`events_cli.py`), so `events discover` and `events acquire` end with `Stopped: …holds other bytes` and a request count. It is still a dead end that costs one request per rerun. |
| `cohort/acquire.py` must quarantine too. | Holds in part. It writes only through `ArtifactStore.put` (`_put`), so Task 2 covers its writes. Its `fetch_sec` read of a kept N-PORT document (`store.latest`, line 174) stops on an unusable one with no remedy. That gap is the first item under "Out of scope, filed at completion". |
| The manual repair is documented. | Holds (`docs/verification/djia-events.md`, "Repairing the store"). Its `data/quarantine/` step is replaced by Task 8. `CLAUDE.md:97` and the roadmap's Stage 15 clause repeat the "repair by hand" wording and go stale when this lands. |

## The three cases

Item wording lumps three states together. Only one is quarantined.

1. **Bytes gone.** The retrieval record exists and the artifact file does not. `put` writes the file fresh. No quarantine.
2. **Bytes changed.** The file's bytes no longer hash to its name. Only `put` meets this, at the same name. Quarantine, then rewrite.
3. **Bytes valid, reader refuses them.** Examples: `SecDataError`, an index page that says "Received" for "Accepted", the page of another accession, a redirected record. The file is valid and is never moved. A refetch repairs it only because the newer retrieval wins in `SavedResponses`.

A primary document that reads as `unread` is a legitimate state, not an unusable response.

## Problem producers

Task 3 gives each producer its class. `unusable` is a list of URLs. The remedy is `refetch_remedy(url)`: `refetch it: earnings-pipeline events discover --refetch <url>`.

| Producer | Case | Class | Line |
| --- | --- | --- | --- |
| `_Reader.get` (`filings.py:151`), `saved.get` raises | gone, changed, redirected | unusable | `<url>: <error>; <remedy>` |
| `_Reader.get`, `saved.get` returns `None` | never saved | missing | unchanged: `nothing saved from <url>: run events discover` |
| `_Reader.files`: `SecDataError`, wrong CIK, older-page `SecDataError` | reader refuses | unusable (that file's URL) | with remedy |
| `_Reader.indexes`: `SecDataError`, `AcceptanceTimeError`, another accession's page, `index_disagreement` (F12) | reader refuses | unusable (the index URL) | with remedy. A disagreement may persist after a refetch. SEC's pages then disagree, and the line stays. |
| `_Reader.repeats`: one accession listed more than once | duplicate | unusable (the issuer's submissions URL) | `refetch the submissions file with its older pages: …`. A stale older page after SEC re-paginates is the likely cause. |
| `identify` (`release.py:326`), primary document `saved.get` raises | gone, changed | unusable (`Identification.unusable`) | with remedy |
| `identify`, primary document is `None` | never saved | missing | unchanged |
| `_companyfacts` (`build.py:253`) | gone, changed, refused, wrong CIK | not structured (the build lists problems only) | with remedy |
| `_named_filing` (`events/build.py`): an override's index page gone, changed, refused or disagreeing | as `indexes` | unusable | with remedy. The build reads overrides only after its first stage passes, so this line is reachable only for a page that stage did not read. |
| `citations_refused` (`events/build.py`, also called by `acquire._named`): a cited artifact, read by hash, gone or changed | unusable by hash | `cited_remedy(saved, sha256)`: refetch the URL whose newest retrieval is that artifact. If the URL was saved again with other bytes, the line says a refetch cannot restore the citation. |
| `check_evidence` (`events/evidence.py`): a frozen record's cited artifact gone or changed | unusable by hash | the same `cited_remedy` |
| `acquire._named` (`acquire.py:545`): the override's index page gone, changed or refused | unusable | `refetch_remedy(url)`. The store raises a plain `ValueError` for changed bytes, which this `except` must also catch, so the line keeps its override tag. |
| `discover_filing` (`discover.py:222`): the submissions file is unusable, so it lists no accession | hint cannot help | — | names the unusable file's remedy, not "run events discover" |
| `discover_filing` (`discover.py:235,242`): index page unusable or disagreeing | as `indexes` | — | with remedy |
| `acquire._filing` (`acquire.py:162,172`): index page or primary document | as above | unusable | `refetch_remedy`. Acquisition never fetches these. |
| `acquire._exhibit` (`acquire.py:330`) | gone, changed | unusable | `exhibit_remedy(url)`: `refetch it: earnings-pipeline events acquire --refetch <url>` |
| `cohort/acquire.fetch_sec` kept check | gone, changed | out of scope | Out of scope, filed at completion |

A page that the readers reach only behind another unusable file (an index page behind an unusable submissions file) is classified after that file is refetched. The refusal text in Task 4 says so.

## For the owner's review

Settled defaults. Change any of them at plan review.

1. **Exhibit refetch in `events acquire`.** The item's `Done when:` names discovery, the readers, the store and `cohort/acquire.py`. It does not name `events acquire`. This plan adds `acquire --refetch` anyway, for two reasons. The `REPAIR` problem lines in `acquire.py` are problem lines that need a remedy. Stage 15 is mostly an exhibit run, so exhibits are where damage is likeliest. EV2 forces a separate command. Drop Tasks 6 and 7 if you want the narrower reading, and `REPAIR` keeps its manual wording.
2. **The quarantine lives in the source directory**, at `<root>/<source_id>/quarantine/<artifact name>/<damaged bytes' SHA-256><ext>`. `os.link` needs one filesystem, and `data/` may be a symlink. The old manual step used `data/quarantine/`.
3. **A refetch accepts only unusable URLs.** A usable one is refused, so `--refetch` cannot update a valid response under a frozen citation. A submissions file brings its saved older pages (matched by URL, since a damaged file cannot list them).
4. **`--refetch` is its own mode.** It runs no discovery phase afterwards. A plain `events discover` rerun fetches whatever a refreshed file now lists. This keeps a damaged companyfacts file from ending the run, which is the unguarded read that item P2.3 owns.
5. **Not touched, needs your word.** `CLAUDE.md:97` says the repair is manual. It becomes stale when this lands. The roadmap's Stage 15 clause stales too, and derive-roadmap's reconcile updates it.
6. **P2.3 stays open.** "Read companyfacts in discovery through the problem-collecting reader" shares `discover.py` with Task 4. Task 4's `read_back` guards only its own companyfacts read, and P2.3 should reuse that guard. The two land in either order. The second takes the other's hunk.

## File structure

- Create `packages/earnings-ingestion/src/earnings_ingestion/events/recover.py`: the refetch plan and its execution for discovery's responses.
- Modify `fetch/store.py` (sync, quarantine), `events/saved.py` (`urls`, `hashes`, `refetch_remedy`, `cited_remedy`), `events/filings.py`, `events/release.py`, `events/build.py` and `events/evidence.py` (remedy text only), `events/discover.py` (`read_back`, `Discovery.unusable`, `discover_filing`), `events/acquire.py`. All under `packages/earnings-ingestion/src/earnings_ingestion/`.
- Modify `apps/earnings-pipeline/src/earnings_pipeline/events_cli.py` and `docs/verification/djia-events.md`.
- Tests: `packages/earnings-ingestion/tests/test_fetch_store.py`, `test_cohort_acquire.py`, `test_events_discover.py`, `test_events_acquire.py`, and `apps/earnings-pipeline/tests/test_events_cli.py`.

Task commands:

```bash
uv run --locked --all-packages pytest <files> -m "not live and not browser" -q
uv run --locked ruff check packages apps tests && uv run --locked ruff format --check packages apps tests
```

## Coverage of the item's `Done when:`

| Clause | Task |
| --- | --- |
| `issuer_filings` and identification tell an unusable response from a missing one | 3 |
| An explicit opt-in refetch states its count first, and refetches a submissions file with its older pages | 4, 5 |
| The store quarantines changed bytes by renaming, never deleting or replacing a valid file, `cohort/acquire.py` included | 2 |
| The store syncs before the link | 1 |
| Each problem line names a remedy that works | 3, 6 |
| A test truncates a fixture index page, runs the opt-in refetch over a fake fetch, sees exactly that URL fetched, and rebuilds the synthetic events v1 content hash | 5 (CLI), 4 (library) |

---

### Task 1: `write_new` syncs before it links

**Files:**
- Modify: `packages/earnings-ingestion/src/earnings_ingestion/fetch/store.py` (`write_new`)
- Test: `packages/earnings-ingestion/tests/test_fetch_store.py`

**Interfaces:**
- Consumes: none.
- Produces: `write_new(path: Path, data: bytes) -> None`, same signature and same no-op/`FileExistsError` rules. Callers (`freeze`, `state_table`, `pilot`, `ArtifactStore.put`) change in no way.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_file_is_synced_before_it_is_linked(tmp_path, monkeypatch) -> None:
    # monkeypatch os.fsync and os.link with wrappers that append "fsync" / "link"
    write_new(tmp_path / "a.json", b"x")
    assert calls == ["fsync", "link"]

def test_a_failed_sync_leaves_nothing_at_the_path(tmp_path, monkeypatch) -> None:
    # os.fsync raises OSError("disk")
    with pytest.raises(OSError, match="disk"):
        write_new(tmp_path / "a.json", b"x")
    assert list(tmp_path.iterdir()) == []
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_fetch_store.py -m "not live and not browser" -q`
Expected: the first test FAILS with `calls == ['link']`.

- [ ] **Step 3: Implement.** In `write_new`, call `out.flush()` and `os.fsync(out.fileno())` inside the `with` block, before `os.link`. The existing `finally: os.unlink(temporary)` already cleans up. Sync the file only. A lost directory entry leaves a missing artifact, which is the "bytes gone" case and is recoverable.

- [ ] **Step 4: Run to verify they pass.** Same command; expected: all pass. Run Ruff.

- [ ] **Step 5: Commit**

```bash
git add packages/earnings-ingestion/src/earnings_ingestion/fetch/store.py packages/earnings-ingestion/tests/test_fetch_store.py
git commit -m "feat(store): sync a new file before it is linked"
```

### Task 2: The store quarantines changed bytes

**Files:**
- Modify: `packages/earnings-ingestion/src/earnings_ingestion/fetch/store.py`
- Test: `packages/earnings-ingestion/tests/test_fetch_store.py`, `packages/earnings-ingestion/tests/test_cohort_acquire.py`

**Interfaces:**
- Consumes: Task 1's `write_new`.
- Produces: `ArtifactStore.quarantine(self, source_id: str, sha256: str, media_type: str) -> Path | None` and `ArtifactStore.quarantined: list[Path]` (every path this object moved, oldest first). `ArtifactStore.put` calls `quarantine` before it writes the artifact. `write_new` is unchanged: a frozen manifest or state file that differs is still a real conflict.

- [ ] **Step 1: Write the failing tests** in `test_fetch_store.py`, with `store_in`, `retrieval`, `BODY`, `RIGHTS`, `WHEN`:
  - `test_changed_bytes_are_moved_aside_by_a_rewrite_never_deleted`: put, then `path.write_bytes(BODY[:5])`, then put again with `retrieval(when=WHEN + timedelta(days=1))`. Assert `store.get(...)` returns `BODY`. Assert the damaged bytes sit at `path.parent / "quarantine" / sha256_hex(BODY) / f"{sha256_hex(BODY[:5])}.html"` and `read_bytes() == BODY[:5]`. Assert `store.quarantined == [that path]` and two retrievals.
  - `test_bytes_that_are_gone_need_no_quarantine`: unlink the artifact, put again. `store.quarantined == []`, no `quarantine` folder, `get` works.
  - `test_valid_bytes_are_never_moved_or_replaced`: put twice. The artifact's `st_ino` is unchanged and `store.quarantined == []`.
  - `test_the_same_damage_twice_is_kept_once_and_other_damage_beside_it`: damage with `BODY[:5]` and put; damage with `BODY[:5]` again and put (no error); damage with `BODY[:7]` and put. The quarantine folder holds exactly two files.
  - `test_a_failed_rewrite_after_the_move_loses_nothing`: patch `earnings_ingestion.fetch.store.write_new` to raise `OSError` once. `put` raises, the damaged bytes are in `quarantine/`, `get` raises `FileNotFoundError` ("bytes are gone"), and a second `put` (patch undone) succeeds.
  - `test_the_quarantine_is_not_read_as_a_saved_response`: after the first scenario, `len(store.retrievals("press", sha)) == 2`, `[p.name for p in path.parent.glob("*.html")] == [path.name]`, and `store.latest(...)` returns `BODY`.
  
  In `test_cohort_acquire.py`, `test_a_hand_saved_page_over_changed_bytes_is_quarantined`: `register_saved` a page (`NOW`), truncate `cohort_repo / ref.storage_ref`, `register_saved` the same bytes with `saved_at=NOW + timedelta(days=1)`. No error, `store.get(...)` returns the body, `len(store.quarantined) == 1`. This is the `cohort/acquire.py` clause.

- [ ] **Step 2: Run to verify they fail.** Same command with both files. Expected: the changed-bytes tests FAIL with `FileExistsError: ...holds other bytes`.

- [ ] **Step 3: Implement `quarantine` and the `put` call.**
  - Compute the artifact path with `_artifact_path`. Return `None` if it does not exist, or if its bytes hash to `sha256`.
  - Otherwise name the target `root / source_id / "quarantine" / sha256 / f"{sha256_hex(damaged)}{path.suffix}"` and create its folder.
  - Rename with `os.link(path, target)`, then `os.unlink(path)`. Never `os.rename`, which would replace a file. A `FileExistsError` from the link means the same bytes are already there (the name is their hash), so go on to the unlink.
  - Append the target to `self.quarantined` and return it. Set `self.quarantined = []` in `__init__`.
  - Update the module docstring: different bytes at an artifact's name are damage, `put` moves them aside and writes the artifact again, and the folder is in the source directory because `os.link` needs one filesystem.

- [ ] **Step 4: Run to verify they pass,** then Ruff.

- [ ] **Step 5: Commit**

```bash
git add packages/earnings-ingestion/src/earnings_ingestion/fetch/store.py packages/earnings-ingestion/tests/test_fetch_store.py packages/earnings-ingestion/tests/test_cohort_acquire.py
git commit -m "feat(store): quarantine changed artifact bytes instead of refusing the rewrite"
```

### Task 3: Tell an unusable response from a missing one, and name a remedy

**Files:**
- Modify: `events/saved.py`, `events/filings.py`, `events/release.py`, `events/build.py` (`_companyfacts`, remedy text only), `events/discover.py` (`discover_filing` only)
- Test: `packages/earnings-ingestion/tests/test_events_discover.py`; `apps/earnings-pipeline/tests/test_events_cli.py` (one expected string)

**Interfaces:**
- Consumes: none.
- Produces:
  - `events.saved.refetch_remedy(url: str, what: str = "it") -> str` returning `f"refetch {what}: earnings-pipeline events discover --refetch {url}"`.
  - `events.saved.cited_remedy(saved: SavedResponses, sha256: str) -> str`: for an artifact cited by hash. If some retrieval record names it and it is the newest retrieval of its URL, the refetch remedy for that URL. If the URL was saved again with other bytes, a sentence saying a refetch cannot restore a citation that names its bytes by hash. If no record names it, an empty string.
  - `SavedResponses.urls(self, prefix: str = "") -> tuple[str, ...]`, sorted, and `SavedResponses.hashes(self, url: str) -> frozenset[str]`, the SHA-256 of every retrieval ever saved from `url`. `SavedResponses.__init__` already reads every record, so it keeps both indexes.
  - `IssuerFilings.unusable: tuple[str, ...]` and `Identification.unusable: tuple[str, ...]`: URLs that are saved and cannot be used, never in `missing`.

- [ ] **Step 1: Write the failing tests** in `test_events_discover.py` (reuse `universe`, `layer`, `run`, `Recorder`, `save` from `events.synthetic`, and the `issuer_filings(...)` call shown by `test_issuer_filings_lists_what_the_build_reads_and_lacks`). Populate a store with `run(universe, Recorder(layer), store)`, damage one file, and read the issuer back.
  - `test_each_damaged_response_is_unusable_never_missing`, parametrized: bytes gone (unlink); bytes changed (`write_bytes`); redirected record (`put` a record whose `final_url` differs); wrong-shape submissions (`save` `b"{}"`); another CIK's submissions bytes; wrong-shape older page (Eastfield `-001`); an index page stating "Received" for "Accepted"; another accession's index page; an index page that disagrees with its row (another form); one accession listed in the main file and in an older page. `events.synthetic.index_page`, `submissions_file` and `older_page_entry` build such pages. Each asserts the URL is in `filings.unusable` and not in `filings.missing`, and that exactly one problem for it ends with `refetch_remedy(url)` (for the duplicate, `refetch_remedy(main_url, "the submissions file with its older pages")`).
  - `test_a_missing_response_is_missing_never_unusable`: an empty store. `unusable == ()`, the submissions URL is in `missing`, and the problem is `f"nothing saved from {url}: run events discover"`.
  - `test_a_primary_document_that_cannot_be_read_is_unusable`: bytes changed gives `identification.unusable == (url,)`. A saved plain-text document with no Item line gives `unusable == ()`.
  - `test_a_damaged_companyfacts_file_names_a_remedy_in_the_build`: `build_events(...)` raises `EventBuildError` whose problem for the companyfacts URL ends with `refetch_remedy(url)`.
  - `test_a_cited_artifact_that_cannot_be_read_names_a_remedy_that_works`: override `release-acme-2025-02-28` cites Acme's index page `0009990001-25-000008-index.htm`. With that artifact's bytes changed, `citations_refused(override, saved, folder)` returns a line ending with `refetch_remedy(url)`. When the same URL is saved again with other bytes and the old artifact is then damaged, the line says a refetch cannot restore the citation and contains no `--refetch`. `check_evidence(load_event_evidence(<fixture evidence file>, manifest), store)` returns the same remedy for a damaged cited artifact.
  - `test_discover_filing_names_the_unusable_file_it_cannot_list`: with Acme's submissions bytes changed, `discover_filing(universe, cik, accession, ...)` raises `ValueError` ending with `refetch_remedy(submissions_url(cik))`, and requests nothing.
  - **Expected edits, not regressions.** These tests quote old problem lines. Add the remedy suffix and change nothing else: `test_discovery_names_each_saved_response_the_build_cannot_read` (all three lines) and, in the app tests, `test_discover_names_a_saved_response_it_cannot_read_and_fails`. Both keep their invariant: plain `discover` sends 0 requests for an unusable response.

- [ ] **Step 2: Run to verify they fail** (`pytest` on both test files). Expected: attribute errors on `unusable` and on `refetch_remedy`.

- [ ] **Step 3: Implement.** Follow the "Problem producers" table row by row. `_Reader` gains `self.unusable: list[str]` beside `missing`. In `identify`, add the URL to `unusable` where it already catches `(FileNotFoundError, ValueError)`, and keep the existing guard that avoids a second "nothing saved" line. `repeats` receives the main file's URL for its remedy. `_companyfacts`, `_named_filing`, `citations_refused`, `check_evidence` (which builds its `SavedResponses` only on the failure path) and `discover_filing` change their text only. `acquire._named` is Task 6's. Update the module docstrings of `filings.py` and `discover.py`: a saved response that cannot be read is "refetched by an explicit command", no longer "never fetched again".

- [ ] **Step 4: Run to verify they pass,** then Ruff.

- [ ] **Step 5: Commit**

```bash
git add packages/earnings-ingestion/src packages/earnings-ingestion/tests apps/earnings-pipeline/tests/test_events_cli.py
git commit -m "feat(events): tell an unusable saved response from a missing one"
```

### Task 4: Plan and run a refetch (discovery's responses)

**Files:**
- Create: `packages/earnings-ingestion/src/earnings_ingestion/events/recover.py`
- Modify: `events/discover.py` (`read_back`, `Discovery.unusable`)
- Test: `packages/earnings-ingestion/tests/test_events_discover.py`

**Interfaces:**
- Consumes: `IssuerFilings.unusable`, `Identification.unusable`, `SavedResponses.urls`, `SavedResponses.hashes`, `ArtifactStore.quarantined`, `submissions_page_url`, `pad_cik`.
- Produces, in `events/discover.py`:
  - `ReadBack(problems: tuple[str, ...], unusable: tuple[str, ...])`, frozen.
  - `read_back(universe: UniverseManifest, saved: SavedResponses) -> ReadBack`. It replaces `_unreadable`: the same reads, with `unusable` URLs collected and companyfacts read through a guard of its own. A companyfacts file that cannot be read, or that states another CIK, goes into `unusable` with a problem line, and that issuer's identification is skipped.
  - `Discovery.unusable: list[str]`, filled by `discover` from `read_back`.
- Produces, in `events/recover.py`:
  - `RefetchPlan(urls: tuple[str, ...])` with `count -> int`.
  - `Refetched(fetched: tuple[str, ...], changed: tuple[str, ...], quarantined: tuple[Path, ...], problems: tuple[str, ...])`, frozen.
  - `expected_types(url: str) -> frozenset[str]`: `.json` gives `application/json`, `-index.htm` gives `text/html`, anything else gives `text/html` and `text/plain`.
  - `plan_refetch(universe: UniverseManifest, store: ArtifactStore, named: Sequence[str]) -> RefetchPlan`, raising `ValueError`.
  - `run_refetch(universe: UniverseManifest, plan: RefetchPlan, fetch: Fetch, store: ArtifactStore) -> Refetched`.

- [ ] **Step 1: Write the failing tests** in `test_events_discover.py`:
  - `test_a_refetch_plan_names_only_unusable_responses`: an empty name list, a usable URL, and an unsaved URL each raise `ValueError`. The usable one's message says refetching replaces only responses discovery cannot use, and that an exhibit is refetched by `events acquire --refetch`.
  - `test_a_refetch_plan_adds_a_submissions_files_saved_older_pages`: with Eastfield's submissions file damaged, `plan_refetch(...).urls == (main_url, older_page_url)` and `count == 2`. With only the older page damaged and named, `urls == (older_page_url,)`.
  - `test_a_refetch_fetches_exactly_its_plan_and_mends_each_case`, parametrized over bytes gone, bytes changed, and wrong shape (an index page stating "Received"). After `run_refetch(...)` over a `Recorder(layer)`: `recorder.requested == [url]` and `result.problems == ()`. `build_events(...)` reproduces `load_event_manifest(REPO / FIXTURE_DIR / "events-v1.json").definition.content_hash` (read from the file, never typed as a literal). For bytes changed, `result.quarantined` has one existing path holding the damaged bytes. For bytes gone, it is empty.
  - `test_a_refetch_that_returns_other_bytes_is_reported_changed`: the `Recorder` serves the same index page plus a trailing newline. `result.changed == (url,)`. In the wrong-shape case of the test above, the refetch brings back the original good bytes, so there `result.changed == ()`: a URL counts as changed only when its new bytes match no earlier retrieval of it.
  - `test_a_refetch_that_still_cannot_be_used_reports_the_problem`: the `Recorder` serves the same wrong-shape bytes. `fetched == (url,)` and one problem ends with `refetch_remedy(url)`.
  - `test_read_back_names_an_unusable_companyfacts_file_and_goes_on`: truncate Acme's companyfacts file. `read_back` returns without raising, its `unusable` holds that URL, and the other issuers are still read.

- [ ] **Step 2: Run to verify they fail.** Expected: `ImportError` on `events.recover`.

- [ ] **Step 3: Implement.**
  - `plan_refetch` builds `SavedResponses(store)` and `read_back(...).unusable` once, and refuses each name that is not saved or not in that set. The refusal for a saved URL says it is not among the responses discovery cannot use, that an exhibit is refetched by `events acquire --refetch`, and that a page behind an unusable submissions file is classified once that file is refetched. It expands a name that equals some issuer's `submissions_url(cik)` with `saved.urls(prefix=submissions_page_url(f"CIK{pad_cik(cik)}-submissions-"))`, in sorted order, without repeats. It deduplicates names and keeps their order.
  - `run_refetch` records each URL's earlier hashes with `saved.hashes(url)` before it fetches. Then, for each planned URL, it calls `fetch(url, expected_types(url))` and `store.put(SEC_SOURCE_ID, ..., rights_status=SEC_RIGHTS.rights_status, rights_basis=SEC_RIGHTS.rights_basis)`. A URL whose new sha is not among its earlier hashes goes into `changed`. Last, it runs `read_back` on a fresh `SavedResponses` and returns its `problems`. It runs no discovery phase.
  - Rewrite `discover`'s module docstring to say what `unusable` and `run_refetch` do.

- [ ] **Step 4: Run to verify they pass,** then Ruff.

- [ ] **Step 5: Commit**

```bash
git add packages/earnings-ingestion/src packages/earnings-ingestion/tests/test_events_discover.py
git commit -m "feat(events): plan and run a refetch of unusable discovery responses"
```

### Task 5: `events discover --refetch`

**Files:**
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/events_cli.py` (`discover_command`, module docstring)
- Test: `apps/earnings-pipeline/tests/test_events_cli.py`

**Interfaces:**
- Consumes: `plan_refetch`, `run_refetch`, `RefetchPlan.count`, `Refetched`.
- Produces: `discover_command(..., refetch: Annotated[list[str] | None, typer.Option(help=...)] = None)`. Order of checks, all before `open_sec_client`:
  1. `--refetch` with `--filing` exits 1: `Refused: pass --refetch or --filing, not both`.
  2. `plan_refetch(...)` raising `ValueError` exits 1: `Refused: <message>`.
  3. Print `refetch: {count} requests to SEC, through the shared client`, then each URL on its own line indented two spaces.
  4. No `--max-requests` exits 1: `Refused: pass --max-requests, the request count the user approved`. A value below `count` exits 1: `Refused: --max-requests {n} is below the {count} requests to refetch`.
  5. Open the client with `max_requests=max_requests` (the cap) and run `run_refetch`, through the same stop handling and "requests sent" line as `discover`. Do not copy that block. A repeated `--refetch` is allowed: Typer collects every value, so `_OneFiling` is not needed for it.
  6. Print `refetched {n}; requests sent: {sent}`, then `quarantined: <path>` for each moved file (`shown(path, repo)`), then `changed: {url} returned other bytes than its earlier retrieval; run events build and compare its content hash with the frozen version's before relying on it`, then each `problem:` on stderr. Exit 1 if any problem.

- [ ] **Step 1: Write the failing tests.** In the existing `client(...)` helper add `requested: list[str] | None = None`, appended to by its handler. Use the `repo` and `moved` fixtures and `EVENTS_STORE`.
  - `test_refetch_mends_a_truncated_index_page_and_rebuilds_the_frozen_hash` (the item's test). Truncate (not delete) the artifact of Acme's index page `https://www.sec.gov/Archives/edgar/data/9990001/000999000125000008/0009990001-25-000008-index.htm` to its first 10 bytes. An override of the corpus cites this page, so the hash rebuild below also proves the citation is restored. Then `run(repo, "build", store=EVENTS_STORE)` exits 1, and every `problem:` line on stderr ends with `refetch_remedy(url)`, not just the line for that URL. Run `run(repo, "discover", "--refetch", url, store=EVENTS_STORE)` with no count: exit 1, stdout lines `["refetch: 1 requests to SEC, through the shared client", f"  {url}"]`, `budgets == []`, and stderr `Refused: pass --max-requests...`. Run again with `--max-requests 1`: exit 0, `budgets == [1]`, `requested == [url]`, stdout ends `refetched 1; requests sent: 1` then one `quarantined: data/raw/events/sec-edgar/quarantine/...` line. Finally `run(repo, "build", store=EVENTS_STORE)` exits 0, and its last line is `f"32 events, 27 eligible, content {hash}"` with `hash` read from `load_event_manifest(REPO / FIXTURE_DIR / "events-v1.json")`.
  - `test_refetch_adds_a_submissions_files_older_pages_to_its_stated_count`: Eastfield's main file truncated gives `refetch: 2 requests ...` with both URLs, and `--max-requests 1` is refused before the client opens (`budgets == []`).
  - `test_refetch_refuses_what_is_not_unusable`: a usable URL, an unsaved URL, and a damaged exhibit (EV2) each exit 1 with `Refused`, and `budgets == []`. The exhibit's message names `events acquire --refetch`.
  - `test_refetch_refuses_filing_beside_it`.
  - `test_refetch_stops_on_a_persistent_403_and_prints_its_count`: `client(..., status=403)` gives "Stopped:" on stderr and `requests sent:` on stdout.
  - `test_refetch_reports_other_bytes`: the client serves different valid bytes. Stdout holds a `changed: <url> returned other bytes...` line.

- [ ] **Step 2: Run to verify they fail.** Expected: Typer error `No such option: --refetch`.

- [ ] **Step 3: Implement** as specified above. Update the module docstring: `--refetch` states its count first, needs `--max-requests`, replaces only unusable responses, and a plain `events discover` fetches what a refreshed file now lists.

- [ ] **Step 4: Run to verify they pass,** then Ruff.

- [ ] **Step 5: Commit**

```bash
git add apps/earnings-pipeline/src/earnings_pipeline/events_cli.py apps/earnings-pipeline/tests/test_events_cli.py
git commit -m "feat(events-cli): refetch an unusable saved response, counted first"
```

### Task 6: `acquire` refetches an unusable exhibit

**Files:**
- Modify: `packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py`
- Test: `packages/earnings-ingestion/tests/test_events_acquire.py`

**Interfaces:**
- Consumes: `refetch_remedy`, Task 2's quarantine.
- Produces:
  - `exhibit_remedy(url: str) -> str` returning `f"refetch it: earnings-pipeline events acquire --refetch {url}"`.
  - `unusable_exhibits(events, pilot, store, states_dir, overrides=None) -> tuple[str, ...]`: the saved exhibits of documents a run would attempt (candidates and an override's exhibit) that `saved.get` cannot read.
  - `planned_requests(..., overrides=None, refetch: Collection[str] = ()) -> tuple[int, int]`. A `refetch` URL not in `unusable_exhibits` raises `ValueError`. A refetch URL counts as to-fetch (`most + 1`; `first + 1` when it is its document's first candidate).
  - `acquire(..., refetch: Collection[str] = ())`.
  - `REPAIR` is removed. `_filing` and `_named` use `refetch_remedy(url)`, because acquisition never fetches an index page or a primary document, and `_named` also catches a plain `ValueError`. `_exhibit` uses `exhibit_remedy(url)`.

- [ ] **Step 1: Write the failing tests.** Extend the module's `run` helper with `refetch=()`. Reuse `save_unreadable`, `Served`, `frozen`, `store`.
  - Edit `test_a_saved_exhibit_that_cannot_be_read_is_a_problem_never_fetched_again`: replace the `"repair the store by hand"` assertion with `problem.endswith(exhibit_remedy(url))`. Keep the rest.
  - `test_an_overrides_unusable_index_page_keeps_its_tag_and_names_a_remedy`: an acquisition override whose filing's saved index page has changed bytes gives a problem that starts with the override ID and ends with `refetch_remedy(url)`, and fetches nothing for that page.
  - `test_unusable_exhibits_names_a_saved_pending_exhibit_that_cannot_be_read`: `(url,)` after `save_unreadable`, and `()` without damage.
  - `test_planned_requests_counts_a_refetch_and_refuses_what_is_not_unusable`: `most` rises by 1 with the damaged URL as `refetch`. A usable saved exhibit and an unsaved one raise `ValueError`.
  - `test_acquire_refetches_an_unusable_exhibit_and_acquires_its_document`: with `refetch=frozenset({url})`, `served.requested.count(url) == 1`, `result.problems == ()`, the first pilot event's document is `parsed`, and `len(store.quarantined) == 1`.

- [ ] **Step 2: Run to verify they fail.** Expected: `ImportError` on `exhibit_remedy`.

- [ ] **Step 3: Implement.** Share one walk over the pending documents between `planned_requests` and `unusable_exhibits`. In `_exhibit`, the saved-read branch becomes `if url in saved and url not in refetch`. Update the module docstring's Problems bullet: a saved exhibit that cannot be read is refetched only on an explicit, counted request.

- [ ] **Step 4: Run to verify they pass,** then Ruff.

- [ ] **Step 5: Commit**

```bash
git add packages/earnings-ingestion/src/earnings_ingestion/events/acquire.py packages/earnings-ingestion/tests/test_events_acquire.py
git commit -m "feat(events): refetch an unusable saved exhibit in acquire"
```

### Task 7: `events acquire --refetch`

**Files:**
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/events_cli.py` (`acquire_command`, module docstring)
- Test: `apps/earnings-pipeline/tests/test_events_cli.py`

**Interfaces:**
- Consumes: `planned_requests(..., refetch=...)`, `acquire(..., refetch=...)`, `ArtifactStore.quarantined`.
- Produces: `acquire_command(..., refetch: Annotated[list[str] | None, typer.Option(help=...)] = None)`. The existing `Refused:` path already catches the planner's `ValueError` before the client opens. Print one `refetch: <url>` line after the count line. Pass `refetch=frozenset(refetch or ())` in `options`. Keep one `ArtifactStore` object, so its `quarantined` can print `quarantined: <path>` after the run.

- [ ] **Step 1: Write the failing tests** (`repo`, `moved`, `exhibit_bodies`, and `client(monkeypatch, {**served(), **exhibit_bodies()}, requested=...)`). In each test, on a fresh `moved` store, truncate the saved artifact of the exhibit that `test_a_saved_exhibit_that_cannot_be_read_is_a_problem_never_fetched_again` damages: the first pilot row's. That test proves a run reaches it. A later candidate behind a confirmed first exhibit would never be fetched, and the assertions below would fail. A small helper in `test_events_cli.py` finds its URL the way that test does (`exhibit_bodies()` keys inside the folder of the first pilot row's `release_accession`). Do not run a plain `acquire` first: it would take the one exhibit SEC never served to a terminal state, and the base count would fall from 1 to 0.
  - `test_acquire_refetch_states_its_count_first_and_fetches_the_exhibit`: `acquire --refetch <url>` with no count exits 1. Stdout line 4 starts `at most 2 requests to SEC, through the shared client;`, a `refetch: {url}` line follows, stderr says `Refused: pass --max-requests`, and `budgets == []`. With `--max-requests 2`: exit 0, `budgets == [2]`, `requested.count(url) == 1`, and a `quarantined:` line is printed.
  - `test_acquire_without_a_refetch_names_the_remedy_and_fetches_nothing_for_it`: `acquire --max-requests 1` exits 1 with a `problem:` line ending in `exhibit_remedy(url)`, and `url` is not in `requested`.
  - `test_acquire_refetch_refuses_a_usable_exhibit_before_the_client_opens`: `Refused`, `budgets == []`.

- [ ] **Step 2: Run to verify they fail.** Expected: `No such option: --refetch`.

- [ ] **Step 3: Implement** as specified. Update the module docstring.

- [ ] **Step 4: Run to verify they pass,** then Ruff.

- [ ] **Step 5: Commit**

```bash
git add apps/earnings-pipeline/src/earnings_pipeline/events_cli.py apps/earnings-pipeline/tests/test_events_cli.py
git commit -m "feat(events-cli): refetch an unusable saved exhibit in acquire, counted first"
```

### Task 8: Record the repair, and the owner's gates

**Files:**
- Modify: `docs/verification/djia-events.md`

**Interfaces:**
- Consumes: Tasks 1 to 7.
- Produces: no code.

- [ ] **Step 1: Rewrite "Repairing the store"** (the section after "The requests (plan B)"). Keep the sentence "No repair was needed in plan 8's runs." as history. The new text states:
  - the three cases and which is quarantined;
  - the two commands, each with its count-first gate (run without `--max-requests` to read the count, then rerun with the approved count);
  - that quarantined bytes sit under `<root>/sec-edgar/quarantine/` and are never deleted;
  - that a refetch returning other bytes prints `changed:`, and the operator compares `events build`'s content hash with the frozen one;
  - the manual route that remains for what this plan does not cover: a damaged retrieval record, and the cohort store (`cohort fetch-sec`). It keeps the existing three steps, with the quarantine folder inside the source directory.
- [ ] **Step 2: Replace the sentence** that begins `Recovering a saved response that is present but unusable (P2.1, P2.2) stays` (above "The acquisition") with one that says plan 25 recovered it, and points to "Repairing the store".
- [ ] **Step 3: Run the agent-safe checks:** `uv run --locked --all-packages pytest packages/earnings-ingestion/tests/test_fetch_store.py packages/earnings-ingestion/tests/test_cohort_acquire.py packages/earnings-ingestion/tests/test_events_discover.py packages/earnings-ingestion/tests/test_events_acquire.py apps/earnings-pipeline/tests/test_events_cli.py -m "not live and not browser" -q`, then `uv run --locked ruff check packages apps tests` and `uv run --locked ruff format --check packages apps tests`. Expected: all pass.
- [ ] **Step 4: Commit**

```bash
git add docs/verification/djia-events.md
git commit -m "docs(verification): record the recovery of unusable saved responses"
```

- [ ] **Step 5: Hand the gates to the owner.** The agent does not run these. The owner runs the root suite in their own terminal and records its counts in the PR:

```bash
uv run --locked --all-packages pytest packages apps tests -m "not live and not browser"
```

The Stage 6 wording gate and the browser modes are not needed, because this plan changes no Stage 6 file and no browser code. No `-m live` run is needed, because this plan sends no request. The Plan Completion Protocol then runs: it appends the items below to `specs/deferred_items.md` under `## 25-recover-unusable-saved-responses — <completion date>`, ticks the source item, and asks the owner about the `CLAUDE.md:97` line.

---

## Out of scope, filed at completion

These two items follow the deferred-item schema. The Plan Completion Protocol appends them to `specs/deferred_items.md`, and then adds `→ item:` markers here.

- [ ] Let `cohort fetch-sec` refetch an unusable saved N-PORT document (plan 25's
      scope check): `fetch_sec` in `cohort/acquire.py` decides a filing is kept
      with `store.latest`, which raises when the newest artifact is gone or
      changed. `cohort fetch-sec` then stops with `Stopped: no artifact …` and no
      remedy. Plan 25's quarantine already covers its writes. Cohort v1 is frozen
      and Stage 15 consumes it unchanged, so nobody rebuilds the cohort store
      until a new cohort version. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/` and
      `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py`. Size: quick-fix.
      Revisit if: `cohort fetch-sec` stops on a saved N-PORT document that is gone
      or changed.
- [ ] Name a damaged retrieval record instead of stopping every reader (plan 25's
      scope check): `SavedResponses.__init__` (`events/saved.py`) and
      `ArtifactStore.retrievals` and `latest` (`fetch/store.py`) read
      each record with `Retrieval.model_validate_json` and no handler, so a
      truncated record raises a validation error out of every command, with no
      file named. A record's name carries the first 12 hex digits of its bytes'
      SHA-256, so damage is detectable, but the URL inside an unreadable record is
      unknown, so a refetch cannot be named for it. Paths are under
      `packages/earnings-ingestion/src/earnings_ingestion/`. Plan 25's sync makes new damage
      unlikely, and the manual repair in `docs/verification/djia-events.md` still
      covers old damage. Size: design. Revisit if: any `events` or `cohort` command
      stops with a validation error on a file under `retrievals/`.
