"""Dated snapshots compared with the reconstructed roster (P §Membership evidence).

A corroborating snapshot, a secondary roster or a fund's holdings, never adds or
removes a member: it is compared on its own date, and a disagreement is a blocking
``difference`` until a reviewer acknowledges that exact finding. A check list, or any
snapshot first published after the cutoff, is compared and reported only.

Fund holdings name companies, not securities. A holding matches the one security
whose cited name its name covers, or the security a ``holding_alias`` override names
(plan 6, P6-10); any other holding is listed as unmatched. For each report date, the
latest filing filed on or before the cutoff is compared, and earlier ones are
``superseded``.
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from earnings_ingestion.cohort.findings import make_finding
from earnings_ingestion.cohort.intervals import roster
from earnings_ingestion.cohort.locators import CitableArtifact
from earnings_ingestion.cohort.names import covered
from earnings_ingestion.cohort.records import (
    Citation,
    EvidenceClass,
    Finding,
    FindingKind,
    MembershipInterval,
    Override,
    OverrideKind,
    SecurityRecord,
    SnapshotReconciliation,
)
from earnings_ingestion.sec.data import Filing, HoldingsReport

EQUITY_COMMON = "EC"


@dataclass(frozen=True)
class FundFiling:
    """One saved N-PORT filing of the corroborating fund."""

    filing: Filing
    report: HoldingsReport
    artifact: CitableArtifact


def reconcile(
    snapshot_id: str,
    *,
    source_id: str,
    evidence_class: EvidenceClass,
    as_of: date,
    published_on: date,
    cutoff: date,
    listed: Iterable[str],
    unmatched: Iterable[str],
    intervals: Iterable[MembershipInterval],
    citation: Citation | None,
) -> SnapshotReconciliation:
    """``listed`` security ids compared with the roster on ``as_of``."""
    listed = set(listed)
    reconstructed = roster(intervals, as_of)
    return SnapshotReconciliation(
        snapshot_id=snapshot_id,
        source_id=source_id,
        evidence_class=evidence_class,
        as_of=as_of,
        published_on=published_on,
        withheld=published_on > cutoff,
        matched=tuple(sorted(listed & reconstructed)),
        reconstructed_only=tuple(sorted(reconstructed - listed)),
        snapshot_only=tuple(sorted(listed - reconstructed)),
        unmatched=tuple(sorted(set(unmatched))),
        citation=citation,
    )


def match_holdings(
    report: HoldingsReport,
    securities: Iterable[SecurityRecord],
    overrides: Iterable[Override],
) -> tuple[set[str], list[str]]:
    """The security ids a fund's common-equity holdings match, and the names of
    holdings that match no single security."""
    securities = tuple(securities)
    aliases = {
        o.holding_name: o.security_id
        for o in overrides
        if o.kind is OverrideKind.HOLDING_ALIAS
    }
    matched: set[str] = set()
    unmatched: list[str] = []
    for holding in report.holdings:
        if holding.asset_category not in (None, EQUITY_COMMON):
            continue
        if holding.name in aliases:
            matched.add(aliases[holding.name])
            continue
        found = {
            security.security_id
            for security in securities
            if any(covered(i.name, holding.name) for i in security.identities)
        }
        if len(found) == 1:
            matched |= found
        else:
            unmatched.append(holding.name)
    return matched, unmatched


def _order(fund: FundFiling) -> tuple[date, float, str]:
    accepted = fund.filing.accepted_at
    return (
        fund.filing.filing_date,
        accepted.timestamp() if accepted else 0.0,
        fund.filing.accession,
    )


def current_filings(
    filings: Iterable[FundFiling], cutoff: date
) -> tuple[list[FundFiling], list[Finding]]:
    """The filings to compare, and a ``superseded`` finding for each replaced one.

    Per report date, the latest filing filed on or before the cutoff is compared;
    filings after the cutoff are compared too, and reported as withheld.
    """
    by_date: dict[date, list[FundFiling]] = defaultdict(list)
    for filing in filings:
        by_date[filing.report.report_date].append(filing)
    current, findings = [], []
    for report_date in sorted(by_date):
        group = sorted(by_date[report_date], key=_order)
        timely = [f for f in group if f.filing.filing_date <= cutoff]
        current.extend(timely[-1:])
        current.extend(f for f in group if f.filing.filing_date > cutoff)
        for replaced in timely[:-1]:
            findings.append(
                make_finding(
                    FindingKind.SUPERSEDED,
                    replaced.filing.accession,
                    f"{replaced.filing.accession} ({replaced.filing.form}) for"
                    f" {report_date} is replaced by {timely[-1].filing.accession}",
                    blocking=False,
                )
            )
    return current, findings


def difference_findings(
    reconciliations: Iterable[SnapshotReconciliation],
) -> tuple[Finding, ...]:
    """A finding for each disagreeing snapshot; blocking unless it is a check list
    or was first published after the cutoff."""
    findings = []
    for r in reconciliations:
        if r.agrees:
            continue
        parts = [
            f"reconstruction only: {', '.join(r.reconstructed_only) or 'none'}",
            f"snapshot only: {', '.join(r.snapshot_only) or 'none'}",
            f"unmatched: {', '.join(r.unmatched) or 'none'}",
        ]
        findings.append(
            make_finding(
                FindingKind.DIFFERENCE,
                r.snapshot_id,
                f"{r.snapshot_id} on {r.as_of}: {'; '.join(parts)}",
                blocking=not r.withheld
                and r.evidence_class is not EvidenceClass.USER_SUPPLIED,
                evidence_ids=[r.snapshot_id],
            )
        )
    return tuple(findings)


def _quarter(day: date) -> tuple[int, int]:
    return day.year, (day.month - 1) // 3 + 1


def gap_findings(
    reconciliations: Iterable[SnapshotReconciliation], *, start: date, cutoff: date
) -> tuple[Finding, ...]:
    """A ``gap`` for each calendar quarter from ``start`` through ``cutoff`` with no
    timely corroborating snapshot."""
    covered_quarters = {
        _quarter(r.as_of)
        for r in reconciliations
        if not r.withheld and r.evidence_class is not EvidenceClass.USER_SUPPLIED
    }
    findings = []
    year, quarter = _quarter(start)
    while (year, quarter) <= _quarter(cutoff):
        if (year, quarter) not in covered_quarters:
            findings.append(
                make_finding(
                    FindingKind.GAP,
                    f"{year}q{quarter}",
                    f"no corroborating snapshot is dated in {year}Q{quarter}",
                    blocking=False,
                )
            )
        year, quarter = (year + 1, 1) if quarter == 4 else (year, quarter + 1)
    return tuple(findings)
