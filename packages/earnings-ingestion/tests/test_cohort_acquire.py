"""Acquisition, offline: a fake fetch serves the synthetic cohort's SEC records."""

import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import RightsStatus, sha256_hex
from earnings_ingestion.cohort.acquire import (
    check_media_type,
    cite,
    fetch_page,
    fetch_sec,
    register_saved,
    terms_digest,
)
from earnings_ingestion.cohort.build import build
from earnings_ingestion.cohort.config import load_cohort_config
from earnings_ingestion.cohort.register import load_registers
from earnings_ingestion.cohort.synthetic import FIXTURE_DIR, build_options
from earnings_ingestion.fetch.client import Fetched
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore

RAW = FIXTURE_DIR / "raw"
SYNTHETIC = {
    "rights_status": RightsStatus.REDISTRIBUTABLE,
    "rights_basis": "synthetic test data, invented for this repository",
}
NOW = datetime(2026, 9, 30, 9, 0, tzinfo=UTC)


def served(repo: Path, *sources: str) -> dict[str, tuple[bytes, str]]:
    """Every saved artifact of ``sources``, by the URL it came from."""
    store = ArtifactStore(repo / RAW, repo)
    pages = {}
    for source_id in sources:
        for path in (repo / RAW / source_id / "retrievals").glob("*/*.json"):
            record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
            body = store.get(source_id, record.sha256, **SYNTHETIC).body
            pages[record.request_url] = (body, record.media_type)
    return pages


def fake(pages: dict[str, tuple[bytes, str]], requested: list[str]):
    def fetch(url: str, types: frozenset[str]) -> Fetched:
        requested.append(url)
        body, media = pages[url]
        assert media in types
        return Fetched(
            body=body,
            retrieval=Retrieval(
                request_url=url,
                final_url=url,
                retrieved_at=NOW,
                retrieval_method=RetrievalMethod.HTTP,
                http_status=200,
                media_type=media,
                content_type=media,
                byte_count=len(body),
                sha256=sha256_hex(body),
            ),
        )

    return fetch


def test_fetch_sec_saves_every_record_the_build_reads(cohort_repo) -> None:
    pages = served(cohort_repo, "sec-edgar", "synthetic-fund")
    for source_id in ("sec-edgar", "synthetic-fund"):
        shutil.rmtree(cohort_repo / RAW / source_id)
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    options = build_options()
    registers = load_registers(
        cohort_repo, options["register"], options["sec_register"]
    )
    config = load_cohort_config(cohort_repo / FIXTURE_DIR)
    requested: list[str] = []

    first = fetch_sec(fake(pages, requested), store, registers, config)
    assert sorted(first.fetched) == sorted(pages)
    assert first.kept == []
    rebuilt = build(cohort_repo, **options)
    assert rebuilt.report.blocking == ()
    assert rebuilt.candidate_issuer_ids == (
        "cik-0009990001",
        "cik-0009990002",
        "cik-0009990003",
        "cik-0009990005",
        "cik-0009990006",
    )

    again = fetch_sec(fake(pages, requested), store, registers, config)
    assert len(again.kept) == 10
    assert all("/Archives/" not in url for url in again.fetched)


def registers_of(repo: Path):
    options = build_options()
    return load_registers(repo, options["register"], options["sec_register"])


def test_a_hand_saved_page_records_that_nothing_was_fetched(cohort_repo) -> None:
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    ref = register_saved(
        store,
        registers_of(cohort_repo),
        "synthetic-index",
        b"<p>Saved in a browser.</p>",
        url="https://index.example/notices/saved",
        media_type="text/html",
        saved_at=NOW,
    )
    (retrieval,) = store.get(
        "synthetic-index", ref.content_sha256, **SYNTHETIC
    ).retrievals
    assert retrieval.retrieval_method is RetrievalMethod.SAVED_BY_USER
    assert retrieval.http_status is None


def test_a_page_is_saved_only_for_a_registered_source(cohort_repo) -> None:
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    pages = {"https://index.example/a": (b"<p>A notice.</p>", "text/html")}
    fetch = fake(pages, [])
    ref = fetch_page(
        fetch,
        store,
        registers_of(cohort_repo),
        "synthetic-index",
        "https://index.example/a",
    )
    assert ref.storage_ref.startswith("tests/fixtures/cohort/raw/synthetic-index/")
    with pytest.raises(ValueError, match="not in the membership source register"):
        fetch_page(
            fetch,
            store,
            registers_of(cohort_repo),
            "elsewhere",
            "https://index.example/a",
        )


def test_cite_finds_a_span_or_a_pointer_and_shows_its_text(cohort_repo) -> None:
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    registers = registers_of(cohort_repo)
    page = next(iter(served(cohort_repo, "synthetic-index").values()))[0]
    locator, text = cite(
        store,
        registers,
        "synthetic-index",
        sha256_hex(page),
        find="Synthetic Industrial Average",
    )
    assert text == "Synthetic Industrial Average"
    assert locator.canonicalization_version == "walker-1"
    again, same = cite(
        store,
        registers,
        "synthetic-index",
        sha256_hex(page),
        span=(locator.start, locator.end),
    )
    assert (again, same) == (locator, text)
    tickers = next(
        body
        for url, (body, _) in served(cohort_repo, "sec-edgar").items()
        if url.endswith("company_tickers.json")
    )
    pointed, value = cite(
        store, registers, "sec-edgar", sha256_hex(tickers), pointer="/0/ticker"
    )
    assert (pointed.pointer, value) == ("/0/ticker", '"ACME"')
    with pytest.raises(ValueError, match="exactly one"):
        cite(store, registers, "sec-edgar", sha256_hex(tickers))


def test_cite_can_take_the_whole_line_holding_a_row(cohort_repo) -> None:
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    registers = registers_of(cohort_repo)
    page = next(iter(served(cohort_repo, "synthetic-roster").values()))[0]
    locator, text = cite(
        store, registers, "synthetic-roster", sha256_hex(page), find="ACM", line=True
    )
    assert "\t" in text and "ACM" in text and "\n" not in text
    found, _ = cite(store, registers, "synthetic-roster", sha256_hex(page), find="ACM")
    assert locator.start <= found.start < found.end <= locator.end
    with pytest.raises(ValueError, match="line needs find"):
        cite(
            store,
            registers,
            "synthetic-roster",
            sha256_hex(page),
            span=(0, 3),
            line=True,
        )


def test_a_terms_page_is_hashed_by_its_canonical_text() -> None:
    page = b"<html><body><p>Terms.</p></body></html>"
    assert terms_digest(page, "text/html") == terms_digest(
        page.replace(b"<p>", b"<p class='x'>"), "text/html"
    )
    assert terms_digest(b"plain", "text/plain") == sha256_hex(b"plain")


@pytest.mark.parametrize(
    ("body", "media_type", "found"),
    [
        (b"%PDF-1.4\n%%EOF\n", "text/html", "which are a PDF"),
        (b"<p>A notice.</p>", "application/pdf", "which are not a PDF"),
    ],
)
def test_bytes_that_contradict_their_type_are_refused(
    cohort_repo, body, media_type, found
) -> None:
    refusal = f"{media_type} contradicts the bytes, {found}"
    with pytest.raises(ValueError, match=refusal):
        check_media_type(body, media_type)
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    with pytest.raises(ValueError, match=refusal):
        register_saved(
            store,
            registers_of(cohort_repo),
            "synthetic-index",
            body,
            url="https://index.example/notices/saved",
            media_type=media_type,
            saved_at=NOW,
        )
    assert not list(
        (cohort_repo / RAW / "synthetic-index").glob(f"{sha256_hex(body)}.*")
    )


def test_bytes_that_match_their_type_pass() -> None:
    check_media_type(b"%PDF-1.7\n", "application/pdf")
    check_media_type(b"<p>A notice.</p>", "text/html")
    check_media_type(b"Terms.", "text/plain; charset=utf-8")


def test_a_pdf_page_is_fetched_and_saved_as_a_pdf(cohort_repo, make_pdf) -> None:
    store = ArtifactStore(cohort_repo / RAW, cohort_repo)
    pdf = make_pdf([(72, 720, "A notice.")])
    url = "https://index.example/notices/a.pdf"
    fetch = fake({url: (pdf, "application/pdf")}, [])
    ref = fetch_page(fetch, store, registers_of(cohort_repo), "synthetic-index", url)
    assert ref.media_type == "application/pdf"
    assert ref.storage_ref.endswith(f"/synthetic-index/{sha256_hex(pdf)}.pdf")
