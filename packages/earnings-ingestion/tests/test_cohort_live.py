"""The live verification's logic, offline: fake fetches stand in for the clients."""

from contextlib import contextmanager
from datetime import UTC, datetime
from types import SimpleNamespace

from earnings_core import RightsStatus, sha256_hex
from earnings_ingestion.cohort import live
from earnings_ingestion.cohort.live import verify_live
from earnings_ingestion.cohort.records import LiveVerification
from earnings_ingestion.cohort.synthetic import FIXTURE_DIR, build_options
from earnings_ingestion.cohort.web import RobotsRefusal
from earnings_ingestion.fetch.client import AccessStop, Fetched
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore

NOW = datetime(2026, 10, 2, 9, 0, tzinfo=UTC)
RIGHTS = {
    "rights_status": RightsStatus.REDISTRIBUTABLE,
    "rights_basis": "synthetic test data, invented for this repository",
}


def pages(repo) -> dict[str, tuple[bytes, str]]:
    store = ArtifactStore(repo / FIXTURE_DIR / "raw", repo)
    served = {}
    for source_id in ("synthetic-roster", "synthetic-index"):
        for path in (repo / FIXTURE_DIR / "raw" / source_id / "retrievals").glob(
            "*/*.json"
        ):
            record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
            body = store.get(source_id, record.sha256, **RIGHTS).body
            served[record.request_url] = (body, "text/html")
    return served


def fake(served, refuse=frozenset(), block=frozenset()):
    def fetch(url, types):
        if url in refuse:
            raise RobotsRefusal(f"{url} is refused by robots.txt (Disallow: /)")
        if url in block:
            raise AccessStop(
                f"403 persisted for {url}; stopping without changing identity"
            )
        body, media = served.get(url, (b"synthetic terms", "text/plain"))
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


def test_an_unchanged_world_rebuilds_the_frozen_manifest(cohort_repo) -> None:
    served = pages(cohort_repo)
    result = verify_live(
        cohort_repo,
        fetch_web=fake(served),
        fetch_sec=fake(served),
        now=NOW,
        options=build_options(),
    )
    assert {check.outcome for check in result.checks} == {"unchanged"}
    assert {check.purpose for check in result.checks} == {"terms", "evidence"}
    assert all(check.retrieval is not None for check in result.checks)
    assert result.rebuilt_content_hash == result.frozen_content_hash
    assert result.rebuilt_operative_hash == result.frozen_operative_hash
    assert result.rebuilt_operative_hash is not None
    assert result.blocking_finding_ids == ()
    assert result.build_problems == ()


def test_a_register_only_change_keeps_the_operative_hash(cohort_repo) -> None:
    """The source register's version is in the content hash and no fact is."""
    register = cohort_repo / FIXTURE_DIR / "source-register.toml"
    text = register.read_text(encoding="utf-8")
    assert 'owner = "Synthetic SEC"' in text
    register.write_text(
        text.replace('owner = "Synthetic SEC"', 'owner = "Synthetic SEC, renamed"'),
        encoding="utf-8",
    )
    served = pages(cohort_repo)
    result = verify_live(
        cohort_repo,
        fetch_web=fake(served),
        fetch_sec=fake(served),
        now=NOW,
        options=build_options(),
    )
    assert result.rebuilt_content_hash != result.frozen_content_hash
    assert result.rebuilt_operative_hash == result.frozen_operative_hash
    assert result.rebuilt_operative_hash is not None


def test_a_changed_fact_changes_the_operative_hash(cohort_repo) -> None:
    """An edit to the universe's definition changes a fact, so both hashes move."""
    universe = cohort_repo / FIXTURE_DIR / "universe.toml"
    text = universe.read_text(encoding="utf-8")
    one, two = (f'selection_policy_version = "djia-pilot/{n}"' for n in (1, 2))
    assert one in text
    universe.write_text(text.replace(one, two, 1), encoding="utf-8")
    served = pages(cohort_repo)
    result = verify_live(
        cohort_repo,
        fetch_web=fake(served),
        fetch_sec=fake(served),
        now=NOW,
        options=build_options(),
    )
    assert result.rebuilt_content_hash != result.frozen_content_hash
    assert result.rebuilt_operative_hash != result.frozen_operative_hash
    assert None not in (result.rebuilt_operative_hash, result.frozen_operative_hash)


def test_a_failed_rebuild_has_no_rebuilt_operative_hash(cohort_repo) -> None:
    served = pages(cohort_repo)
    page = next((cohort_repo / FIXTURE_DIR / "raw" / "synthetic-roster").glob("*.html"))
    page.unlink()
    result = verify_live(
        cohort_repo,
        fetch_web=fake(served),
        fetch_sec=fake(served),
        now=NOW,
        options=build_options(),
    )
    assert result.build_problems
    assert result.rebuilt_content_hash is None
    assert result.rebuilt_operative_hash is None
    assert result.frozen_operative_hash is not None


def test_an_unreadable_terms_page_is_recorded_not_raised(
    cohort_repo, monkeypatch
) -> None:
    def unreadable(body, media_type):
        raise ValueError("walker-1 found no text")

    monkeypatch.setattr(live, "terms_digest", unreadable)
    served = pages(cohort_repo)
    result = verify_live(
        cohort_repo,
        fetch_web=fake(served),
        fetch_sec=fake(served),
        now=NOW,
        options=build_options(),
    )
    terms = [check for check in result.checks if check.purpose == "terms"]
    assert terms
    for check in terms:
        assert check.outcome == "failed"
        assert check.detail.startswith("terms page unreadable: ")
        assert "walker-1 found no text" in check.detail
        assert check.retrieval is not None
    evidence = [check for check in result.checks if check.purpose == "evidence"]
    assert {check.outcome for check in evidence} == {"unchanged"}


def test_changes_and_refusals_are_recorded_not_hidden(cohort_repo) -> None:
    served = pages(cohort_repo)
    changed = "https://roster.example/index?rev=1001"
    served[changed] = (b"<p>A newer revision.</p>", "text/html")
    refused = "https://index.example/notices/index-2024-11-01"
    blocked = "https://www.sec.gov/privacy"
    result = verify_live(
        cohort_repo,
        fetch_web=fake(served, refuse={refused}),
        fetch_sec=fake(served, block={blocked}),
        now=NOW,
        options=build_options(),
    )
    outcomes = {check.url: check.outcome for check in result.checks}
    assert outcomes[changed] == "changed"
    assert outcomes[refused] == "refused"
    assert outcomes[blocked] == "refused"
    assert result.rebuilt_content_hash == result.frozen_content_hash


def test_the_evidence_refetch_accepts_an_unchanged_pdf(pdf_cohort) -> None:
    served = pages(pdf_cohort)
    notice = "https://index.example/notices/index-2024-11-01"
    pdf = next((pdf_cohort / FIXTURE_DIR / "raw" / "synthetic-index").glob("*.pdf"))
    served[notice] = (pdf.read_bytes(), "application/pdf")
    serve = fake(served)

    def fetch(url, types):
        """The clients refuse a response whose media type was not asked for."""
        fetched = serve(url, types)
        assert fetched.retrieval.media_type in types
        return fetched

    result = verify_live(
        pdf_cohort,
        fetch_web=fetch,
        fetch_sec=fake(served),
        now=NOW,
        options=build_options(),
    )
    (check,) = [check for check in result.checks if check.url == notice]
    assert (check.outcome, check.retrieval.media_type) == (
        "unchanged",
        "application/pdf",
    )
    assert result.build_problems == ()


def test_run_live_caps_each_client_and_records_what_both_sent(
    tmp_path, monkeypatch
) -> None:
    """Each client is capped at the approved count, and the record keeps the
    requests both sent (PR #6's review, F35)."""

    class Fake:
        def __init__(self, count: int) -> None:
            self.throttle = SimpleNamespace(count=count)
            self.client = self
            self.fetch = None

    @contextmanager
    def web(hosts, *, environ, max_requests):
        assert max_requests == 7
        yield Fake(2)

    @contextmanager
    def sec(*, environ, max_requests):
        assert max_requests == 7
        yield Fake(1)

    empty = LiveVerification(
        checked_at=datetime(2026, 9, 29, tzinfo=UTC),
        checks=(),
        build_problems=(),
        rebuilt_content_hash=None,
        frozen_content_hash=None,
        blocking_finding_ids=(),
    )
    assert empty.requests_sent is None
    monkeypatch.setattr(live, "_targets", lambda repo, options: [])
    monkeypatch.setattr(live, "open_web_client", web)
    monkeypatch.setattr(live, "open_sec_client", sec)
    monkeypatch.setattr(live, "verify_live", lambda repo, **kwargs: empty)
    result, path = live.run_live(tmp_path, max_requests=7)
    assert result.requests_sent == 3
    saved = LiveVerification.model_validate_json(path.read_text(encoding="utf-8"))
    assert saved.requests_sent == 3
