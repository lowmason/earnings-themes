# Harden Ingestion Error Reporting and Refusals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: implement this plan task-by-task via subagent-driven-development (the default) — or executing-plans when your human partner chose inline execution at the handoff. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The cohort, events and browser-setup commands end every ordinary failure with one named line and no traceback, refuse the repeated or unbound records that they accept today, and apply the owner's two rulings on acceptance time and shared releases.

**This plan sends no request, so its approved request count is 0.** Every test serves saved fixtures or a fake fetch. No model is loaded.

**Architecture:** The plan has four kinds of change. (1) Each CLI catches the error types its loaders and readers raise, and prints a `problem:`, `Refused:` or `Failed:` line. (2) The record models and the build refuse repeats: a repeated acknowledgement, a repeated finding ID, an accession that a fund lists twice, and an older page with shifted dates. (3) The evidence record is bound to the store's retrievals and to the manifest's releases. (4) Two owner rulings change the events build. A missing `acceptanceDateTime` has nothing to cross-check, and two issuers' events may share one release. Neither ruling changes events v1, because v1 holds no empty value and no shared release.

**Tech Stack:** Python 3.14.0, Pydantic, Typer, pytest, Ruff, uv.

**Spec:** none. The requirements are 15 open items in `specs/deferred_items.md`, which the owner selected in the `/deferred` pass of 2026-11-13. Line numbers are at `b27794a`:

| Item | Section | Line |
| --- | --- | --- |
| Report `browser setup`'s ordinary failures in one line | `5-structure-aware-canonicalization` | L240 |
| Three small robustness fixes | `5-structure-aware-canonicalization` | L247 |
| Four stale claims | `6-point-in-time-djia-cohort` | L320 |
| Report the cohort CLI's override and terms errors as `problem:` lines | `7-…-plan-a` | L379 |
| Show the operative hashes in `verify-live` | `7-…-plan-a` | L391 |
| Report `events freeze`'s citation errors as `problem:` lines (widened) | `7-…-plan-a` | L465 |
| Bound the periodic reports that can block on acceptance time (amended) | `7-…-plan-a` | L541 |
| Refuse a repeated acknowledgement | `7-…-plan-a` | L593 |
| Bind each evidence citation to its artifact's retrievals | `PR #6 review (plan 7)` | L670 |
| Bind older submissions pages to their dates, and pad the page skip | `PR #6 review (plan 7)` | L705 |
| Refuse two findings that share one `finding_id` | `PR #6 review (plan 7)` | L818 |
| Read companyfacts in discovery through the problem-collecting reader | `PR #6 review (plan 7)` | L861 |
| Refuse a fund filing listed twice in the cohort build | `PR #6 review (plan 7)` | L965 |
| Decide whether two issuers' events may share one release | `PR #6 review (plan 7)` | L979 |
| Print a `quarantined:` line when a plain save moves damaged bytes aside | `25-recover-unusable-saved-responses` | L1792 |

Each item's `Done when:` is its acceptance test. Read the item before its task. The plan also argues from `specs/completed/event-discovery-eligibility-and-acquisition.md` (the Stage 5 spec), which Tasks 4, 5 and 6 amend.

## Global Constraints

- No request and no model. Default tests only: never `-m live`. `EDGAR_IDENTITY` is exported on this machine, so a live test really sends requests.
- events v1, its pilot, cohort v1 and both synthetic corpora must keep loading and rebuilding with unchanged content hashes. Each task names its proof. The real stores are under `data/raw/`, which only the owner's main checkout holds, so the real rebuilds are the owner's gate (Task 10).
- Agents do not open `data/`, `/private/tmp/earnings-plan21` or `.handoff/`. This repository is public. Committed files hold URLs, hashes, pointers and synthetic text only.
- Agents run only the targeted commands in each task. The root suite, the Stage 6 wording gate and the browser modes are owner-only (Task 10, and README "Development checks").
- Do not edit `CLAUDE.md`, the roadmap, `uv.lock` or `.python-version`. The Stage 5 spec is edited only by the amendment steps in Tasks 4, 5 and 6, with the exact wording given there.
- `packages/earnings-ingestion/tests/test_events_discover.py::test_stage_5_has_no_client_or_throttle_of_its_own` forbids `httpx`, `requests`, `urllib`, `socket`, `Throttle(` and `time.sleep` in `events/*.py`.
- Prose in docs and docstrings follows the user's plain-technical-English rule: the main point first, one idea for each sentence, no semicolons.

Task commands, from the repository root:

```bash
uv run --locked --all-packages pytest <files> -m "not live and not browser" -q
uv run --locked ruff check packages apps tests && uv run --locked ruff format --check packages apps tests
```

The fixture proofs that several tasks run:

```bash
uv run --locked --all-packages pytest tests/integration/test_event_fixtures.py tests/integration/test_event_corpus_v1.py tests/integration/test_cohort_fixtures.py -m "not live and not browser" -q
```

## Review Focus

Each line below has its test, in the task whose code a person would see fail.

- **A retrieval record under `retrievals/` is empty or truncated.** Today every `events` and `cohort` command stops with a validation error that names no file. Expected: the command ends with one line that names the record's path and the manual repair, and `events discover` gives no rerun advice. Test: Task 8.
- **A filing has no `acceptanceDateTime`, and its index page is saved.** Expected under reading (a): no finding, the filing is placed by its page, and the build and freeze still reproduce the frozen hash. Test: Task 5.
- **An older page holds one filing accepted on the cutoff at 18:00 ET.** Its `filingFrom` is the next business day. Expected: the page is read and its filing is visible. Test: Task 6.
- **A co-registrant 8-K is listed by two cohort issuers.** Expected under the per-issuer ruling: each issuer's event takes it as its release, and the build raises no problem. Test: Task 4.
- **A plain `events discover` saves over damaged bytes and then stops.** Expected: each moved path prints once, before the request count. Test: Task 9.

## Decisions

- **D1** (owner, brief, 2026-11-13): No spec and no brainstorming. The 15 selected items are the requirements, in one hardening plan. Applied in: Spec line.
- **D2** (owner, brief, 2026-11-13): Item L541 takes reading (a): a missing `acceptanceDateTime` has nothing to cross-check. The saved index page's Accepted value places the filing, and its cross-check is null. This is the owner's ruling in the `/deferred` pass. Applied in: Task 5, Task 5 (spec amendment).
- **D3** (owner, brief, 2026-11-13): Item L979 is per-issuer: two cohort issuers' events may share one co-registrant release. Only two events of one issuer may not. This is the owner's ruling in the `/deferred` pass. Applied in: Task 4, Task 4 (spec amendment).

---

## For the owner's review

These are settled defaults. Change any of them at plan review.

1. **The unreadable retrieval record (L465's third bullet) is in scope, but only as naming.** Task 8 makes each reader raise an error that names the record's path, and each CLI prints that path with the manual repair. Readers still stop on the first damaged record, as they do today. The design item "Name a damaged retrieval record instead of stopping every reader" (L1754) keeps its open questions: whether a reader skips a damaged record and goes on, and how `run_refetch` guards its own read-back. → item: 25-recover-unusable-saved-responses — 2026-11-13. To keep L1754 whole instead, drop Task 8's Steps 1–4 and the matching test. L465 then stays open for that one bullet.
2. **`events freeze` keeps `Refused:` for ordinary refusals.** A `LocatorError` from the evidence record becomes a `problem:` line, as L465 asks. Every other `OSError` or `ValueError` stays `Refused: <error>`, because `test_events_cli_corpus.py` pins `Refused:` for a build of another corpus.
3. **L320's host claim is fixed in the docstring.** `cohort/web.py` says what the code does. `fetch_page` gains no host check. The item allows either.
4. **The slack is seven days, for both bounds.** One constant, `FILING_DATE_SLACK = timedelta(days=7)` in `events/filings.py`, bounds the 8-K trigger (Task 5) and pads the page skip (Task 6). The committed v1 evidence record shows that the latest skipped page ends on 2024-06-23. That date is before 2024-07-01 less seven days, so v1's skip set does not change. An eighth day would read that page.
5. **The optional page check is not adopted.** L705 lets a page's earliest filing date be required to equal its `filingFrom`. Task 6 adds only the required check: a page's filing dates must stay before the next newer page's `filingFrom`, or before the recent block's earliest date.
6. **A shared release reaches acquisition as one document.** Under D3, two events whose release is one filing get one canonical document, with the same `doc_id`, under two `<event_id>:release` states. Each firm-quarter then counts that document's quotes. No v1 issuers are co-registrants. Task 4 changes the build and the spec only.
7. **`browser setup` prints `Failed: <error>`** for a network, disk, subprocess or install failure. A refused archive keeps `Refused: <error>`.

## File structure

All paths are under `packages/earnings-ingestion/src/earnings_ingestion/` unless given in full.

- `browser/install.py`, `browser/store.py`, `browser/serialize.py`, `tests/integration/capture_browser_fixtures.py`, `apps/earnings-pipeline/src/earnings_pipeline/cli.py`: Task 1.
- `cohort/build.py`, `cohort/live.py`, `cohort/records.py`, `cohort/web.py`, `cohort/pdftext.py`, `fetch/robots.py`, `README.md`, `apps/…/cohort_cli.py`: Tasks 2 and 3.
- `sec/data.py` (`repeated_accessions`): Task 3.
- `events/records.py`, `events/build.py`: Task 4.
- `events/acceptance.py`, `events/filings.py`, `events/evidence.py`: Tasks 5, 6 and 7.
- `events/freeze.py`: Tasks 7 and 8.
- `fetch/store.py`, `events/saved.py`, `apps/…/events_cli.py`: Tasks 8 and 9.
- `events/discover.py`, `apps/…/paths.py`: Task 9.
- `docs/data-dictionary.md`: Tasks 2, 5, 6. The Stage 5 spec: Tasks 4, 5, 6. `docs/verification/djia-events.md`: Task 8.
- `tests/integration/test_event_store_v1.py`, `tests/integration/test_cohort_store_v1.py` (new): Task 10.

## Coverage of the items' `Done when:`

| Item | Task |
| --- | --- |
| L240, L247 | 1 |
| L320, L379, L391 | 2 |
| L965 | 3 |
| L593, L818, L979 | 4 |
| L541 | 5 |
| L705 | 6 |
| L670 | 7 |
| L465 | 8 |
| L861, L1792 | 9 |
| Real-store proof of "v1 still rebuilds / still passes" (L541, L670, L705, L965) | 10 |

---

### Task 1: Browser setup and capture robustness (L240, L247)

**Files:**
- Modify: `browser/install.py` (`SETUP_FAILURES`, the end of `install`)
- Modify: `browser/store.py` (`CaptureStore.put`)
- Modify: `browser/serialize.py` (`fixture_capture_json`)
- Modify: `tests/integration/capture_browser_fixtures.py` (`capture_one`)
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/cli.py` (`setup`)
- Test: `apps/earnings-pipeline/tests/test_cli.py`, `packages/earnings-ingestion/tests/test_browser_install.py`, `test_browser_store.py`, `test_browser_serialize.py`

**Interfaces:**
- Produces: `SETUP_FAILURES: tuple[type[BaseException], ...]` in `browser/install.py`, and `fixture_capture_json(capture: RenderedCapture) -> str` in `browser/serialize.py`.

- [ ] **Step 1: Write the failing tests**

```python
# apps/earnings-pipeline/tests/test_cli.py
@pytest.mark.parametrize(
    "error",
    [
        httpx.ConnectError("no route to host"),
        OSError("No space left on device"),
        subprocess.TimeoutExpired(["chrome", "--version"], 60),
        RuntimeError("the cache holds no installed pin after the install"),
    ],
)
def test_setup_reports_an_ordinary_failure_in_one_line(monkeypatch, tmp_path, error):
    def fail(pin, cache, fetch):
        raise error

    monkeypatch.setattr(cli, "load_pin", lambda: load_pin("mac-arm64"))
    monkeypatch.setattr(cli, "install", fail)
    result = RUNNER.invoke(cli.app, ["browser", "setup", "--cache", str(tmp_path)])
    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert result.stderr == f"Failed: {error}\n"
```

- `test_browser_install.py::test_install_raises_when_the_cache_holds_no_pin_afterwards`: use the setup of `test_install_checks_extracts_and_finds_the_binaries`, and monkeypatch the module's `installed` to return `None`. Assert `pytest.raises(RuntimeError, match="holds no installed")`.
- `test_browser_store.py::test_a_failure_file_is_stamped_in_utc`: put a failed capture whose `captured_at` is `datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=5)))`. Assert the path's name is `"20260101T220405000000Z.json"`.
- `test_browser_serialize.py::test_a_fixture_capture_drops_its_screenshots`: build a completed capture with one screenshot `ArtifactRef` (the `make_capture` fixture). Assert `from_capture_json(fixture_capture_json(capture)).screenshots == ()`, and that every other field equals the capture's.
- `test_browser_serialize.py::test_the_capture_script_writes_through_fixture_capture_json`: read `tests/integration/capture_browser_fixtures.py` as text. Assert it contains `fixture_capture_json(capture)` and does not contain `to_capture_json(`. The script imports Selenium, so the test reads it and does not import it.

- [ ] **Step 2: Run the tests and see them fail**

Run the four files. Expected: the parametrized setup test fails with a traceback for each error. The others fail on the `AssertionError`, the `+05:00` stamp, and the missing name.

- [ ] **Step 3: Implement**

- `SETUP_FAILURES = (OSError, httpx.HTTPError, subprocess.SubprocessError, RuntimeError)`. `SubprocessError` covers `TimeoutExpired`. `install` replaces its `assert done is not None` with `raise RuntimeError(f"{cache} holds no installed {pin.version} after the install")`.
- `setup` keeps `except ValueError` → `Refused: …`, and adds `except SETUP_FAILURES as error:` → `typer.echo(f"Failed: {error}", err=True)` and `raise typer.Exit(1) from error`. `cli.py` imports the tuple and does not import `httpx`.
- `CaptureStore.put` stamps `capture.captured_at.astimezone(UTC)`.
- `fixture_capture_json(capture)` returns `to_capture_json(capture.model_copy(update={"screenshots": ()}))`. `capture_one` writes through it.

- [ ] **Step 4: Run the tests and see them pass**

Run the four files and `tests/integration/test_browser_fixtures.py`. Expected: PASS. The committed captures are not regenerated, so the fixture test proves they are unchanged.

- [ ] **Step 5: Commit**

```bash
git commit -m "fix(browser): report setup failures in one line, raise instead of assert, stamp failures in UTC, and drop screenshots from fixtures"
```

---

### Task 2: Cohort CLI problem lines, the live record's operative hashes, and stale claims (L379, L391, L320)

**Files:**
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/cohort_cli.py` (`_build`, `terms_command`, `verify_live_command`)
- Modify: `cohort/build.py` (`CohortBuild.operative_hash`), `cohort/live.py` (`verify_live`), `cohort/records.py` (`LiveVerification`, `LocatorKind.TEXT_SPAN`'s docstring)
- Modify (docstrings only): `fetch/robots.py`, `cohort/web.py`, `cohort/pdftext.py`
- Modify: the `docs/` row of `README.md`
- Modify: `docs/data-dictionary.md` (`### LiveVerification`)
- Test: `apps/earnings-pipeline/tests/test_cohort_cli.py`, `packages/earnings-ingestion/tests/test_cohort_live.py`, `tests/contracts/test_data_dictionary.py`

**Interfaces:**
- Produces: `CohortBuild.operative_hash -> str`, a property: `operative_hash(self.manifest(1, EPOCH))`, the same projection Stage 5 keys on. `LiveVerification.rebuilt_operative_hash: Sha256Hex | None = None` and `LiveVerification.frozen_operative_hash: Sha256Hex | None = None`. The defaults keep records saved before this change loading. Task 10 uses the property.

- [ ] **Step 1: Write the failing tests**

- `test_cohort_cli.py::test_build_and_freeze_report_a_bad_override_as_a_problem`: append to the copy's `overrides.toml` a `reject_assertion` override whose `membership_assertion_id` names no assertion, such as `index-2024-10-31:corvid-common:removed`. `reconstruct` then raises `ValueError("rejections name no assertion: …")`. For `build` and `freeze`, assert exit 1, `isinstance(result.exception, SystemExit)`, and a stderr line that starts with `problem: ` and contains `rejections name no assertion`.
- `test_cohort_cli.py::test_build_reports_a_toml_syntax_error_as_a_problem`: append `"[[overrides]\n"` to the copy's `overrides.toml`. Assert the same three things for `build`.
- `test_cohort_cli.py::test_terms_reports_a_page_walker_1_cannot_read_as_a_problem`: monkeypatch `cohort_cli.terms_digest` to raise `ValueError("walker-1 found no text")`. With `--saved FILE`, assert stderr is `problem: <FILE>: walker-1 found no text\n`. With a fake `open_web_client` whose `fetch` returns a `Fetched`, assert `problem: <URL>: walker-1 found no text\n`. Both exit 1 with `SystemExit`. The existing media-type case keeps its `Refused:` line.
- `test_cohort_live.py::test_an_unreadable_terms_page_is_recorded_not_raised`: monkeypatch `live.terms_digest` to raise `ValueError`. Assert `verify_live` returns, and each terms check has `outcome == "failed"`, a `detail` that starts with `terms page unreadable: `, and its `retrieval` kept.
- `test_cohort_live.py::test_a_register_only_change_keeps_the_operative_hash`: in the `cohort_repo` copy, change only `owner` in the `sec-edgar` entry of `source-register.toml`. That changes `source_register_version` and no fact. Assert `rebuilt_content_hash != frozen_content_hash` and `rebuilt_operative_hash == frozen_operative_hash`. Add `rebuilt_operative_hash == frozen_operative_hash` to `test_an_unchanged_world_rebuilds_the_frozen_manifest`.
- `test_cohort_cli.py::test_verify_live_tells_a_register_change_from_a_changed_fact`: monkeypatch `cohort_cli.run_live` to return two records. Assert that the record with equal operative hashes and different content hashes prints `operative rebuilt <h>; frozen <h>: the facts are unchanged` after the existing `rebuilt …; frozen …` line. Assert that the record with different operative hashes prints `…: a fact changed`.

- [ ] **Step 2: Run the tests and see them fail**

Expected: a traceback for the override and TOML cases, a raised `ValueError` from `verify_live`, and `AttributeError` on the operative fields.

- [ ] **Step 3: Implement**

- `_build` keeps `except CohortError`, and adds `except (OSError, ValueError) as error:`, which prints `problem: {error}` to stderr and raises `typer.Exit(1)`. The cohort's overrides load inside `build`, so this handler covers the overrides loader that L465 also names.
- `terms_command`: `check_media_type` keeps its own `try` and its `Refused:` line. `terms_digest` gets a second `try` on each path, which prints `problem: {saved or url}: {error}`.
- `verify_live`: guard `terms_digest` with `except ValueError as exc:` → `outcome, detail = "failed", f"terms page unreadable: {exc}"`, and keep the retrieval. Fill `rebuilt_operative_hash` from `rebuilt.operative_hash` (`None` when the build raised `CohortError`). Fill `frozen_operative_hash` from `operative_hash(manifests[-1])` (`None` with no manifest).
- `verify_live_command` prints the operative line only when both hashes are present.
- The four stale claims. Make each docstring say what the code does. Change no behavior.
  - `fetch/robots.py`: a 401 or another 4xx disallows everything. A response the client gives up on raises `AccessStop` out of `verdict`.
  - `cohort/web.py`: the client reaches the hosts its caller opens it for. `fetch_page` checks that the source is registered, not that the URL's host is the source's.
  - `LocatorKind.TEXT_SPAN`: code-point offsets into an HTML artifact's `walker-1` text or a PDF's `pdftext-1` text.
  - `cohort/pdftext.py`: pypdf's logger is held at ERROR for the call.
- `README.md`'s `docs/` row lists what `ls docs docs/adr docs/verification` holds at execution time: both source registers, the verification records by stage, ADRs 0001 to the highest, and the data dictionary. The README is the docs site's homepage, so add no GitHub alert, no Mermaid and no relative link.
- `docs/data-dictionary.md`: add the two `LiveVerification` rows.

- [ ] **Step 4: Run the tests and see them pass**

Run `test_cohort_cli.py`, `test_cohort_live.py`, `tests/contracts/test_data_dictionary.py`, then the fixture proofs. Expected: PASS. `test_cohort_fixtures.py` proves that the synthetic cohort still regenerates byte for byte and replays to its frozen manifest.

- [ ] **Step 5: Commit**

```bash
git commit -m "fix(cohort): report override, config and terms errors as problem lines, and record the operative hashes in verify-live"
```

---

### Task 3: Refuse a fund filing listed twice (L965)

**Files:**
- Modify: `sec/data.py` (`repeated_accessions`)
- Modify: `events/filings.py` (`_Reader.repeats` uses it, with its message unchanged)
- Modify: `cohort/build.py` (`_fund_filings`)
- Test: `packages/earnings-ingestion/tests/test_sec_data.py`, `test_cohort_build.py`

**Interfaces:**
- Produces: `repeated_accessions(listed: Iterable[tuple[str, Iterable[Filing]]]) -> dict[str, list[str]]`. It takes each file's URL and its filings. It returns each accession that is listed more than once, mapped to `["at <pointer('accessionNumber')> in <url>", …]` in the order read. The events reader's message is built from it, and stays `"<accession> is listed <n> times: <where, …>"`.

- [ ] **Step 1: Write the failing tests**

- `test_sec_data.py::test_repeated_accessions_names_each_copy`: two files share one accession. Assert the mapping has that accession only, with both copies in order.
- `test_cohort_build.py::test_a_fund_filing_in_its_recent_block_and_an_older_page_stops_the_build`: follow `test_a_fund_page_of_another_count_stops_the_build`. Give the synthetic fund an older page that repeats one N-PORT from its recent block, with a matching `filingCount`. Assert `pytest.raises(CohortError)`, and a problem equal to `f"{accession} is listed 2 times: at {p1} in {submissions_url}, at {p2} in {page_url}"`. The build never deduplicates the filing.

- [ ] **Step 2: Run the tests and see them fail.** Expected: `ImportError`, and no `CohortError`.

- [ ] **Step 3: Implement.** `_fund_filings` keeps each file's URL beside its filings, then appends one problem for each entry of `repeated_accessions` and returns `[]`. `_Reader.repeats` calls the helper.

- [ ] **Step 4: Run the tests and see them pass**

Run both files, `test_events_filings.py` (whose `test_a_filing_listed_in_two_files_is_a_problem` pins the unchanged events message), and the fixture proofs. Expected: PASS. DIA's saved file has no older page and no repeat, so cohort v1 does not change.

- [ ] **Step 5: Commit**

```bash
git commit -m "fix(cohort): refuse a fund filing listed twice, through the events reader's repeat check"
```

---

### Task 4: Repeated acknowledgements, repeated finding IDs, and per-issuer shared releases (L593, L818, L979)

**Files:**
- Modify: `events/records.py` (`EventOverridesFile._distinct`)
- Modify: `events/build.py` (`build_events`, `shared_releases` and its docstring)
- Modify: `specs/completed/event-discovery-eligibility-and-acquisition.md` (§Review overrides)
- Test: `packages/earnings-ingestion/tests/test_events_records.py`, `test_events_build.py`, `apps/earnings-pipeline/tests/test_events_cli.py`

**Interfaces:**
- Consumes: `EventRow.issuer_id`.
- Produces: `shared_releases(rows, sets)` keeps its signature and refuses a release only when two rows of one `issuer_id` take it.

- [ ] **Step 1: Write the failing tests**

- `test_events_records.py::test_two_acknowledgements_of_one_finding_are_refused`: two `acknowledge` overrides with distinct `override_id`s name one `finding_id`. Assert `pytest.raises(ValidationError, match="finding_id repeated among acknowledgements")`.
- `test_events_build.py`: replace `test_two_events_never_share_a_release` with `test_only_one_issuer_s_events_may_not_share_a_release`. Its rows are `SimpleNamespace(event_id=…, issuer_id=…, release_accession=…)`. Two issuers sharing `0000000001-25-000001` give `[]`. One issuer whose two events share `0000000004-25-000001` gives `["release-id/1: 0000000004-25-000001 would be the release of <e1> and <e2>"]`, with the override IDs as today when `sets` names them.
- `test_events_build.py::test_a_co_registrant_8k_is_each_issuer_s_release` (Review Focus): pick two synthetic issuers whose slots share a period end P. In the second issuer's listing, replace its release for P with the first issuer's release row (same accession, form, items and dates). Save that filing's index page and primary document under the second issuer's CIK, with the same bytes. Assert that `build_events` raises nothing, and that both events' rows carry the shared `release_accession`.
- `test_events_cli.py::test_build_refuses_a_finding_id_two_issuers_share`: list Dynamo's 8-K `0009990005-26-000018`, written `"2026-07-21T12:00:00.000Z"` as in `test_build_names_each_blocking_finding_s_own_remedy`, under a second issuer too. Save its index page under that issuer's CIK. Assert `events build` exits 1 with `SystemExit`, and a stderr line `problem: acceptance_time_mismatch:0009990005-26-000018: 2 findings share this ID, under <issuer>, <issuer>`.

- [ ] **Step 2: Run the tests and see them fail.** Expected: no refusal, a refusal where `[]` is expected, an `EventBuildError` for the shared release, and a pydantic traceback.

- [ ] **Step 3: Implement**

- `_distinct` counts `finding_id` over `acknowledge` overrides and raises `ValueError(f"finding_id repeated among acknowledgements: {sorted(repeated)}")`.
- `build_events` counts finding IDs right after the issuer loop and before its first `if problems: raise`. It appends `f"{finding_id}: {n} findings share this ID, under {', '.join(issuer_ids)}"` for each repeat. Findings are never deduplicated.
- `shared_releases` groups rows by `(issuer_id, release_accession)`. Its docstring says the refusal guards an invariant within one issuer, and that two issuers may share a co-registrant's release (D3).

- [ ] **Step 4: Amend the Stage 5 spec (§Review overrides).** Replace this bullet:

```markdown
  - No two events share a release. A filing that would be the release of two events,
    whether an override or the rule names it for each, is refused. Within one issuer
    the ranges never meet, so only a filing two issuers list, such as a
    co-registrant's 8-K, can be shared.
```

with:

```markdown
  - No two events of one issuer share a release. A filing that would be the release
    of two of one issuer's events, whether an override or the rule names it for each,
    is refused. Within one issuer the ranges never meet, so the refusal guards an
    invariant. A filing that two issuers list, such as a co-registrant's 8-K, may be
    the release of one event of each. *(owner, plan 26, 2026-11-13: the owner's
    ruling in the `/deferred` pass.)*
```

- [ ] **Step 5: Run the tests and see them pass**

Run the three test files and the fixture proofs. Expected: PASS. v1 has no shared release and no repeated finding, and `test_event_corpus_v1.py::test_the_overrides_load` loads the real overrides.

- [ ] **Step 6: Commit**

```bash
git commit -m "fix(events): refuse repeated acknowledgements and finding IDs, and let two issuers share a co-registrant release (D3)"
```

---

### Task 5: Acceptance time under reading (a), and its two bounds (L541)

**Files:**
- Modify: `events/acceptance.py` (`survey`)
- Modify: `events/filings.py` (`FILING_DATE_SLACK`, `issuer_filings`, the module docstring)
- Modify: `events/evidence.py` (`_row`, `_event`)
- Modify: `docs/data-dictionary.md` (`acceptance_time_unknown`, `acceptance_time_mismatch`, `rows_cross_checked`, `EventCitations.cross_check`)
- Modify: the Stage 5 spec, §Acceptance time (EV10)
- Test: `packages/earnings-ingestion/tests/test_events_filings.py`, `test_events_freeze.py`, `apps/earnings-pipeline/tests/test_events_cli.py`

**Interfaces:**
- Produces: `FILING_DATE_SLACK: timedelta = timedelta(days=7)` in `events/filings.py`, which Task 6 uses.

- [ ] **Step 1: Write the failing tests**

- `test_events_filings.py::test_a_missing_value_is_unknown_unless_filed_before_the_range`: keep its assertions. Then save the index page of `report` and of `unplaced` (`saved.index(...)`), read again, and assert:

```python
assert read.findings == ()
assert report.accession in [p.filing.accession for p in read.periodic]
assert unplaced.accession in [p.filing.accession for p in read.releases]
```

- `test_events_filings.py::test_an_old_periodic_report_with_no_value_raises_nothing`: reports for 2023-12-31 (`written=""`) and 2024-03-31 (with a value), and one in-window report. Assert `read.findings == ()`. Assert that `read.periodic` holds the same accessions as a store without the 2023-12-31 report.
- `test_events_filings.py::test_the_latest_report_before_the_window_with_no_value_still_blocks`: the 2024-03-31 report with `written=""`. Assert one `acceptance_time_unknown` finding for it. The slots' guards pair it with the first in-window report.
- `test_events_filings.py::test_a_no_value_release_past_the_cutoff_margin_raises_nothing`: an Item 2.02 8-K with `written=""` and `filing_date=date(2026, 9, 30)` (the cutoff plus 8 days) gives no finding. One filed on `date(2026, 9, 29)` gives `acceptance_time_unknown`.
- `test_events_cli.py::test_build_names_each_blocking_finding_s_own_remedy`: keep the no-value unknown and its hint line, which pins the wording for a row with no value. Add an unknown whose value falls on either side of the cutoff, in a file that establishes no convention. In setup, assert that its `FileSurvey.convention is None`. Assert the same hint form for it.
- `test_events_cli.py::test_an_emptied_10q_with_its_index_page_saved_still_freezes` (Review Focus): empty Dynamo's 10-Q `0009990005-26-000017`, and save its index page with `events.synthetic.index_page`. Assert that `events build` exits 0 with the last line `f"32 events, 27 eligible, content {EVENTS_HASH}"`, and that `events freeze` exits 0 with `unchanged: djia-synthetic v1`.
- `test_events_freeze.py::test_a_row_with_no_value_is_cited_without_one`: over a build whose slot's periodic report has no value and a saved index page, assert that `evidence_of(...)`'s `periodic_row` has no locator at `acceptanceDateTime`, and that `check_evidence(...) == ()`. For a release with no value, assert `cross_check is None`.

- [ ] **Step 2: Run the tests and see them fail.** Expected: a mismatch finding where reading (a) expects none, an unknown for the old report and the late 8-K, and a freeze that holds.

- [ ] **Step 3: Implement**

- `survey` cross-checks only rows with a value (`filing.accepted_at is not None`). So a row with no value is never a mismatch, and `rows_cross_checked` leaves it out.
- `issuer_filings`:
  - Compute `floor`, the latest `report_date` before `start` among the file's original periodic reports. When `_visible` returns `None` for a report whose `report_date < floor`, skip it with no finding. Visible reports keep today's handling.
  - Raise the no-value 8-K unknown only when `start <= filing.filing_date <= cutoff + FILING_DATE_SLACK`. A filing accepted after 17:30 takes the next business day's filing date, so its filing date can fall after its acceptance date.
- `_event` and `_row` leave the `acceptanceDateTime` column out of `periodic_row` when the row has no value, and set `cross_check` to `None` for a release with no value.
- In the `events/filings.py` module docstring, add one sentence for each change.
- In `docs/data-dictionary.md`:
  - The `acceptance_time_unknown` row adds the two bounds.
  - The `acceptance_time_mismatch` row says "with a value".
  - The `rows_cross_checked` row says "with a value and a saved index page".
  - The `cross_check` row says null "when the row has no value".

- [ ] **Step 4: Amend the Stage 5 spec (§Acceptance time (EV10)).** After the sub-bullet that ends "The reader never infers a file's convention from its dates.", insert:

```markdown
  - A row with no value has nothing to cross-check. When the filing's index page is
    saved, the page's Accepted value places the filing, and its cross-check is null:
    no finding, and the evidence record cites no `acceptanceDateTime`. Without the
    page, the row is `acceptance_time_unknown` until `events discover --filing`
    saves it (P7-8). An original periodic report older than the issuer's latest
    report before the window raises no `acceptance_time_unknown`, since no slot or
    guard reads it. An Item 2.02 8-K with no value raises one only when it is filed
    from the window's start to seven days after the cutoff. *(owner, plan 26,
    2026-11-13: reading (a), the owner's ruling in the `/deferred` pass.)*
```

- [ ] **Step 5: Run the tests and see them pass**

Run the three test files, `test_events_acceptance.py`, `tests/contracts/test_data_dictionary.py` and the fixture proofs. Expected: PASS. PR #6 found that none of the 112,236 rows the v1 build reads has an empty value, so v1 does not change (Task 10 rebuilds it).

- [ ] **Step 6: Commit**

```bash
git commit -m "fix(events): a missing acceptanceDateTime has nothing to cross-check (D2), and bound the reports and 8-Ks that can block on it"
```

---

### Task 6: Bind older pages to their dates, and pad the page skip (L705)

**Files:**
- Modify: `events/filings.py` (`_Reader.files`, the module docstring)
- Modify: `docs/data-dictionary.md` (`### SkippedPage`)
- Modify: the Stage 5 spec, §Store, client, and readers, "Older pages"
- Test: `packages/earnings-ingestion/tests/test_events_filings.py`

**Interfaces:**
- Consumes: `FILING_DATE_SLACK` (Task 5).

- [ ] **Step 1: Write the failing tests** (`Saved.submissions(..., pages=...)` builds older pages)

- `test_an_older_page_that_starts_after_the_cutoff_is_read` (Review Focus): an older page whose only filing is an Item 2.02 8-K, accepted `"2026-09-22 18:00:00"` ET with `filing_date=date(2026, 9, 23)`. Its entry's `filingFrom` and `filingTo` are 2026-09-23. Assert the page is not in `read.skipped`, and the filing is among `read.releases` once its index page is saved.
- `test_the_padded_skip_reads_a_page_ending_seven_days_before_the_start`: a page with `filingTo` = `start - 7 days` is read. One with `filingTo` = `start - 8 days` is in `read.skipped`.
- `test_an_older_page_with_shifted_dates_is_refused`: the right `filingCount`, but one filing date on or after the next newer page's `filingFrom`. Assert a problem that names the page, and that ends with the remedy `_Reader.repeats` gives: the submissions file with its older pages. Do the same for the newest older page against the recent block's earliest filing date.

- [ ] **Step 2: Run the tests and see them fail.** Expected: the first page is skipped, the second is read, and the shifted page passes.

- [ ] **Step 3: Implement**

- Skip a dated page when `page.filing_to < start - FILING_DATE_SLACK` or `page.filing_from > cutoff + FILING_DATE_SLACK`.
- After the pages are read, order the dated pages by `filing_from`. For each read page, the bound is the next newer page's `filing_from`. For the newest older page, it is the recent block's earliest `filing_date`. Refuse a page whose latest `filing_date` is not before its bound, through `self.refuse(main.url, …, "the submissions file with its older pages")`. Do not require the latest date to lie within a day of `filingTo`, since a long weekend breaks that.
- In `docs/data-dictionary.md`, the `filing_from` row says "SEC's `filingFrom`". The `filing_to` row says "SEC's `filingTo`. It can differ by a day from the page's last filing date. A page is skipped when this is more than seven days before 2024-07-01, or when `filing_from` is more than seven days after 2026-09-22."

- [ ] **Step 4: Amend the Stage 5 spec.** Replace:

```markdown
- **Older pages.** An older page is read when its own `filingFrom`–`filingTo` range
  meets `[2024-07-01, 2026-09-22]`. Otherwise it is skipped by those dates, and the
  skip is recorded (R1.1).
```

with:

```markdown
- **Older pages.** An older page is read unless its `filingTo` is more than seven days
  before 2024-07-01, or its `filingFrom` is more than seven days after 2026-09-22.
  These are filing dates. A filing accepted after 17:30 takes the next business
  day's filing date, so the margin keeps a page that holds a filing accepted inside
  the range. A skipped page is recorded (R1.1). A page that is read must hold only
  filing dates before the next newer page's `filingFrom`, or before the recent
  block's earliest filing date for the newest page. Otherwise it is refused, as a
  page that SEC cut again. *(owner, plan 26, 2026-11-13.)*
```

- [ ] **Step 5: Run the tests and see them pass**

Run `test_events_filings.py`, `tests/contracts/test_data_dictionary.py` and the fixture proofs. Expected: PASS. If a fixture's own page fails the strict "before" check, stop and report it. Do not loosen the check. The synthetic skipped page ends on 2024-05-03, and the latest skipped page of v1 ends on 2024-06-23, so neither skip set changes. Task 10 checks v1's 19 read pages.

- [ ] **Step 6: Commit**

```bash
git commit -m "fix(events): pad the older-page skip by seven days and refuse a page whose dates shifted"
```

---

### Task 7: Bind the evidence record to the store and to the manifest (L670)

**Files:**
- Modify: `events/evidence.py` (`check_evidence`)
- Modify: `events/freeze.py` (`load_event_evidence`)
- Test: `packages/earnings-ingestion/tests/test_events_freeze.py`, `test_events_discover.py`

- [ ] **Step 1: Write the failing tests**

- `test_events_freeze.py::test_loading_evidence_refuses_a_release_citation_of_another_filing`: re-point one event's `release` citation URL to another filing's index page. Assert `pytest.raises(ValueError, match=<event_id>)`. A row with no `release_accession` must have `release is None`.
- `test_events_discover.py::test_check_evidence_refuses_a_citation_no_retrieval_supports`, parametrized: a citation URL that is not among its artifact's retrievals' `request_url`s, a `source_id` other than `sec-edgar`, a `retrieved_at` that matches no retrieval, a `files[]` URL that is not among its retrievals, and a `files[]` `retrieved_at` that matches none. For each, assert one problem that names the event (or the file) and the field.

- [ ] **Step 2: Run the tests and see them fail.** Expected: no refusal.

- [ ] **Step 3: Implement**

- `load_event_evidence`: for each row, the `release` citation's URL equals `filing_index_url(row.cik, row.release_accession)`, or both are absent. The committed v1 records pass: all 263 real and 31 synthetic release citations match (checked at `b27794a`).
- `check_evidence` reads `stored.retrievals` from the `store.get` it already does, and checks each citation's `source_id`, `url` and `retrieved_at`, and each file's `url` and `retrieved_at`, against them.

- [ ] **Step 4: Run the tests and see them pass**

Run both files and the fixture proofs. Expected: PASS. `test_event_fixtures.py::test_every_citation_verifies_against_the_committed_store` proves the synthetic record, and `test_event_corpus_v1.py` loads the real one.

- [ ] **Step 5: Commit**

```bash
git commit -m "fix(events): bind each evidence citation to its artifact's retrievals and each release citation to its row"
```

---

### Task 8: Events commands end every load failure with a named line (L465)

**Files:**
- Modify: `fetch/store.py` (`RetrievalRecordError`, `read_retrieval`, `ArtifactStore.retrievals`, `ArtifactStore.latest`)
- Modify: `events/saved.py` (`SavedResponses.__init__`)
- Modify: `events/freeze.py` (`LeftoverEvidence`, `freeze_events`)
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/events_cli.py` (`Layout.universes`, `_build`, `_counted`, `freeze_command`, `select_command`)
- Modify: `docs/verification/djia-events.md` ("Repairing the store": one sentence on the new line)
- Test: `packages/earnings-ingestion/tests/test_fetch_store.py`, `test_events_freeze.py`, `apps/earnings-pipeline/tests/test_events_cli.py`

**Interfaces:**
- Produces:
  - `class RetrievalRecordError(ValueError)` with `.path: Path`. Its message is `f"{path}: unreadable retrieval record; repair it by hand (docs/verification/djia-events.md, \"Repairing the store\")"`.
  - `read_retrieval(path: Path) -> Retrieval`, which raises it for any `ValueError` the read or the validation raises. `UnicodeDecodeError` and pydantic's `ValidationError` are both `ValueError`s.
  - `class LeftoverEvidence(ValueError)` with `.path: Path`.

  Both error classes subclass `ValueError`, so every existing `except ValueError` still catches them.

- [ ] **Step 1: Write the failing tests**

- `test_fetch_store.py::test_an_unreadable_retrieval_record_is_named`: write `b""` over one record. Assert that `retrievals`, `latest` and `SavedResponses(store)` each raise `RetrievalRecordError` with `.path` equal to that record.
- `test_events_freeze.py::test_a_leftover_evidence_file_with_other_bytes_is_refused`: following `test_a_changed_fact_writes_the_next_version`, write other bytes to `events-v2.evidence.json` first. Assert `pytest.raises(LeftoverEvidence, match="delete it")`, and that no `events-v2.json` exists. In `…_with_the_same_bytes_completes`, write the bytes a first freeze into another directory produced. Assert that the freeze completes.
- `test_events_cli.py`, parametrized over three edits of `overrides.toml` and the commands `build` and `freeze`:
  - a repeated `override_id`
  - a second override of one kind for one `event_id`
  - a TOML syntax error

  Assert exit 1, `SystemExit`, and a stderr line that starts with `problem: tests/fixtures/events/overrides.toml: `.
- `test_events_cli.py::test_build_refuses_a_tampered_universe_manifest`: change one fact in the copy's universe manifest. Assert exit 1, `SystemExit`, and stderr that starts with `Refused: <that path>: `. Assert the same for `discover`, with the fake client, before any client opens (`budgets == []`).
- `test_events_cli.py::test_an_empty_retrieval_record_is_named` (Review Focus): in the `moved` store, write `b""` over one record under `sec-edgar/retrievals/`. Assert that `events build` exits 1 with `problem: data/raw/events/sec-edgar/retrievals/<…>.json: unreadable retrieval record; …`. With the fake client (`client(monkeypatch, served())`), assert that `events discover --max-requests 5` ends with `requests sent: 0` and `Stopped: …unreadable retrieval record…`, and that no line says "a rerun fetches only what is missing".
- `test_events_cli.py::test_freeze_reports_a_citation_error_as_a_problem`: monkeypatch `events_cli.freeze_events` to raise `LocatorError("… not in the walker-1 text")`. Assert exit 1, `SystemExit`, and `problem: … not in the walker-1 text`.
- `test_events_cli.py::test_freeze_reports_a_leftover_evidence_file_as_a_refusal`: monkeypatch it to raise `LeftoverEvidence`. Assert `Refused: …delete it…`.
- `test_events_cli.py::test_select_says_to_rerun_when_another_select_froze_first`: monkeypatch `events_cli.freeze_pilot` to raise `FileExistsError("… holds other bytes")`. Assert exit 1, `SystemExit`, and stderr that ends with `rerun events select\n`.

- [ ] **Step 2: Run the tests and see them fail.** Expected: tracebacks, and a `FileExistsError` that names no cause.

- [ ] **Step 3: Implement the store and the readers.** `retrievals`, `latest` and `SavedResponses.__init__` read each record through `read_retrieval`.

- [ ] **Step 4: Implement the freeze.** Before its first write, `freeze_events` checks whether `evidence_path` exists without `manifest_path` and holds other bytes than the new evidence. If so, it raises `LeftoverEvidence(f"{path} exists without {manifest name} and holds other bytes: delete it, then freeze again")`. It never overwrites the file.

- [ ] **Step 5: Implement the CLI**

- `Layout.universes()` wraps each `load_manifest(path)` in `except (OSError, ValueError)` → `_fail(f"Refused: {shown(path, self.repo)}: {error}")`.
- `_build` builds `SavedResponses` inside `except RetrievalRecordError` → `problem: {shown(error.path, repo)}: unreadable retrieval record; …`. It wraps only the `load_overrides(path)` call in `except (OSError, ValueError)` → `problem: {shown(path, repo)}: {error}`. Do not widen the handler around `build_events`: `EventBuildError` and `LocatorError` are `ValueError`s too.
- `_counted` catches `RetrievalRecordError` before `STOPS`. It prints `requests sent: {sent}` with no rerun clause, then `Stopped: {error}`.
- `freeze_command`: `EventFreezeRefused` → `HOLDS` lines (unchanged). Then `LocatorError` → `problem: {error}`. Then `(OSError, ValueError)` → `Refused: {error}`.
- `select_command` adds `except FileExistsError as error:` → `_fail(f"Refused: {error}; another events select froze this pilot first: rerun events select")`.
- In `docs/verification/djia-events.md`, "Repairing the store", add one sentence: an unreadable retrieval record now names its path, and the repair stays manual.

- [ ] **Step 6: Run the tests and see them pass**

Run the three test files, `test_events_cli_corpus.py` (its pinned `Refused:` stays) and the fixture proofs. Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git commit -m "fix(events): end override, universe, retrieval-record, freeze and select failures with a named line"
```

---

### Task 9: Discovery reads companyfacts in a guard, and every save reports what it moved aside (L861, L1792)

**Files:**
- Modify: `events/saved.py` (`issuer_companyfacts`)
- Modify: `events/build.py` (`_companyfacts` is replaced by it), `events/discover.py` (the documents phase and `read_back`, and the module docstring's sentence on item P2.3)
- Modify: `apps/earnings-pipeline/src/earnings_pipeline/paths.py` (`quarantined_lines`)
- Modify: `apps/…/events_cli.py` (`_discover`, `_counted`, `acquire_command`), `apps/…/cohort_cli.py` (`fetch_sec_command`)
- Test: `packages/earnings-ingestion/tests/test_events_discover.py`, `apps/earnings-pipeline/tests/test_events_cli.py`, `test_cohort_cli.py`

**Interfaces:**
- Produces:
  - `issuer_companyfacts(saved: SavedResponses, cik: str) -> CompanyFacts | str | None`. It returns `None` when nothing is saved. It returns a problem line when the file cannot be read or states another CIK. The line is `f"{url}: {exc}; {refetch_remedy(url)}"` or `f"{url} is the companyfacts file of CIK {facts.cik}; {refetch_remedy(url)}"`, the build's text today. Otherwise it returns the facts.
  - `quarantined_lines(store: ArtifactStore, repo: Path) -> list[str]`: one `quarantined: <shown path>` for each distinct path in `store.quarantined`, in order. `events_cli._quarantined` becomes a call to it.
  - `_counted(budget, run, *, rerun=…, before_count: Callable[[], None] = lambda: None)`. `before_count` runs before the `requests sent` line on every early exit.

- [ ] **Step 1: Write the failing tests**

- `test_events_discover.py::test_a_truncated_companyfacts_file_skips_only_its_issuer`: truncate one synthetic issuer's companyfacts artifact. Delete the retrieval records of another issuer's candidate primary document. Run `discover` with a fake fetch. Assert that the fetched URLs include that primary document, and that one problem starts with the truncated file's URL and ends with `refetch_remedy(url)`.
- `test_events_cli.py::test_discover_handles_a_vanished_companyfacts_artifact`: delete one companyfacts artifact file and keep its record. Assert that `events discover --max-requests 5` exits 1 with `SystemExit`, prints `fetched N; requests sent: M`, and prints a `problem:` line that names the URL.
- `test_events_cli.py::test_discover_prints_each_quarantined_file_once` (Review Focus), parametrized over plain `discover` and `discover --filing CIK ACC`: `truncate(repo, INDEX)`, then `unsave` that filing, so the save needs the damaged artifact's name. Serve the original bytes. Assert that the `quarantined:` line `truncate` returned appears exactly once. In a stopped variant, the fake fetch raises `AccessStop` after that save. Assert that the line comes before `requests sent:`.
- `test_cohort_cli.py::test_fetch_sec_prints_each_quarantined_file_once`: damage one saved SEC artifact of the synthetic cohort, delete its retrieval records, and serve its original bytes through the fake SEC client. Assert one `quarantined: ` line.

- [ ] **Step 2: Run the tests and see them fail.** Expected: the documents phase stops on the truncated file, a traceback for the vanished one, and no `quarantined:` line.

- [ ] **Step 3: Implement**

- `build_events` and `read_back` call `issuer_companyfacts`. `None` in the build still appends `nothing saved from <url>: run events discover`.
- `discover`'s documents phase calls it and skips the issuer unless it returns facts. It records no problem there, because `read_back` reports the same file after the phase.
- `_discover` builds one `store`, passes it to `discover` and `discover_filing`, passes `_counted` a `before_count` that echoes each of `quarantined_lines(store, layout.repo)`, and echoes the same lines after its `fetched` line.
- `fetch_sec_command` builds one `store` and prints the lines after its counts. A stop prints them before `requests sent`.

- [ ] **Step 4: Run the tests and see them pass**

Run the three test files and the fixture proofs. Expected: PASS. The plan 25 tests of `acquire`'s quarantine lines still pass, through the shared helper.

- [ ] **Step 5: Commit**

```bash
git commit -m "fix(events): read companyfacts in a guard in discovery, and print quarantined files after every save"
```

---

### Task 10: Real-store checks and the owner's gates

**Files:**
- Modify: `tests/integration/test_event_store_v1.py`
- Create: `tests/integration/test_cohort_store_v1.py`

**Interfaces:**
- Consumes: `CohortBuild.operative_hash` (Task 2), `check_evidence` (Task 7), `build_events` and `load_overrides`.

- [ ] **Step 1: Write the real-store tests.** Each test skips when its store is absent, as the existing tests in `test_event_store_v1.py` do. Failure output holds hashes and counts only.
  - `test_events_v1_rebuilds_from_the_saved_store`: `build_events` over `data/raw/events` with the committed overrides and universe v1. Assert `content_hash` equals `events-v1.json`'s, and nothing holds the freeze.
  - `test_every_v1_citation_verifies_against_the_saved_store`: `check_evidence(load_event_evidence(...), ArtifactStore(STORE, REPO)) == ()`.
  - `test_cohort_v1_rebuilds_to_its_operative_hash` (new file): `build(REPO).operative_hash == operative_hash(<the latest frozen manifest>)`, with no blocking finding. The content hash is not compared. Plan 7 Task 16 changed the register, so the content hash no longer reproduces (L391).

- [ ] **Step 2: Agents' check.** Run every test file named in Tasks 1–9, the fixture proofs, and Ruff. Expected: PASS and clean. In a worktree, the Step 1 tests skip and prove nothing.

- [ ] **Step 3: Owner gate: the real stores.** Run this from the main checkout, which holds `data/raw/`, at the branch's head:

```bash
uv run --locked --all-packages pytest tests/integration/test_event_store_v1.py tests/integration/test_cohort_store_v1.py tests/integration/test_event_corpus_v1.py -m "not live and not browser" -rs
```

Expected: the three new tests pass, and none of them skips. If `test_events_v1_rebuilds_from_the_saved_store` fails, stop and report the problem lines. A page that Task 6 refuses, or a hash that moved, is a finding for the owner. Never re-freeze to make the test pass.

- [ ] **Step 4: Owner gate: the root suite.** Run the root command from `CLAUDE.md` ("Commands"). Expected: no failures. Record the counts against the suite baseline.

---

## Self-review notes

- Coverage: each of the 15 items maps to a task (see the Coverage table). L465's third bullet is covered as naming only (owner's review, item 1).
- Types: `FILING_DATE_SLACK` (Task 5) is used in Task 6. `CohortBuild.operative_hash` (Task 2) is used in Task 10. `RetrievalRecordError` (Task 8) is caught by `_counted` and `_build`, which Task 9 extends. `quarantined_lines` (Task 9) replaces the body of `_quarantined`.
- Order: Tasks 8 and 9 both edit `_counted`. Task 9 runs after Task 8 and keeps Task 8's `RetrievalRecordError` branch.
