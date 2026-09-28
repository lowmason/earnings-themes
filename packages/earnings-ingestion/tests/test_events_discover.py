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
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.build import build_events, load_overrides
from earnings_ingestion.events.discover import discover, discover_filing
from earnings_ingestion.events.filings import issuer_filings
from earnings_ingestion.events.fixture import (
    COHORT_MANIFEST,
    FIXTURE_DIR,
    SYNTHETIC_CORPUS,
)
from earnings_ingestion.events.freeze import load_event_manifest
from earnings_ingestion.events.layer import (
    ACME,
    BOREALIS,
    CORVID,
    DYNAMO,
    Release,
    exhibit_bodies,
    filings,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.synthetic import eight_k, index_page, save
from earnings_ingestion.fetch.client import UnexpectedResponse
from earnings_ingestion.fetch.records import Retrieval
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.client import open_sec_client
from earnings_ingestion.sec.filing_index import read_filing_index
from earnings_ingestion.sec.urls import (
    archive_url,
    filing_index_url,
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
        f"{submissions}: no artifact {gone[submissions]} {no_bytes} are gone",
        f"{index}: the index page states no Accepted",
        f"{document}: no artifact {gone[document]} {no_bytes} are gone",
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
    assert result.problems == [f"{index}: its form is 8-K/A, but its row's is 8-K"]


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
