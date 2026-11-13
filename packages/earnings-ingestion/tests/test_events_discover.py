"""Discovery (the Stage 5 spec, §Store, client, and readers; SV5; EV2).

Every test runs the shared SEC client over a recording transport that serves the
committed synthetic event layer, so no request leaves the process. Discovery must
request exactly the responses the build reads, each once, and never an exhibit.
"""

import re
import shutil
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import httpx
import pytest
from earnings_core import sha256_hex
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.build import (
    EventBuildError,
    _named_filing,
    build_events,
    citations_refused,
    load_overrides,
)
from earnings_ingestion.events.discover import discover, discover_filing
from earnings_ingestion.events.evidence import check_evidence
from earnings_ingestion.events.filings import issuer_filings
from earnings_ingestion.events.fixture import (
    COHORT_MANIFEST,
    FIXTURE_DIR,
    SYNTHETIC_CORPUS,
)
from earnings_ingestion.events.freeze import load_event_evidence, load_event_manifest
from earnings_ingestion.events.layer import (
    ACME,
    BOREALIS,
    CORVID,
    DYNAMO,
    EASTFIELD,
    OLDER_PAGES,
    RETRIEVED,
    Registrant,
    Release,
    exhibit_bodies,
    filings,
)
from earnings_ingestion.events.release import identify
from earnings_ingestion.events.saved import (
    SavedResponses,
    cited_remedy,
    refetch_remedy,
)
from earnings_ingestion.events.slots import issuer_slots
from earnings_ingestion.events.synthetic import (
    HTML,
    JSON,
    SyntheticFiling,
    eight_k,
    index_page,
    older_page_entry,
    retrieval_of,
    save,
    submissions_file,
)
from earnings_ingestion.fetch.client import UnexpectedResponse
from earnings_ingestion.fetch.records import Retrieval
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.client import open_sec_client
from earnings_ingestion.sec.companyfacts import read_companyfacts
from earnings_ingestion.sec.filing_index import read_filing_index
from earnings_ingestion.sec.urls import (
    archive_url,
    companyfacts_url,
    filing_index_url,
    submissions_page_url,
    submissions_url,
)

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / FIXTURE_DIR / "raw"
IDENTITY = {"EDGAR_IDENTITY": "Plan 7 synthetic discovery test@example.com"}
EVENTS_PACKAGE = REPO / "packages/earnings-ingestion/src/earnings_ingestion/events"


def served(root: Path, repo: Path) -> dict[str, tuple[bytes, str]]:
    """Every response saved under ``root``, by URL, but the exhibits acquisition
    saved (plan 8): discovery fetches the rest."""
    store = ArtifactStore(root, repo)
    found = {}
    exhibits = exhibit_bodies()
    for path in sorted((root / SEC_SOURCE_ID / "retrievals").glob("*/*.json")):
        record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
        if record.request_url in exhibits:
            continue
        stored = store.get(
            SEC_SOURCE_ID,
            record.sha256,
            rights_status=SEC_RIGHTS.rights_status,
            rights_basis=SEC_RIGHTS.rights_basis,
        )
        found[record.request_url] = (stored.body, record.media_type)
    return found


class Recorder:
    """A transport serving ``responses``, which records every request it sees."""

    def __init__(self, responses: dict[str, tuple[bytes, str]]) -> None:
        self.responses = dict(responses)
        self.requested: list[str] = []

    def transport(self) -> httpx.MockTransport:
        def handle(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            self.requested.append(url)
            if url not in self.responses:
                return httpx.Response(404, text="Not Found")
            body, media_type = self.responses[url]
            return httpx.Response(
                200, content=body, headers={"content-type": media_type}
            )

        return httpx.MockTransport(handle)


@pytest.fixture(scope="module")
def universe():
    return load_manifest(REPO / COHORT_MANIFEST)


@pytest.fixture(scope="module")
def layer() -> dict[str, tuple[bytes, str]]:
    return served(RAW, REPO)


def run(universe, recorder: Recorder, store: ArtifactStore, *, filing=None):
    lines: list[str] = []
    with open_sec_client(
        environ=IDENTITY,
        transport=recorder.transport(),
        sleep=lambda seconds: None,
        max_requests=200,
    ) as sec:
        if filing is None:
            result = discover(universe, sec.fetch, store, say=lines.append)
        else:
            result = discover_filing(universe, *filing, sec.fetch, store)
        sent = sec.throttle.count
    return result, sent, lines


def test_discovery_requests_what_the_build_reads_and_never_an_exhibit(
    universe, layer, tmp_path
) -> None:
    recorder = Recorder(layer)
    store = ArtifactStore(tmp_path / "data" / "raw" / "events", tmp_path)
    result, sent, lines = run(universe, recorder, store)
    assert sorted(recorder.requested) == sorted(layer)
    assert len(recorder.requested) == len(set(recorder.requested)) == sent == 84
    assert result.fetched == recorder.requested
    assert lines == [
        "submissions and companyfacts: 10 to fetch",
        "older pages and index pages: 38 to fetch",
        "older pages and index pages: 2 to fetch",
        "older pages and index pages: 0 to fetch",
        "primary documents: 34 to fetch",
    ]
    pages = [
        read_filing_index(body)
        for url, (body, _) in layer.items()
        if url.endswith("-index.htm")
    ]
    exhibits = {
        document.filename
        for page in pages
        for document in page.documents
        if document.doc_type.startswith("EX-")
    }
    assert exhibits
    assert not [url for url in recorder.requested if url.rsplit("/", 1)[1] in exhibits]
    built = build_events(
        universe,
        SavedResponses(store),
        load_overrides(REPO / FIXTURE_DIR / "overrides.toml"),
        corpus_id=SYNTHETIC_CORPUS,
    )
    committed = load_event_manifest(REPO / FIXTURE_DIR / "events-v1.json")
    assert built.content_hash == committed.definition.content_hash


def test_a_stopped_run_resumes_and_fetches_only_what_the_store_lacks(
    universe, layer, tmp_path
) -> None:
    gone = sorted(url for url in layer if url.endswith("-index.htm"))[3]
    partial = Recorder({url: r for url, r in layer.items() if url != gone})
    store = ArtifactStore(tmp_path / "data" / "raw" / "events", tmp_path)
    with pytest.raises(UnexpectedResponse, match="404"):
        run(universe, partial, store)
    first = [url for url in partial.requested if url != gone]
    recorder = Recorder(layer)
    result, sent, _ = run(universe, recorder, store)
    assert sorted(recorder.requested) == sorted(set(layer) - set(first))
    assert gone in recorder.requested and sent == len(recorder.requested)
    again = Recorder(layer)
    result, sent, _ = run(universe, again, store)
    assert (again.requested, sent, result.fetched) == ([], 0, [])


def test_discovery_names_each_saved_response_the_build_cannot_read(
    universe, layer, tmp_path
) -> None:
    """A saved response the build cannot read is never fetched again, because it is
    saved, so discovery names it rather than finish as though nothing were wrong. One
    issuer loses its submissions file's bytes; another keeps its registrant, but an
    index page of its, saved again, states no Accepted value; a third loses a
    candidate's primary document."""
    store = ArtifactStore(tmp_path / "data" / "raw" / "events", tmp_path)
    run(universe, Recorder(layer), store)
    borealis, corvid = (f"/edgar/data/{int(r.cik)}/" for r in (BOREALIS, CORVID))
    index = min(url for url in layer if borealis in url and url.endswith("-index.htm"))
    document = min(
        url for url in layer if corvid in url and not url.endswith("-index.htm")
    )
    submissions = submissions_url(ACME.cik)
    saved = SavedResponses(store)
    gone = {}
    for url in (submissions, document):
        artifact = saved.get(url).artifact
        (tmp_path / artifact.storage_ref).unlink()
        gone[url] = artifact.content_sha256
    unlabeled = layer[index][0].replace(b">Accepted<", b">Received<")
    assert unlabeled != layer[index][0]
    later = saved.get(index).retrieved_at + timedelta(seconds=1)
    save(store, index, unlabeled, "text/html", later)
    recorder = Recorder(layer)
    result, sent, _ = run(universe, recorder, store)
    assert (recorder.requested, sent, result.fetched) == ([], 0, [])
    no_bytes = "for source 'sec-edgar': its retrieval records remain, but its bytes"
    assert result.problems == [
        (
            f"{submissions}: no artifact {gone[submissions]} {no_bytes} are gone;"
            f" {refetch_remedy(submissions)}"
        ),
        f"{index}: the index page states no Accepted; {refetch_remedy(index)}",
        (
            f"{document}: no artifact {gone[document]} {no_bytes} are gone;"
            f" {refetch_remedy(document)}"
        ),
    ]


def test_discover_filing_saves_one_filing_and_an_8ks_document(
    universe, layer, tmp_path
) -> None:
    """Dynamo's Item 7.01 8-K was never read; its index page and document are
    served, and discovery saves them on request."""
    (filing,) = [
        filing
        for filing, entry in filings(DYNAMO)
        if isinstance(entry, Release) and "7.01" in entry.items
    ]
    index = filing_index_url(DYNAMO.cik, filing.accession)
    document = archive_url(DYNAMO.cik, filing.accession, filing.primary_document)
    responses = dict(layer)
    responses[index] = (index_page(DYNAMO.cik, filing), "text/html")
    responses[document] = (
        eight_k(DYNAMO.name, [("7.01", ("An invented investor presentation.",))]),
        "text/html",
    )
    root = Path(shutil.copytree(RAW, tmp_path / "data" / "raw" / "events"))
    store = ArtifactStore(root, tmp_path)
    recorder = Recorder(responses)
    run(universe, recorder, store, filing=(DYNAMO.cik, filing.accession))
    assert recorder.requested == [index, document]
    (report, _) = next((f, e) for f, e in filings(DYNAMO) if f.form == "10-Q")
    responses[filing_index_url(DYNAMO.cik, report.accession)] = (
        index_page(DYNAMO.cik, report),
        "text/html",
    )
    recorder = Recorder(responses)
    run(universe, recorder, store, filing=(DYNAMO.cik, report.accession))
    assert recorder.requested == [filing_index_url(DYNAMO.cik, report.accession)]
    with pytest.raises(ValueError, match="list no 0009990005-99-000001"):
        run(universe, recorder, store, filing=(DYNAMO.cik, "0009990005-99-000001"))
    with pytest.raises(ValueError, match="has CIK 0009990004"):
        run(universe, recorder, store, filing=("0009990004", filing.accession))


def test_discover_filing_checks_the_index_page_before_it_fetches_the_document(
    universe, layer, tmp_path
) -> None:
    """An index page that disagrees with its submissions row stops ``--filing``
    before the primary document is fetched (PR #6's review, F12)."""
    (filing,) = [
        filing
        for filing, entry in filings(DYNAMO)
        if isinstance(entry, Release) and "7.01" in entry.items
    ]
    index = filing_index_url(DYNAMO.cik, filing.accession)
    responses = dict(layer)
    responses[index] = (
        index_page(DYNAMO.cik, replace(filing, form="8-K/A")),
        "text/html",
    )
    root = Path(shutil.copytree(RAW, tmp_path / "data" / "raw" / "events"))
    recorder = Recorder(responses)
    result, _, _ = run(
        universe,
        recorder,
        ArtifactStore(root, tmp_path),
        filing=(DYNAMO.cik, filing.accession),
    )
    assert recorder.requested == [index]
    assert result.problems == [
        f"{index}: its form is 8-K/A, but its row's is 8-K; {refetch_remedy(index)}"
    ]


def test_issuer_filings_lists_what_the_build_reads_and_lacks(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "data" / "raw" / "events", tmp_path)
    empty = issuer_filings(
        SavedResponses(store),
        DYNAMO.cik,
        "cik-0009990005",
        start=load_manifest(REPO / COHORT_MANIFEST).definition.period_end_start,
        cutoff=load_manifest(
            REPO / COHORT_MANIFEST
        ).definition.public_information_cutoff,
    )
    assert empty.missing == (submissions_url(DYNAMO.cik),)
    full = issuer_filings(
        SavedResponses(ArtifactStore(RAW, REPO)),
        DYNAMO.cik,
        "cik-0009990005",
        start=load_manifest(REPO / COHORT_MANIFEST).definition.period_end_start,
        cutoff=load_manifest(
            REPO / COHORT_MANIFEST
        ).definition.public_information_cutoff,
    )
    assert (full.missing, full.problems) == ((), ())


ACME_RELEASE = "0009990001-25-000008"
"""Acme's release of 2025-03-20, whose index page an override of the corpus cites."""
EASTFIELD_PAGE = submissions_page_url(OLDER_PAGES[EASTFIELD][0][0])
"""Eastfield's older page whose dates meet the range, so the build reads it."""


def populated(universe, layer, repo: Path) -> ArtifactStore:
    """A store under ``repo`` that discovery filled from the synthetic layer."""
    store = ArtifactStore(repo / "data" / "raw" / "events", repo)
    run(universe, Recorder(layer), store)
    return store


def stored_at(store: ArtifactStore, url: str) -> Path:
    """The file that holds the newest response saved from ``url``."""
    return store.repo / SavedResponses(store).get(url).artifact.storage_ref


def resave(store: ArtifactStore, url: str, body: bytes, media_type: str) -> None:
    """Save ``body`` as a newer retrieval of ``url``, which the readers then read."""
    later = SavedResponses(store).get(url).retrieved_at + timedelta(seconds=1)
    save(store, url, body, media_type, later)


def read_issuer(universe, store: ArtifactStore, registrant: Registrant):
    definition = universe.definition
    return issuer_filings(
        SavedResponses(store),
        registrant.cik,
        f"cik-{registrant.cik}",
        start=definition.period_end_start,
        cutoff=definition.public_information_cutoff,
    )


def acme_filing(accepted: str) -> SyntheticFiling:
    ((filing, _),) = [(f, e) for f, e in filings(ACME) if f.accepted == accepted]
    return filing


def bytes_gone(store, layer):
    url = submissions_url(ACME.cik)
    stored_at(store, url).unlink()
    return ACME, url, refetch_remedy(url)


def bytes_changed(store, layer):
    url = filing_index_url(ACME.cik, ACME_RELEASE)
    stored_at(store, url).write_bytes(b"<html><body>damaged</body></html>")
    return ACME, url, refetch_remedy(url)


def redirected_record(store, layer):
    url = EASTFIELD_PAGE
    saved = SavedResponses(store).get(url)
    later = saved.retrieved_at + timedelta(seconds=1)
    record = retrieval_of(url, saved.text.body, JSON, later).model_copy(
        update={"final_url": f"{url}.moved"}
    )
    store.put(
        SEC_SOURCE_ID,
        saved.text.body,
        record,
        rights_status=SEC_RIGHTS.rights_status,
        rights_basis=SEC_RIGHTS.rights_basis,
    )
    return EASTFIELD, url, refetch_remedy(url)


def wrong_shape_submissions(store, layer):
    url = submissions_url(ACME.cik)
    resave(store, url, b"{}", JSON)
    return ACME, url, refetch_remedy(url)


def another_ciks_submissions(store, layer):
    url = submissions_url(ACME.cik)
    resave(store, url, layer[submissions_url(BOREALIS.cik)][0], JSON)
    return ACME, url, refetch_remedy(url)


def wrong_shape_older_page(store, layer):
    url = EASTFIELD_PAGE
    resave(store, url, b"{}", JSON)
    return EASTFIELD, url, refetch_remedy(url)


def received_for_accepted(store, layer):
    url = filing_index_url(ACME.cik, ACME_RELEASE)
    resave(store, url, layer[url][0].replace(b">Accepted<", b">Received<"), HTML)
    return ACME, url, refetch_remedy(url)


def another_accessions_index_page(store, layer):
    url = filing_index_url(ACME.cik, ACME_RELEASE)
    resave(store, url, index_page(ACME.cik, acme_filing("2025-03-11 08:00:00")), HTML)
    return ACME, url, refetch_remedy(url)


def an_index_page_of_another_form(store, layer):
    url = filing_index_url(ACME.cik, ACME_RELEASE)
    filing = replace(acme_filing("2025-03-20 16:05:00"), form="8-K/A")
    resave(store, url, index_page(ACME.cik, filing), HTML)
    return ACME, url, refetch_remedy(url)


def listed_in_the_main_file_and_an_older_page(store, layer):
    """Eastfield's submissions file, as the layer writes it, with one filing of its
    older page that the build reads listed again among its recent filings."""
    url = submissions_url(EASTFIELD.cik)
    listed = [filing for filing, _ in filings(EASTFIELD)]
    entries, paged = [], []
    for name, since, until in OLDER_PAGES[EASTFIELD]:
        inside = [f for f in listed if since <= f.accepted[:10] < until]
        entries.append(older_page_entry(name, inside))
        paged.append(inside)
    recent = [f for f in listed if not any(f in inside for inside in paged)]
    body = submissions_file(
        EASTFIELD.cik,
        EASTFIELD.name,
        [*recent, paged[0][0]],
        convention=EASTFIELD.convention,
        older_pages=entries,
    )
    resave(store, url, body, JSON)
    return (
        EASTFIELD,
        url,
        refetch_remedy(url, "the submissions file with its older pages"),
    )


@pytest.mark.parametrize(
    "damage",
    [
        bytes_gone,
        bytes_changed,
        redirected_record,
        wrong_shape_submissions,
        another_ciks_submissions,
        wrong_shape_older_page,
        received_for_accepted,
        another_accessions_index_page,
        an_index_page_of_another_form,
        listed_in_the_main_file_and_an_older_page,
    ],
)
def test_each_damaged_response_is_unusable_never_missing(
    universe, layer, tmp_path, damage
) -> None:
    """A saved response the readers cannot use is unusable, by URL, and its problem
    names the refetch that replaces it; it is never missing, which discovery fetches."""
    store = populated(universe, layer, tmp_path)
    registrant, url, remedy = damage(store, layer)
    read = read_issuer(universe, store, registrant)
    assert read.unusable == (url,)
    assert url not in read.missing
    assert len([problem for problem in read.problems if problem.endswith(remedy)]) == 1


def test_a_missing_response_is_missing_never_unusable(universe, tmp_path) -> None:
    store = ArtifactStore(tmp_path / "data" / "raw" / "events", tmp_path)
    url = submissions_url(ACME.cik)
    read = read_issuer(universe, store, ACME)
    assert read.unusable == ()
    assert url in read.missing
    assert read.problems == (f"nothing saved from {url}: run events discover",)


def identification(universe, store: ArtifactStore, registrant: Registrant, event: str):
    """``release-id/1``'s reading of one event's slot, read from ``store``."""
    definition = universe.definition
    saved = SavedResponses(store)
    read = read_issuer(universe, store, registrant)
    facts = read_companyfacts(saved.get(companyfacts_url(registrant.cik)).text.body)
    made, _ = issuer_slots(
        read,
        facts,
        f"cik-{registrant.cik}",
        start=definition.period_end_start,
        stop=definition.period_end_stop,
    )
    (slot,) = [slot for slot in made if slot.event_id == event]
    return identify(
        slot, read.releases, saved, cutoff=definition.public_information_cutoff
    )


def test_a_primary_document_that_cannot_be_read_is_unusable(
    universe, layer, tmp_path
) -> None:
    """A plain-text document reads as ``unread``, a legitimate state; a document
    whose bytes changed is unusable, and named once."""
    store = populated(universe, layer, tmp_path)
    filing = acme_filing("2024-09-26 16:05:00")
    url = archive_url(ACME.cik, filing.accession, filing.primary_document)
    event = "cik-0009990001:2024-08-31"
    resave(store, url, b"Acme Industrial Corp posted its results.\n", "text/plain")
    plain = identification(universe, store, ACME, event)
    assert (plain.unusable, plain.problems) == ((), ())
    assert plain.candidates[0].reading.unread == "it is text/plain, not HTML"
    path = stored_at(store, url)
    path.write_bytes(b"damaged")
    damaged = identification(universe, store, ACME, event)
    assert damaged.unusable == (url,)
    assert damaged.problems == (
        f"{url}: {path} no longer hashes to its name; {refetch_remedy(url)}",
    )


def test_a_damaged_companyfacts_file_names_a_remedy_in_the_build(
    universe, layer, tmp_path
) -> None:
    store = populated(universe, layer, tmp_path)
    url = companyfacts_url(ACME.cik)
    stored_at(store, url).write_bytes(b"{}")
    with pytest.raises(EventBuildError) as caught:
        build_events(
            universe,
            SavedResponses(store),
            load_overrides(REPO / FIXTURE_DIR / "overrides.toml"),
            corpus_id=SYNTHETIC_CORPUS,
        )
    (problem,) = [p for p in caught.value.problems if p.startswith(url)]
    assert problem.endswith(refetch_remedy(url))


def test_a_cited_artifact_that_cannot_be_read_names_a_remedy_that_works(
    universe, layer, tmp_path
) -> None:
    """A cited artifact is read by its hash. While it is its URL's newest response,
    a refetch restores it. Once the URL is saved again with other bytes, a refetch
    restores those, never the bytes the citation names."""
    store = populated(universe, layer, tmp_path)
    overrides = load_overrides(REPO / FIXTURE_DIR / "overrides.toml").overrides
    (override,) = [o for o in overrides if o.override_id == "release-acme-2025-02-28"]
    (citation,) = override.citations
    url = filing_index_url(ACME.cik, ACME_RELEASE)
    assert citation.url == url
    folder = archive_url(ACME.cik, ACME_RELEASE, "")
    path = stored_at(store, url)
    good = path.read_bytes()
    path.write_bytes(b"<html><body>damaged</body></html>")
    damaged = f"release-acme-2025-02-28: {path} no longer hashes to its name"
    assert citations_refused(override, SavedResponses(store), folder) == [
        f"{damaged}; {refetch_remedy(url)}"
    ]
    manifest = load_event_manifest(REPO / FIXTURE_DIR / "events-v1.json")
    evidence = load_event_evidence(
        REPO / FIXTURE_DIR / "events-v1.evidence.json", manifest
    )
    problems = check_evidence(evidence, store)
    assert problems
    assert set(problems) == {
        f"{path} no longer hashes to its name; {refetch_remedy(url)}"
    }
    path.write_bytes(good)
    resave(store, url, good + b"\n", HTML)
    path.write_bytes(b"<html><body>damaged</body></html>")
    (line,) = citations_refused(override, SavedResponses(store), folder)
    assert line.startswith(f"{damaged}; ")
    assert "a refetch cannot restore" in line
    assert "--refetch" not in line


def test_discover_filing_names_the_unusable_file_it_cannot_list(
    universe, layer, tmp_path
) -> None:
    """``--filing`` cannot fetch a saved submissions file, so for one it cannot
    read it names the refetch, never "run events discover"."""
    store = populated(universe, layer, tmp_path)
    url = submissions_url(ACME.cik)
    stored_at(store, url).write_bytes(b"{}")
    recorder = Recorder(layer)
    with pytest.raises(ValueError) as caught:
        run(universe, recorder, store, filing=(ACME.cik, ACME_RELEASE))
    assert str(caught.value).endswith(refetch_remedy(url))
    assert recorder.requested == []


def test_the_refetch_remedy_names_the_command_and_the_url() -> None:
    url = submissions_url(ACME.cik)
    command = f"earnings-pipeline events discover --refetch {url}"
    assert refetch_remedy(url) == f"refetch it: {command}"
    assert refetch_remedy(url, "the submissions file with its older pages") == (
        f"refetch the submissions file with its older pages: {command}"
    )


def test_saved_responses_list_urls_by_prefix_and_every_hash_of_a_url(
    tmp_path,
) -> None:
    store = ArtifactStore(tmp_path / "data" / "raw" / "events", tmp_path)
    page = submissions_page_url("CIK0009990001-submissions-001.json")
    main, facts = submissions_url(ACME.cik), companyfacts_url(ACME.cik)
    for number, url in enumerate([page, facts, main]):
        save(store, url, b"{}", JSON, RETRIEVED + timedelta(seconds=number))
    save(store, main, b'{"saved": "again"}', JSON, RETRIEVED + timedelta(days=1))
    saved = SavedResponses(store)
    assert saved.urls() == (facts, page, main)
    assert saved.urls(submissions_page_url("CIK0009990001")) == (page, main)
    assert saved.hashes(main) == {sha256_hex(b"{}"), sha256_hex(b'{"saved": "again"}')}
    assert saved.hashes(facts) == {sha256_hex(b"{}")}
    assert saved.hashes(submissions_url(BOREALIS.cik)) == frozenset()


def test_cited_remedy_names_the_url_whose_newest_response_the_artifact_is(
    tmp_path,
) -> None:
    """An artifact saved from two URLs is restored by the one whose newest response
    it still is; one whose URLs were all saved again cannot be restored."""
    store = ArtifactStore(tmp_path / "data" / "raw" / "events", tmp_path)
    first, second, third = (f"<p>{n}</p>".encode() for n in ("a", "b", "c"))
    index = filing_index_url(ACME.cik, ACME_RELEASE)
    copy = archive_url(ACME.cik, ACME_RELEASE, "copy.htm")
    save(store, index, first, HTML, RETRIEVED)
    save(store, index, second, HTML, RETRIEVED + timedelta(seconds=1))
    save(store, copy, first, HTML, RETRIEVED)
    other = archive_url(ACME.cik, ACME_RELEASE, "other.htm")
    save(store, other, third, HTML, RETRIEVED)
    save(store, other, second, HTML, RETRIEVED + timedelta(seconds=1))
    saved = SavedResponses(store)
    assert cited_remedy(saved, sha256_hex(first)) == refetch_remedy(copy)
    assert cited_remedy(saved, sha256_hex(second)) == refetch_remedy(index)
    assert cited_remedy(saved, sha256_hex(third)) == (
        f"{other} was saved again with other bytes, so a refetch cannot restore a"
        " citation that names these bytes by hash"
    )
    assert cited_remedy(saved, "0" * 64) == ""


def an_accepted_time_daylight_saving_repeats(store, layer):
    url = filing_index_url(ACME.cik, ACME_RELEASE)
    body = layer[url][0].replace(b">2025-03-20 16:05:00<", b">2024-11-03 01:30:00<")
    resave(store, url, body, HTML)
    return ACME, url, refetch_remedy(url)


def an_index_page_without_its_rows_document(store, layer):
    url = filing_index_url(ACME.cik, ACME_RELEASE)
    filing = replace(acme_filing("2025-03-20 16:05:00"), primary_document="x.htm")
    resave(store, url, index_page(ACME.cik, filing), HTML)
    return ACME, url, refetch_remedy(url)


def listed_twice_in_the_main_file(store, layer):
    url = submissions_url(ACME.cik)
    listed = [filing for filing, _ in filings(ACME)]
    body = submissions_file(
        ACME.cik, ACME.name, [*listed, listed[3]], convention=ACME.convention
    )
    resave(store, url, body, JSON)
    return ACME, url, refetch_remedy(url, "the submissions file with its older pages")


@pytest.mark.parametrize(
    "damage",
    [
        an_accepted_time_daylight_saving_repeats,
        an_index_page_without_its_rows_document,
        listed_twice_in_the_main_file,
    ],
)
def test_other_damaged_responses_are_unusable_never_missing(
    universe, layer, tmp_path, damage
) -> None:
    store = populated(universe, layer, tmp_path)
    registrant, url, remedy = damage(store, layer)
    read = read_issuer(universe, store, registrant)
    assert (read.unusable, read.missing) == ((url,), ())
    (problem,) = read.problems
    assert problem.endswith(remedy)


def test_an_unusable_file_is_listed_once_for_all_its_problems(
    universe, layer, tmp_path
) -> None:
    store = populated(universe, layer, tmp_path)
    url = submissions_url(ACME.cik)
    listed = [filing for filing, _ in filings(ACME)]
    body = submissions_file(
        ACME.cik, ACME.name, [*listed, *listed[3:5]], convention=ACME.convention
    )
    resave(store, url, body, JSON)
    read = read_issuer(universe, store, ACME)
    assert read.unusable == (url,)
    remedy = refetch_remedy(url, "the submissions file with its older pages")
    assert [problem.endswith(remedy) for problem in read.problems] == [True, True]


def test_a_missing_primary_document_is_missing_never_unusable(
    universe, layer, tmp_path, monkeypatch
) -> None:
    store = populated(universe, layer, tmp_path)
    filing = acme_filing("2024-09-26 16:05:00")
    url = archive_url(ACME.cik, filing.accession, filing.primary_document)
    get = SavedResponses.get
    monkeypatch.setattr(
        SavedResponses, "get", lambda self, u: None if u == url else get(self, u)
    )
    found = identification(universe, store, ACME, "cik-0009990001:2024-08-31")
    assert found.unusable == ()
    assert found.problems == (f"nothing saved from {url}: run events discover",)


def test_a_companyfacts_file_of_another_cik_names_a_remedy_in_the_build(
    universe, layer, tmp_path
) -> None:
    store = populated(universe, layer, tmp_path)
    url = companyfacts_url(ACME.cik)
    resave(store, url, layer[companyfacts_url(BOREALIS.cik)][0], JSON)
    with pytest.raises(EventBuildError) as caught:
        build_events(
            universe,
            SavedResponses(store),
            load_overrides(REPO / FIXTURE_DIR / "overrides.toml"),
            corpus_id=SYNTHETIC_CORPUS,
        )
    assert caught.value.problems == (
        f"{url} is the companyfacts file of CIK {BOREALIS.cik}; {refetch_remedy(url)}",
    )


@pytest.mark.parametrize(
    "damage",
    [bytes_changed, another_accessions_index_page, an_index_page_of_another_form],
)
def test_an_override_s_unusable_index_page_names_a_remedy(
    universe, layer, tmp_path, damage
) -> None:
    """The build reads an override's filing only once its first stage has read every
    saved index page, so this reads one that stage did not."""
    store = populated(universe, layer, tmp_path)
    definition = universe.definition
    read = read_issuer(universe, store, ACME)
    facts = SavedResponses(store).get(companyfacts_url(ACME.cik)).text.body
    made, _ = issuer_slots(
        read,
        read_companyfacts(facts),
        f"cik-{ACME.cik}",
        start=definition.period_end_start,
        stop=definition.period_end_stop,
    )
    (slot,) = [slot for slot in made if slot.event_id == "cik-0009990001:2025-02-28"]
    _, url, remedy = damage(store, layer)
    placed, why = _named_filing(
        read,
        SavedResponses(store),
        ACME_RELEASE,
        slot,
        definition.public_information_cutoff,
    )
    assert placed is None
    assert why.startswith(url) and why.endswith(remedy)


def test_a_citation_a_refetch_cannot_mend_names_no_refetch(
    universe, layer, tmp_path
) -> None:
    """A stale locator over valid bytes, and an artifact no saved retrieval names."""
    store = populated(universe, layer, tmp_path)
    overrides = load_overrides(REPO / FIXTURE_DIR / "overrides.toml").overrides
    (override,) = [o for o in overrides if o.override_id == "release-acme-2025-02-28"]
    (citation,) = override.citations
    stale = citation.model_copy(
        update={
            "locator": citation.locator.model_copy(update={"cited_sha256": "0" * 64})
        }
    )
    unknown = citation.model_copy(update={"artifact_sha256": "0" * 64})
    folder = archive_url(ACME.cik, ACME_RELEASE, "")
    saved = SavedResponses(store)
    refused = [
        citations_refused(
            override.model_copy(update={"citations": (c,)}), saved, folder
        )
        for c in (stale, unknown)
    ]
    unknown_line = (
        f"release-acme-2025-02-28: no artifact {'0' * 64} for source 'sec-edgar'"
        f" under {store.root}"
    )
    assert refused == [
        ["release-acme-2025-02-28: the cited content no longer hashes to cited_sha256"],
        [unknown_line],
    ]


def test_evidence_no_saved_retrieval_names_has_no_remedy(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "data" / "raw" / "events", tmp_path)
    manifest = load_event_manifest(REPO / FIXTURE_DIR / "events-v1.json")
    evidence = load_event_evidence(
        REPO / FIXTURE_DIR / "events-v1.evidence.json", manifest
    )
    problems = check_evidence(evidence, store)
    under = re.escape(str(store.root))
    assert problems
    assert all(
        re.fullmatch(
            f"no artifact [0-9a-f]{{64}} for source 'sec-edgar' under {under}", p
        )
        for p in problems
    )


def test_discover_filing_names_an_unusable_index_page_and_fetches_nothing(
    universe, layer, tmp_path
) -> None:
    store = populated(universe, layer, tmp_path)
    _, url, remedy = bytes_changed(store, layer)
    recorder = Recorder(layer)
    result, sent, _ = run(universe, recorder, store, filing=(ACME.cik, ACME_RELEASE))
    (problem,) = result.problems
    assert problem.startswith(f"{url}: ") and problem.endswith(remedy)
    assert (recorder.requested, sent) == ([], 0)


def test_discover_filing_names_only_an_unusable_file_that_lists_filings(
    universe, layer, tmp_path
) -> None:
    """An unusable older page may hold the filing; an unusable index page lists
    none, so a filing no file lists still needs discovery."""
    store = populated(universe, layer, tmp_path)
    bytes_changed(store, layer)
    with pytest.raises(ValueError) as caught:
        run(universe, Recorder(layer), store, filing=(ACME.cik, "0009990001-99-000001"))
    assert str(caught.value).endswith(": run events discover")
    stored_at(store, EASTFIELD_PAGE).write_bytes(b"{}")
    _, since, until = OLDER_PAGES[EASTFIELD][0]
    (paged, *_) = [f for f, _ in filings(EASTFIELD) if since <= f.accepted[:10] < until]
    with pytest.raises(ValueError) as caught:
        run(universe, Recorder(layer), store, filing=(EASTFIELD.cik, paged.accession))
    assert str(caught.value).endswith(refetch_remedy(EASTFIELD_PAGE))


def test_stage_5_has_no_client_or_throttle_of_its_own() -> None:
    """R1.3, D5: every request goes through the shared SEC client."""
    own = re.compile(
        r"^\s*(?:import|from)\s+(?:httpx|requests|urllib|socket)\b|Throttle\(|time\.sleep",
        re.MULTILINE,
    )
    found = [
        path.name
        for path in sorted(EVENTS_PACKAGE.glob("*.py"))
        if own.search(path.read_text(encoding="utf-8"))
    ]
    assert not found


def test_a_response_saved_under_another_url_stops_discovery(
    universe, layer, tmp_path
) -> None:
    """A fetched response that is still missing would loop forever: discovery stops."""
    store = ArtifactStore(tmp_path / "data" / "raw" / "events", tmp_path)
    recorder = Recorder(layer)
    with open_sec_client(
        environ=IDENTITY, transport=recorder.transport(), sleep=lambda seconds: None
    ) as sec:

        def astray(url: str, types: frozenset[str]):
            fetched = sec.fetch(url, types)
            moved = fetched.retrieval.model_copy(update={"request_url": f"{url}?moved"})
            return fetched.__class__(body=fetched.body, retrieval=moved)

        with pytest.raises(RuntimeError, match="was fetched, and is still missing"):
            discover(universe, astray, store)
