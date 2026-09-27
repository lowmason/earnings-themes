"""The synthetic event layer (the Stage 5 spec, §The synthetic event layer; plan 7,
P7-17), read through the slot, release, and eligibility functions over Stage 4's
synthetic cohort, before any override.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.events.eligibility import decide, memberships
from earnings_ingestion.events.filings import IssuerFilings, issuer_filings
from earnings_ingestion.events.layer import ACME, filings, write_layer
from earnings_ingestion.events.release import Identification, identify
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.slots import Slot, issuer_slots
from earnings_ingestion.events.synthetic import SyntheticStore
from earnings_ingestion.fetch.records import Retrieval
from earnings_ingestion.sec.companyfacts import read_companyfacts
from earnings_ingestion.sec.urls import (
    archive_url,
    companyfacts_url,
    filing_index_url,
    submissions_page_url,
)

ROOT = Path(__file__).resolve().parents[3]
COHORT = ROOT / "tests" / "fixtures" / "cohort" / "manifests" / "djia-synthetic-v1.json"


@dataclass(frozen=True)
class Read:
    """What the functions make of one issuer's saved responses."""

    filings: IssuerFilings
    slots: tuple[Slot, ...]
    findings: tuple
    identified: dict[str, Identification]
    reasons: dict[str, str]


def read_issuer(saved, manifest, issuer) -> Read:
    definition = manifest.definition
    start, stop = definition.period_end_start, definition.period_end_stop
    cutoff = definition.public_information_cutoff
    placed = issuer_filings(
        saved, issuer.cik, issuer.issuer_id, start=start, cutoff=cutoff
    )
    facts = read_companyfacts(saved.get(companyfacts_url(issuer.cik)).text.body)
    slots, findings = issuer_slots(
        placed, facts, issuer.issuer_id, start=start, stop=stop
    )
    identified, reasons = {}, {}
    membership = memberships(manifest)[issuer.issuer_id]
    for slot in slots:
        found = identify(slot, placed.releases, saved, cutoff=cutoff)
        published = None if found.release is None else found.release.placed.instant
        decision = decide(
            slot.period_end,
            published,
            found.reason,
            membership,
            start=start,
            stop=stop,
            cutoff=cutoff,
        )
        identified[slot.event_id] = found
        reasons[slot.event_id] = decision.reason.value
    return Read(placed, slots, findings, identified, reasons)


@pytest.fixture(scope="module")
def layer(tmp_path_factory) -> SyntheticStore:
    repo = tmp_path_factory.mktemp("repo")
    return write_layer(repo / "data" / "raw" / "events", repo)


def saved_urls(layer: SyntheticStore) -> set[str]:
    folder = layer.store.root / "sec-edgar" / "retrievals"
    return {
        Retrieval.model_validate_json(path.read_text()).request_url
        for path in folder.glob("*/*.json")
    }


@pytest.fixture(scope="module")
def read(layer) -> dict[str, Read]:
    manifest = load_manifest(COHORT)
    saved = SavedResponses(layer.store)
    return {
        issuer.issuer_id: read_issuer(saved, manifest, issuer)
        for issuer in manifest.issuers
        if issuer.issuer_id in manifest.candidate_issuer_ids
    }


EXCEPTIONS = {
    "cik-0009990001:2025-02-28": "several_release_filings",
    "cik-0009990002:2024-09-30": "same_day_transition",
    "cik-0009990002:2024-12-31": "not_member_at_publication",
    "cik-0009990002:2025-03-31": "not_member_at_publication",
    "cik-0009990005:2025-06-27": "no_release_filing",
    "cik-0009990006:2026-06-30": "not_member_at_publication",
}
"""Every other event is ``member_at_publication``."""


def test_every_event_s_reason_before_any_override(read) -> None:
    reasons = {k: v for issuer in read.values() for k, v in issuer.reasons.items()}
    assert len(reasons) == 32
    assert {k: v for k, v in reasons.items() if k in EXCEPTIONS} == EXCEPTIONS
    others = {v for k, v in reasons.items() if k not in EXCEPTIONS}
    assert others == {"member_at_publication"}
    assert sum(v == "member_at_publication" for v in reasons.values()) == 26


def test_nothing_is_missing_and_the_findings_are_the_layer_s(read) -> None:
    problems = [p for issuer in read.values() for p in issuer.filings.problems]
    problems += [
        p
        for issuer in read.values()
        for found in issuer.identified.values()
        for p in found.problems
    ]
    assert problems == []
    findings = sorted(
        f.finding_id
        for issuer in read.values()
        for f in (*issuer.filings.findings, *issuer.findings)
    )
    assert findings == [
        "fiscal_labels_unknown:cik-0009990003:2025-06-30",
        "period_gap:cik-0009990002:2025-03-31:2026-07-01",
        "period_gap:cik-0009990003:2024-07-01:2024-12-31",
        "period_gap:cik-0009990006:2025-03-31:2025-09-30",
    ]


def test_the_slots_follow_each_calendar(read) -> None:
    """Acme's May fiscal year trips no guard; Dynamo's two securities make one slot
    per period, and its 2026-07-03 period end lies outside the window."""
    ends = {k: [s.period_end for s in v.slots] for k, v in read.items()}
    assert ends["cik-0009990001"][0] == date(2024, 8, 31)
    assert ends["cik-0009990001"][-1] == date(2026, 5, 31)
    assert [len(v) for v in ends.values()] == [8, 3, 7, 7, 7]
    assert ends["cik-0009990005"][-1] == date(2026, 4, 3)
    assert read["cik-0009990005"].slots[-1].next_period_end == date(2026, 7, 3)


def test_each_release_is_identified_by_its_statements(read) -> None:
    methods = {
        event_id: (found.method and found.method.value)
        for issuer in read.values()
        for event_id, found in issuer.identified.items()
    }
    assert methods["cik-0009990005:2025-09-26"] == "sole_candidate"
    assert methods["cik-0009990003:2025-06-30"] == "sole_candidate"
    assert methods["cik-0009990001:2025-02-28"] is None
    assert methods["cik-0009990005:2025-06-27"] is None
    stated = {k for k, v in methods.items() if v == "stated_period"}
    assert len(stated) == 30 - 2


def test_the_preliminary_filing_is_dropped_and_the_gap_s_neighbor_too(read) -> None:
    fourth = read["cik-0009990005"].identified["cik-0009990005:2024-12-31"]
    assert [c.dropped for c in fourth.candidates] == [
        "it calls its results preliminary",
        None,
    ]
    first = read["cik-0009990006"].identified["cik-0009990006:2025-03-31"]
    assert [c.dropped for c in first.candidates] == [None, "it states another period"]


def test_exhibit_numbering_and_the_amendment(read) -> None:
    """Borealis' exhibit is typed EX-99 and Corvid's EX-99.01; Borealis' 8-K/A is
    recorded and never chosen."""
    borealis = read["cik-0009990002"].identified["cik-0009990002:2024-09-30"]
    assert [d.doc_type for d in borealis.release.placed.index.exhibits_99()] == [
        "EX-99"
    ]
    assert [p.filing.form for p in borealis.amendments] == ["8-K/A"]
    corvid = read["cik-0009990003"].identified["cik-0009990003:2024-12-31"]
    assert [d.doc_type for d in corvid.release.placed.index.exhibits_99()] == [
        "EX-99.01"
    ]


def test_the_conventions_and_the_older_pages(read) -> None:
    conventions = {
        k: {file.survey.convention for file in v.filings.files} for k, v in read.items()
    }
    assert conventions == {
        "cik-0009990001": {Convention.EASTERN_DIGITS},
        "cik-0009990002": {Convention.EASTERN_DIGITS},
        "cik-0009990003": {Convention.UTC},
        "cik-0009990005": {Convention.UTC},
        "cik-0009990006": {Convention.UTC},
    }
    eastfield = read["cik-0009990006"].filings
    assert [file.artifact.url for file in eastfield.files][1:] == [
        submissions_page_url("CIK0009990006-submissions-001.json")
    ]
    assert [page.url for page in eastfield.skipped] == [
        submissions_page_url("CIK0009990006-submissions-002.json")
    ]


def test_the_layer_holds_what_discovery_fetches_and_no_filing_after_the_cutoff(
    layer, read
) -> None:
    """Primary documents only of candidates; no exhibit; nothing accepted after the
    cutoff."""
    urls = saved_urls(layer)
    documents = {url for url in urls if "-8k-" in url}
    candidates = {
        archive_url(
            issuer.filings.cik,
            candidate.placed.filing.accession,
            candidate.placed.filing.primary_document,
        )
        for issuer in read.values()
        for found in issuer.identified.values()
        for candidate in found.candidates
    }
    assert documents == candidates
    assert not any("-ex" in url for url in urls)
    (late,) = [f for f, _ in filings(ACME) if f.accepted == "2026-09-24 16:05:00"]
    assert filing_index_url(ACME.cik, late.accession) not in urls
    acme = read["cik-0009990001"]
    assert date(2026, 8, 31) not in [slot.period_end for slot in acme.slots]


def test_the_layer_regenerates_byte_for_byte(layer, tmp_path) -> None:
    again = write_layer(tmp_path / "data" / "raw" / "events", tmp_path)
    first, second = layer.store.root, again.store.root
    files = sorted(p.relative_to(first) for p in first.rglob("*") if p.is_file())
    assert files == sorted(
        p.relative_to(second) for p in second.rglob("*") if p.is_file()
    )
    assert all((first / f).read_bytes() == (second / f).read_bytes() for f in files)
