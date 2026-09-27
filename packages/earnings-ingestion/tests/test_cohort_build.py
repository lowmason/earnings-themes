"""The build and the freeze, on copies of the synthetic cohort (P §Failure handling)."""

import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import RightsStatus, sha256_hex
from earnings_ingestion.cohort.build import CohortError, build
from earnings_ingestion.cohort.freeze import (
    FreezeRefused,
    freeze,
    frozen_manifests,
    load_manifest,
)
from earnings_ingestion.cohort.locators import ArtifactText
from earnings_ingestion.cohort.synthetic import FIXTURE_DIR, build_options
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.data import FILING_COLUMNS
from earnings_ingestion.sec.urls import COMPANY_TICKERS_URL, submissions_url

DIRECTORY = FIXTURE_DIR
OPTIONS = build_options()
LATER = datetime(2026, 10, 1, tzinfo=UTC)
SYNTHETIC = {
    "rights_status": RightsStatus.REDISTRIBUTABLE,
    "rights_basis": "synthetic test data, invented for this repository",
}


def save(
    store: ArtifactStore, source_id: str, url: str, body: bytes, media: str
) -> str:
    """Save ``body`` as retrieved a day after the synthetic cohort's artifacts."""
    retrieval = Retrieval(
        request_url=url,
        final_url=url,
        retrieved_at=datetime(2026, 9, 28, 12, 0, tzinfo=UTC),
        retrieval_method=RetrievalMethod.HTTP,
        http_status=200,
        media_type=media,
        content_type=media,
        byte_count=len(body),
        sha256=sha256_hex(body),
    )
    return store.put(source_id, body, retrieval, **SYNTHETIC).content_sha256


@pytest.fixture
def repo(cohort_repo: Path) -> Path:
    return cohort_repo


def edit(repo: Path, name: str, old: str, new: str) -> None:
    path = repo / DIRECTORY / name
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def blocking_ids(repo: Path) -> set[str]:
    return {finding.finding_id for finding in build(repo, **OPTIONS).report.blocking}


def test_the_reviewed_cohort_holds_no_blocking_finding(repo) -> None:
    assert blocking_ids(repo) == set()


def test_before_review_its_findings_hold_the_freeze(repo) -> None:
    (repo / DIRECTORY / "overrides.toml").unlink()
    held = build(repo, **OPTIONS)
    ids = {finding.finding_id for finding in held.report.blocking}
    assert {
        "membership_conflict:corvid-common",
        "member_count:2024-11-08",
        "identity:eastfield-common",
        "difference:roster-2024-11-08",
    } <= ids
    with pytest.raises(FreezeRefused, match="membership_conflict:corvid-common"):
        freeze(held, repo / DIRECTORY / "manifests", now=LATER)


def test_a_missing_anchor_refuses_the_freeze_with_its_reason(repo) -> None:
    edit(repo, "evidence.toml", 'role = "anchor"', 'role = "corroboration"')
    held = build(repo, **OPTIONS)
    missing = [f for f in held.report.blocking if f.kind == "missing_anchor"]
    assert [f.detail for f in missing] == ["no anchor snapshot is curated"]
    with pytest.raises(FreezeRefused, match="missing_anchor:anchor"):
        freeze(held, repo / DIRECTORY / "manifests", now=LATER)


def test_a_later_snapshot_is_never_backdated_into_the_anchor(repo) -> None:
    edit(
        repo, "evidence.toml", "published_on = 2024-06-20", "published_on = 2024-07-15"
    )
    (missing,) = [
        f for f in build(repo, **OPTIONS).report.blocking if f.kind == "missing_anchor"
    ]
    assert "a later snapshot is never backdated" in missing.detail


def test_fund_holdings_are_never_the_roster(repo) -> None:
    register = "membership-source-register.toml"
    edit(repo, register, 'evidence_class = "secondary"', 'evidence_class = "etf_proxy"')
    (missing,) = [
        f for f in build(repo, **OPTIONS).report.blocking if f.kind == "missing_anchor"
    ]
    assert "etf_proxy evidence is not a roster" in missing.detail


def test_a_missing_artifact_stops_the_build(repo) -> None:
    for path in (repo / DIRECTORY / "raw" / "synthetic-roster").glob("*.html"):
        path.unlink()
    with pytest.raises(CohortError, match="no artifact"):
        build(repo, **OPTIONS)


def test_edited_bytes_stop_the_build(repo) -> None:
    page = next((repo / DIRECTORY / "raw" / "synthetic-index").glob("*.html"))
    page.write_bytes(page.read_bytes().replace(b"synthetic", b"edited"))
    with pytest.raises(CohortError, match="no longer hashes to its name"):
        build(repo, **OPTIONS)


def test_a_fact_the_cited_text_does_not_state_stops_the_build(repo) -> None:
    edit(repo, "evidence.toml", 'ticker = "ACMX"', 'ticker = "ACMQ"')
    with pytest.raises(CohortError, match="does not state 'ACMQ'"):
        build(repo, **OPTIONS)


def test_an_unregistered_source_stops_the_build(repo) -> None:
    edit(
        repo, "evidence.toml", 'source_id = "synthetic-index"', 'source_id = "nowhere"'
    )
    with pytest.raises(CohortError, match="not in the membership source register"):
        build(repo, **OPTIONS)


def test_an_acknowledgement_binds_to_what_the_reviewer_read(repo) -> None:
    path = repo / DIRECTORY / "overrides.toml"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'finding_digest = "[0-9a-f]{64}"', f'finding_digest = "{"0" * 64}"', text
    )
    path.write_text(text, encoding="utf-8")
    stale = build(repo, **OPTIONS)
    assert stale.stale_acknowledgements == ("ack-lagging-revision",)
    assert "difference:roster-2024-11-08" in {
        f.finding_id for f in stale.report.blocking
    }
    with pytest.raises(FreezeRefused, match="acknowledges a finding that has changed"):
        freeze(stale, repo / DIRECTORY / "manifests", now=LATER)


def test_identical_content_keeps_its_version(repo) -> None:
    manifests = repo / DIRECTORY / "manifests"
    again = freeze(build(repo, **OPTIONS), manifests, now=LATER)
    assert (again.created, again.manifest.definition.universe_version) == (False, 1)
    assert [path.name for path in manifests.iterdir()] == ["djia-synthetic-v1.json"]


def test_changed_evidence_is_a_new_version_beside_the_old(repo) -> None:
    manifests = repo / DIRECTORY / "manifests"
    first = (manifests / "djia-synthetic-v1.json").read_bytes()
    edit(
        repo,
        "universe.toml",
        'selection_policy_version = "djia-pilot/1"',
        'selection_policy_version = "djia-pilot/2"',
    )
    second = freeze(build(repo, **OPTIONS), manifests, now=LATER)
    assert (second.created, second.path.name) == (True, "djia-synthetic-v2.json")
    assert (manifests / "djia-synthetic-v1.json").read_bytes() == first
    versions = [
        m.definition.universe_version
        for m in frozen_manifests(manifests, "djia-synthetic")
    ]
    assert versions == [1, 2]


def test_a_frozen_manifest_loads_without_any_saved_artifact(repo) -> None:
    shutil.rmtree(repo / DIRECTORY / "raw")
    manifest = load_manifest(repo / DIRECTORY / "manifests" / "djia-synthetic-v1.json")
    assert manifest.definition.selection_policy_version == "djia-pilot/1"
    assert all(len(issuer.cik) == 10 for issuer in manifest.issuers)


def test_a_tampered_manifest_is_refused(repo) -> None:
    path = repo / DIRECTORY / "manifests" / "djia-synthetic-v1.json"
    path.write_text(path.read_text().replace('"2024-11-08"', '"2024-11-09"', 1))
    with pytest.raises(ValueError, match="does not hash to its content_hash"):
        load_manifest(path)


def test_a_retained_unresolved_security_is_excluded_and_the_freeze_proceeds(
    repo,
) -> None:
    edit(repo, "overrides.toml", 'kind = "set_issuer"', 'kind = "retain_unresolved"')
    edit(repo, "overrides.toml", 'cik = "0009990006"\n', "")
    kept = build(repo, **OPTIONS)
    (mapping,) = [m for m in kept.mappings if m.security_id == "eastfield-common"]
    assert (mapping.status, mapping.override_id) == (
        "retained_unresolved",
        "eastfield-issuer",
    )
    assert "cik-0009990006" not in kept.candidate_issuer_ids
    (finding,) = [f for f in kept.report.findings if f.kind == "identity"]
    assert finding.resolved_by == ("eastfield-issuer",)
    frozen = freeze(kept, repo / DIRECTORY / "manifests", now=LATER)
    assert frozen.manifest.definition.universe_version == 2


def test_a_row_published_after_the_cutoff_never_changes_an_identity(repo) -> None:
    root = repo / DIRECTORY
    store = ArtifactStore(root / "raw", repo)
    tickers = store.latest("sec-edgar", COMPANY_TICKERS_URL, **SYNTHETIC)
    rival = json.loads(tickers.body) | {
        "99": {"cik_str": 9990008, "ticker": "ACMR", "title": "Acme Industrial Rival"}
    }
    save(
        store,
        "sec-edgar",
        COMPANY_TICKERS_URL,
        json.dumps(rival).encode(),
        "application/json",
    )
    filings = {column: [] for column in FILING_COLUMNS}
    rival_record = {
        "cik": "9990008",
        "name": "Acme Industrial Rival Inc",
        "tickers": ["ACMR"],
        "filings": {"recent": filings, "files": []},
    }
    save(
        store,
        "sec-edgar",
        submissions_url(9990008),
        json.dumps(rival_record).encode(),
        "application/json",
    )
    page = b"<html><body><p>Acme Industrial (ACMR) will join on October 9, 2026.</p></body></html>"
    url = "https://index.example/notices/index-2026-09-30"
    sha = save(store, "synthetic-index", url, page, "text/html")
    text = ArtifactText(page, "text/html")
    row, when = text.find("Acme Industrial (ACMR)"), text.find("October 9, 2026")
    with (root / "evidence.toml").open("a", encoding="utf-8") as out:
        out.write(
            f'\n[[changes]]\nevidence_id = "index-2026-09-30"\nsource_id = "synthetic-index"\n'
            f'url = "{url}"\nartifact_sha256 = "{sha}"\n'
            f'canonical_sha256 = "{text.canonical[1]}"\nannounced_on = 2026-09-30\n'
            f"published_on = 2026-09-30\neffective_on = 2026-10-09\n"
            f'timing = "unspecified"\ndate_span = [{when.start}, {when.end}]\n'
            f'date_cited_sha256 = "{when.cited_sha256}"\n\n[[changes.entries]]\n'
            f'action = "added"\nsecurity_id = "acme-common"\nname = "Acme Industrial"\n'
            f'ticker = "ACMR"\nspan = [{row.start}, {row.end}]\n'
            f'cited_sha256 = "{row.cited_sha256}"\n'
        )
    later = build(repo, **OPTIONS)
    (acme,) = [m for m in later.mappings if m.security_id == "acme-common"]
    assert (acme.status, acme.cik) == ("resolved", "0009990001")
    assert "ACMR" in {i.ticker for s in later.securities for i in s.identities}
    assert not later.report.blocking


def test_the_manifest_records_rights_for_every_source_it_cites(repo) -> None:
    manifest = load_manifest(repo / DIRECTORY / "manifests" / "djia-synthetic-v1.json")
    cited = {a.source_id for a in manifest.assertions}
    cited |= {r.source_id for r in manifest.report.reconciliations}
    cited |= {
        c.source_id
        for m in manifest.mappings
        for candidate in m.candidates
        for c in candidate.citations
    }
    assert {s.source_id for s in manifest.sources} == cited
    assert {s.source_id: s.rights_status for s in manifest.sources}["sec-edgar"] == (
        "local_only"
    )


def test_a_pdf_notice_keeps_the_intervals_and_cites_through_pdftext_1(
    pdf_cohort,
) -> None:
    frozen = load_manifest(
        pdf_cohort / DIRECTORY / "manifests" / "djia-synthetic-v1.json"
    )
    built = build(pdf_cohort, **OPTIONS)
    assert built.intervals == frozen.intervals
    assert built.report.blocking == ()
    pdf = next((pdf_cohort / DIRECTORY / "raw" / "synthetic-index").glob("*.pdf"))
    notice = [a for a in built.assertions if a.evidence_id == "index-2024-11-01"]
    assert {a.security_id for a in notice} == {"corvid-common", "borealis-common"}
    assert {a.raw_content_hash for a in notice} == {pdf.stem}
    assert {
        locator.canonicalization_version
        for assertion in notice
        for locator in assertion.evidence_locators
    } == {"pdftext-1"}
