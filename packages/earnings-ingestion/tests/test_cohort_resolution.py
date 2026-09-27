"""Issuer resolution: P-VF's ticker-history, multiple-security, and CIK cases."""

import json
from datetime import UTC, date, datetime

import pytest
from earnings_core import ArtifactRef, RightsStatus
from earnings_ingestion.cohort.locators import ArtifactText, CitableArtifact
from earnings_ingestion.cohort.records import (
    CitedIdentity,
    FindingKind,
    Override,
    OverrideCitation,
    OverrideKind,
    ResolutionMethod,
    ResolutionStatus,
    SecurityRecord,
)
from earnings_ingestion.cohort.resolution import SecEvidence, resolve
from earnings_ingestion.sec.data import read_company_tickers, read_submissions

TICKERS = {
    "0": {"cik_str": 9990001, "ticker": "ACME", "title": "Acme Industrial Corp"},
    "1": {"cik_str": 9990002, "ticker": "BORA", "title": "Borealis Air Inc"},
    "2": {"cik_str": 9990003, "ticker": "CRVD", "title": "Corvid Systems Inc"},
    "3": {"cik_str": 9990004, "ticker": "CRVD", "title": "Corvid Holdings"},
    "4": {"cik_str": 9990005, "ticker": "DYNA", "title": "Dynamo Motors"},
    "5": {"cik_str": 9990005, "ticker": "DYNB", "title": "Dynamo Motors"},
}
REGISTRANTS = {
    "9990001": ("Acme Industrial Corp", ["ACME"], []),
    "9990002": ("Borealis Air Inc", ["BORA"], ["Northern Airways Inc"]),
    "9990003": ("Corvid Systems Inc", ["CRVD"], []),
    "9990004": ("Corvid Systems Holdings", ["CRVD"], []),
    "9990005": ("Dynamo Motors Co", ["DYNA", "DYNB"], []),
    "9990006": ("Eastfield Bank Corp", ["EFB"], []),
}


def citable(body: bytes, url: str) -> CitableArtifact:
    return CitableArtifact(
        source_id="sec-edgar",
        url=url,
        artifact=ArtifactRef.for_bytes(
            body,
            media_type="application/json",
            storage_ref="data/raw/sec-edgar/x.json",
            rights_status=RightsStatus.LOCAL_ONLY,
            rights_basis="test",
        ),
        retrieved_at=datetime(2026, 9, 27, tzinfo=UTC),
        text=ArtifactText(body, "application/json"),
    )


def submissions(cik: str, name: str, tickers: list[str], former: list[str]) -> bytes:
    columns = ("accessionNumber", "filingDate", "reportDate", "acceptanceDateTime")
    recent = {column: [] for column in (*columns, "form", "primaryDocument")}
    data = {
        "cik": cik,
        "name": name,
        "tickers": tickers,
        "formerNames": [
            {
                "name": n,
                "from": "2001-01-01T00:00:00.000Z",
                "to": "2024-01-01T00:00:00.000Z",
            }
            for n in former
        ],
        "filings": {"recent": recent, "files": []},
    }
    return json.dumps(data).encode()


def sec_evidence() -> SecEvidence:
    body = json.dumps(TICKERS).encode()
    registrants = {}
    for cik, (name, tickers, former) in REGISTRANTS.items():
        raw = submissions(cik, name, tickers, former)
        registrants[f"{int(cik):010d}"] = (
            read_submissions(raw),
            citable(raw, f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"),
        )
    return SecEvidence(
        tickers=citable(body, "https://www.sec.gov/files/company_tickers.json"),
        ticker_entries=read_company_tickers(body),
        registrants=registrants,
    )


def security(security_id: str, *identities: tuple[str, str]) -> SecurityRecord:
    return SecurityRecord(
        security_id=security_id,
        identities=tuple(
            CitedIdentity(
                evidence_id=f"item-{index}",
                observed_on=date(2024, 6, 28 - index),
                name=name,
                ticker=ticker,
            )
            for index, (name, ticker) in enumerate(identities)
        ),
    )


def override(override_id: str, kind: OverrideKind, **targets) -> Override:
    return Override(
        override_id=override_id,
        kind=kind,
        citations=(OverrideCitation(source_id="sec-edgar", url="https://x.test/"),),
        rationale="Reviewed against the filings.",
        reviewer="Reviewer Name",
        recorded_on=date(2026, 9, 28),
        effective_from=date(2024, 7, 1),
        **targets,
    )


def run(securities, overrides=(), scope=None):
    scope = frozenset(s.security_id for s in securities) if scope is None else scope
    return resolve(securities, sec_evidence(), overrides, scope)


def test_a_listed_ticker_under_a_covering_name_resolves_to_a_padded_cik() -> None:
    result = run([security("acme-common", ("Acme Industrial", "ACME"))])
    (mapping,) = result.mappings
    assert (mapping.status, mapping.method) == (
        ResolutionStatus.RESOLVED,
        ResolutionMethod.SEC_TICKER_AND_NAME,
    )
    assert (mapping.cik, mapping.issuer_id) == ("0009990001", "cik-0009990001")
    tickers, filings = mapping.candidates[0].citations
    assert [locator.pointer for locator in tickers.locators] == ["/0"]
    assert [locator.pointer for locator in filings.locators] == ["/name", "/tickers"]
    assert result.findings == ()


def test_a_former_name_confirms_and_is_cited() -> None:
    result = run([security("borealis-common", ("Northern Airways", "BORA"))])
    (mapping,) = result.mappings
    assert mapping.cik == "0009990002"
    assert mapping.candidates[0].matched_name == "Northern Airways Inc"
    pointers = [loc.pointer for loc in mapping.candidates[0].citations[1].locators]
    assert pointers == ["/name", "/tickers", "/formerNames/0"]


def test_a_ticker_change_keeps_both_identities_and_resolves_once() -> None:
    record = security(
        "acme-common", ("Acme Industrial", "ACMX"), ("Acme Industrial", "ACME")
    )
    result = run([record])
    (mapping,) = result.mappings
    assert mapping.cik == "0009990001"
    assert [i.ticker for i in record.identities] == ["ACMX", "ACME"]


def test_two_securities_of_one_issuer_derive_one_issuer_row() -> None:
    result = run(
        [
            security("dynamo-class-a", ("Dynamo Motors", "DYNA")),
            security("dynamo-class-b", ("Dynamo Motors", "DYNB")),
        ]
    )
    (issuer,) = result.issuers
    assert issuer.cik == "0009990005"
    assert issuer.security_ids == ("dynamo-class-a", "dynamo-class-b")


def test_a_name_that_is_not_covered_leaves_it_unresolved_and_blocking() -> None:
    result = run([security("acme-common", ("ACI", "ACME"))])
    (mapping,) = result.mappings
    assert mapping.status is ResolutionStatus.UNRESOLVED
    assert mapping.cik is None
    (finding,) = result.findings
    assert (finding.kind, finding.holds_freeze) == (FindingKind.IDENTITY, True)


def test_an_unknown_ticker_is_unresolved_with_its_reason() -> None:
    (mapping,) = run([security("zeta-common", ("Zeta", "ZETA"))]).mappings
    assert mapping.reason == "SEC's ticker list has none of ZETA"


def test_two_confirmed_ciks_conflict() -> None:
    result = run([security("corvid-common", ("Corvid Systems", "CRVD"))])
    (mapping,) = result.mappings
    assert mapping.status is ResolutionStatus.CONFLICTING
    assert mapping.reason == "SEC confirms several CIKs: 0009990003, 0009990004"


def test_overrides_decide_and_resolve_the_finding() -> None:
    unresolved = security("acme-common", ("ACI", "ACME"))
    set_issuer = override(
        "acme-issuer",
        OverrideKind.SET_ISSUER,
        security_id="acme-common",
        cik="0009990001",
    )
    result = run([unresolved], [set_issuer])
    (mapping,) = result.mappings
    assert (mapping.method, mapping.override_id) == (
        ResolutionMethod.OVERRIDE,
        "acme-issuer",
    )
    assert result.findings[0].resolved_by == ("acme-issuer",)
    assert not result.findings[0].holds_freeze

    keep = override(
        "keep-zeta", OverrideKind.RETAIN_UNRESOLVED, security_id="zeta-common"
    )
    (kept,) = run([security("zeta-common", ("Zeta", "ZETA"))], [keep]).mappings
    assert kept.status is ResolutionStatus.RETAINED_UNRESOLVED
    assert kept.reason == "Reviewed against the filings."


def test_an_out_of_scope_security_does_not_block() -> None:
    result = run([security("zeta-common", ("Zeta", "ZETA"))], scope=frozenset())
    assert result.findings == ()


def test_a_proposed_cik_without_saved_submissions_stops_the_build() -> None:
    evidence = sec_evidence()
    evidence = SecEvidence(
        tickers=evidence.tickers,
        ticker_entries=evidence.ticker_entries,
        registrants={},
    )
    with pytest.raises(ValueError, match="run the SEC fetch"):
        resolve(
            [security("acme-common", ("Acme Industrial", "ACME"))],
            evidence,
            (),
            frozenset({"acme-common"}),
        )
