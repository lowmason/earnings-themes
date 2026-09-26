"""Corroboration: snapshots compared on their dates, never used as the roster."""

from datetime import UTC, date, datetime

from earnings_ingestion.cohort.corroboration import (
    FundFiling,
    current_filings,
    difference_findings,
    gap_findings,
    match_holdings,
    reconcile,
)
from earnings_ingestion.cohort.records import (
    BoundBasis,
    BoundTiming,
    CitedIdentity,
    EvidenceClass,
    FindingKind,
    MembershipInterval,
    Override,
    OverrideKind,
    SecurityRecord,
)
from earnings_ingestion.sec.data import Filing, Holding, HoldingsReport

CUTOFF = date(2026, 9, 22)


def interval(security_id: str, start: date, end: date | None = None):
    return MembershipInterval(
        security_id=security_id,
        effective_from=start,
        effective_from_basis=BoundBasis.ANNOUNCED,
        effective_from_timing=BoundTiming.BEFORE_OPEN,
        effective_to=end,
        effective_to_timing=None if end is None else BoundTiming.BEFORE_OPEN,
        assertion_ids=("a",),
    )


INTERVALS = (
    interval("acme-common", date(2024, 6, 28)),
    interval("borealis-common", date(2024, 6, 28), date(2024, 11, 8)),
    interval("corvid-common", date(2024, 11, 8)),
)
SECURITIES = tuple(
    SecurityRecord(
        security_id=security_id,
        identities=(
            CitedIdentity(
                evidence_id="anchor",
                observed_on=date(2024, 6, 28),
                name=name,
                ticker=ticker,
            ),
        ),
    )
    for security_id, name, ticker in [
        ("acme-common", "Acme Industrial", "ACME"),
        ("borealis-common", "Borealis Air", "BORA"),
        ("corvid-common", "Corvid Systems", "CRVD"),
    ]
)


def compare(listed, as_of, *, published=None, cls=EvidenceClass.SECONDARY):
    return reconcile(
        "snapshot",
        source_id="synthetic-roster",
        evidence_class=cls,
        as_of=as_of,
        published_on=published or as_of,
        cutoff=CUTOFF,
        listed=listed,
        unmatched=(),
        intervals=INTERVALS,
        citation=None,
    )


def test_an_agreeing_snapshot_raises_nothing() -> None:
    result = compare({"acme-common", "corvid-common"}, date(2025, 1, 31))
    assert result.agrees
    assert difference_findings([result]) == ()


def test_a_disagreeing_snapshot_blocks_until_acknowledged() -> None:
    result = compare({"acme-common", "borealis-common"}, date(2025, 1, 31))
    assert (result.reconstructed_only, result.snapshot_only) == (
        ("corvid-common",),
        ("borealis-common",),
    )
    (finding,) = difference_findings([result])
    assert finding.kind is FindingKind.DIFFERENCE
    assert finding.holds_freeze


def test_late_snapshots_and_check_lists_are_reported_only() -> None:
    late = compare({"acme-common"}, date(2026, 9, 1), published=date(2026, 9, 26))
    check = compare({"acme-common"}, date(2026, 9, 1), cls=EvidenceClass.USER_SUPPLIED)
    assert late.withheld
    assert [f.blocking for f in difference_findings([late, check])] == [False, False]


def report(*names: str, category: str | None = "EC") -> HoldingsReport:
    return HoldingsReport(
        report_date=date(2025, 1, 31),
        holdings=tuple(
            Holding(name=n, title=None, asset_category=category, position=i)
            for i, n in enumerate(names, start=1)
        ),
    )


def test_holdings_match_by_covering_name_or_a_reviewed_alias() -> None:
    alias = Override(
        override_id="corvid-alias",
        kind=OverrideKind.HOLDING_ALIAS,
        security_id="corvid-common",
        holding_name="CSI Holdings",
        citations=(),
        rationale="The fund's name for Corvid Systems.",
        reviewer="Reviewer Name",
        recorded_on=date(2026, 9, 28),
        effective_from=date(2024, 7, 1),
    )
    holdings = report("Acme Industrial Corp", "CSI Holdings", "Unknown Co")
    matched, unmatched = match_holdings(holdings, SECURITIES, [alias])
    assert matched == {"acme-common", "corvid-common"}
    assert unmatched == ["Unknown Co"]


def test_non_equity_holdings_are_not_members() -> None:
    matched, unmatched = match_holdings(report("Cash", category="STIV"), SECURITIES, [])
    assert (matched, unmatched) == (set(), [])


def filing(accession: str, filed: date, form: str = "NPORT-P") -> FundFiling:
    return FundFiling(
        filing=Filing(
            accession=accession,
            form=form,
            filing_date=filed,
            report_date=date(2025, 1, 31),
            accepted_at=datetime.combine(filed, datetime.min.time(), tzinfo=UTC),
            primary_document="primary_doc.xml",
            columns="/filings/recent",
            index=0,
        ),
        report=report("Acme Industrial Corp"),
        artifact=None,
    )


def test_an_amendment_supersedes_and_a_late_filing_is_kept_apart() -> None:
    original = filing("0009990009-25-000001", date(2025, 3, 28))
    amended = filing("0009990009-25-000002", date(2025, 4, 2), "NPORT-P/A")
    late = filing("0009990009-26-000009", date(2026, 9, 30), "NPORT-P/A")
    current, findings = current_filings([late, original, amended], CUTOFF)
    assert [f.filing.accession for f in current] == [
        "0009990009-25-000002",
        "0009990009-26-000009",
    ]
    (superseded,) = findings
    assert superseded.finding_id == "superseded:0009990009-25-000001"
    assert not superseded.blocking


def test_every_uncorroborated_quarter_is_a_gap() -> None:
    covered = [compare({"acme-common", "corvid-common"}, date(2025, 1, 31))]
    gaps = gap_findings(covered, start=date(2024, 7, 1), cutoff=date(2025, 6, 30))
    assert [f.finding_id for f in gaps] == ["gap:2024q3", "gap:2024q4", "gap:2025q2"]
    assert not any(f.blocking for f in gaps)
