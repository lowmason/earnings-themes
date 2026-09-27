"""Slots, their guards, and their fiscal labels (the Stage 5 spec, §Slots, step 1).

- **Slots.** One per candidate issuer and period end. A period end is a distinct
  ``reportDate`` among the issuer's original 10-Q, 10-K, 10-QT, and 10-KT filings that
  were accepted by the cutoff, and a slot's lies in ``[start, stop)``. Amendments never
  make slots, so period ends are reported by the source, never inferred. When two
  original reports share a period end, the earlier filed makes the slot.
- **Labels** (EV6). A slot's ``reported_fiscal_year`` and ``reported_fiscal_quarter``
  are companyfacts' ``fy`` and ``fp`` for its periodic report, as written. Missing or
  disagreeing labels stay null, with a non-blocking ``fiscal_labels_unknown``.
- **Guards.** Each is a blocking finding that an ``acknowledge`` override answers.
  ``period_gap`` fires when an in-window period end may be missing:
  1. two consecutive visible period ends, at least one inside the window, lie more
     than 105 days apart;
  2. no visible period end precedes the first in-window one, which lies 92 or more
     days after ``start``;
  3. no visible period end follows the last in-window one, which lies more than 91
     days before ``stop``.

  The window's edges are judged by quarter length, never by filing lag, so a
  calendar like Nike's, whose next report is due after the cutoff, trips none.
  ``no_slots`` fires when a candidate issuer has no slot.
"""

from dataclasses import dataclass
from datetime import date
from itertools import pairwise

from earnings_ingestion.events.filings import IssuerFilings, Placed
from earnings_ingestion.events.records import (
    EventFinding,
    EventFindingKind,
    event_finding,
)
from earnings_ingestion.sec.companyfacts import CompanyFacts, FiscalLabels

LONGEST_GAP_DAYS = 105
FIRST_EDGE_DAYS = 92
LAST_EDGE_DAYS = 91


@dataclass(frozen=True)
class Slot:
    """One issuer's period end, the report that made it, and its labels."""

    issuer_id: str
    cik: str
    period_end: date
    periodic: Placed
    next_period_end: date | None
    """P': the issuer's next visible period end, if one is visible."""
    labels: FiscalLabels | None

    @property
    def event_id(self) -> str:
        return f"{self.issuer_id}:{self.period_end.isoformat()}"


def _gap(issuer_id: str, since: date, until: date, detail: str) -> EventFinding:
    return event_finding(
        EventFindingKind.PERIOD_GAP,
        f"{issuer_id}:{since.isoformat()}:{until.isoformat()}",
        detail,
        issuer_id=issuer_id,
    )


def issuer_slots(
    filings: IssuerFilings,
    facts: CompanyFacts,
    issuer_id: str,
    *,
    start: date,
    stop: date,
) -> tuple[tuple[Slot, ...], tuple[EventFinding, ...]]:
    """The issuer's slots, and the findings of its guards and labels."""
    reports: dict[date, Placed] = {}
    for placed in sorted(
        filings.periodic, key=lambda p: (p.filing.filing_date, p.filing.accession)
    ):
        reports.setdefault(placed.filing.report_date, placed)
    ends = sorted(reports)
    inside = [end for end in ends if start <= end < stop]
    findings = []
    if not inside:
        findings.append(
            event_finding(
                EventFindingKind.NO_SLOTS,
                issuer_id,
                "no original periodic report with a period end in"
                f" [{start}, {stop}) was accepted by the cutoff",
                issuer_id=issuer_id,
            )
        )
    for before, after in pairwise(ends):
        days = (after - before).days
        if (start <= before < stop or start <= after < stop) and (
            days > LONGEST_GAP_DAYS
        ):
            findings.append(
                _gap(
                    issuer_id,
                    before,
                    after,
                    f"no period end is visible between {before} and {after},"
                    f" {days} days apart",
                )
            )
    if inside:
        first, last = inside[0], inside[-1]
        if ends[0] == first and (first - start).days >= FIRST_EDGE_DAYS:
            findings.append(
                _gap(
                    issuer_id,
                    start,
                    first,
                    f"no period end is visible before {first},"
                    f" {(first - start).days} days after the window's start {start}",
                )
            )
        if ends[-1] == last and (stop - last).days > LAST_EDGE_DAYS:
            findings.append(
                _gap(
                    issuer_id,
                    last,
                    stop,
                    f"no period end is visible after {last},"
                    f" {(stop - last).days} days before the window's stop {stop}",
                )
            )
    slots = []
    for end in inside:
        placed = reports[end]
        accession = placed.filing.accession
        later = [other for other in ends if other > end]
        slot = Slot(
            issuer_id=issuer_id,
            cik=filings.cik,
            period_end=end,
            periodic=placed,
            next_period_end=later[0] if later else None,
            labels=facts.labels.get(accession),
        )
        if slot.labels is None:
            detail = (
                f"companyfacts' facts of {accession} disagree on fy and fp, or"
                " leave one out"
                if accession in facts.labels
                else f"companyfacts holds no fact of {accession}"
            )
            findings.append(
                event_finding(
                    EventFindingKind.FISCAL_LABELS_UNKNOWN,
                    slot.event_id,
                    detail,
                    issuer_id=issuer_id,
                )
            )
        slots.append(slot)
    return tuple(slots), tuple(sorted(findings, key=lambda f: f.finding_id))
