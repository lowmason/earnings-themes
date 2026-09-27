"""The synthetic event layer (the Stage 5 spec, §The synthetic event layer; plan 7,
P7-17).

``write_layer(root, repo)`` saves, under ``root``, every response that discovery would
fetch for the synthetic cohort's five candidate issuers, all retrieved at
``RETRIEVED``:

- each submissions file, and each older page whose dates meet the range;
- each companyfacts file;
- the index page of every Item 2.02 8-K and 8-K/A that either convention places in
  ``[2024-07-01, 2026-09-22]``;
- the primary document of every candidate.

It saves no exhibit (EV2). Every company, filing, and word is invented; each case
takes its shape from the real filings plan 7 read, never their wording.

``review(first)`` gives the overrides a reviewer records against the layer's first
build: three acknowledged period gaps, Acme's release set by review, and two events
retained unresolved.

The cases, by issuer:

- **Acme Industrial**, a fiscal year ending in May like Nike's, which trips no guard.
  Its submissions give Eastern digits. The quarter ended 2025-02-28 has two
  candidates the rule cannot separate, a sale's effect on the quarter and the
  release. A release and a 10-Q accepted after the cutoff are never read.
- **Borealis Air** leaves the index before the open on 2024-11-08, and releases its
  third quarter at 07:00 that day, a ``same_day_transition``. Its exhibit is typed
  ``EX-99``, and an 8-K/A follows. It is acquired and files nothing after its report
  for 2025-03-31, so no period end follows it: the third ``period_gap`` case.
- **Corvid Systems** joins on 2024-11-08, and its first periodic report covers
  2024-12-31: the second ``period_gap`` case. Its exhibits are typed ``EX-99.01``.
  Its labels for 2025-06-30 disagree, and that quarter's only ``EX-99`` is a pro forma
  overview, like V2's AMC case, for plan B.
- **Dynamo Motors** holds two securities and makes one slot per period. Its calendar
  ends 2026-07-03, outside the window. Its fourth quarter of 2024 has a preliminary
  filing and then the release. Its quarter ended 2025-06-27 has no candidate, and its
  release for 2025-09-26 is narrative-only.
- **Eastfield Bank** leaves on 2026-06-22. It has no 10-Q for 2025-06-30, the first
  ``period_gap`` case. Its submissions give true UTC. One older page is read, and one
  is skipped by its dates.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from earnings_ingestion.cohort.records import OverrideCitation
from earnings_ingestion.cohort.register import SEC_SOURCE_ID
from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.events.records import (
    EventOverride,
    EventOverrideKind,
    EventReason,
)
from earnings_ingestion.events.synthetic import (
    SyntheticFiling,
    SyntheticStore,
    eight_k,
    older_page_entry,
)

if TYPE_CHECKING:
    from earnings_ingestion.events.build import EventBuild

RETRIEVED = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
REVIEWER = "Synthetic Reviewer"
REVIEWED_ON = date(2026, 9, 28)


@dataclass(frozen=True)
class Registrant:
    cik: str
    name: str
    stem: str
    """The prefix of its documents' file names."""
    convention: Convention


@dataclass(frozen=True)
class Report:
    """An original periodic report, and the labels its companyfacts facts state."""

    form: str
    period: date
    accepted: str
    labels: tuple[tuple[int, str], ...]


@dataclass(frozen=True)
class Release:
    """An 8-K. ``text`` is its Item 2.02 section; ``None`` when discovery never
    fetches its document, because it is no candidate."""

    accepted: str
    text: tuple[str, ...] | None
    items: tuple[str, ...] = ("2.02", "9.01")
    form: str = "8-K"
    exhibit: tuple[str, str] = ("EX-99.1", "Earnings release")
    """The index page's only exhibit: its type and description."""
    other: tuple[tuple[str, tuple[str, ...]], ...] = ()
    """The document's other items, before 9.01."""


ACME = Registrant(
    "0009990001", "Acme Industrial Corp", "acme", Convention.EASTERN_DIGITS
)
BOREALIS = Registrant(
    "0009990002", "Borealis Air Inc", "bora", Convention.EASTERN_DIGITS
)
CORVID = Registrant("0009990003", "Corvid Systems Inc", "crvd", Convention.UTC)
DYNAMO = Registrant("0009990005", "Dynamo Motors Co", "dyna", Convention.UTC)
EASTFIELD = Registrant("0009990006", "Eastfield Bank Corp", "efb", Convention.UTC)
REGISTRANTS = (ACME, BOREALIS, CORVID, DYNAMO, EASTFIELD)


def _q(form: str, period: str, accepted: str, *labels: tuple[int, str]) -> Report:
    return Report(form, date.fromisoformat(period), accepted, labels)


def _said(name: str, phrase: str, exhibit: str = "99.1") -> tuple[str, ...]:
    return (
        f"{name} announced {phrase}, in the release furnished as Exhibit {exhibit}.",
    )


REPORTS = {
    ACME: (
        _q("10-K", "2024-05-31", "2024-07-25 16:15:00", (2024, "FY")),
        _q("10-Q", "2024-08-31", "2024-10-08 16:10:00", (2025, "Q1")),
        _q("10-Q", "2024-11-30", "2025-01-07 16:10:00", (2025, "Q2")),
        _q("10-Q", "2025-02-28", "2025-04-08 16:10:00", (2025, "Q3")),
        _q("10-K", "2025-05-31", "2025-07-24 16:15:00", (2025, "FY")),
        _q("10-Q", "2025-08-31", "2025-10-07 16:10:00", (2026, "Q1")),
        _q("10-Q", "2025-11-30", "2026-01-06 16:10:00", (2026, "Q2")),
        _q("10-Q", "2026-02-28", "2026-04-07 16:10:00", (2026, "Q3")),
        _q("10-K", "2026-05-31", "2026-07-23 16:15:00", (2026, "FY")),
        _q("10-Q", "2026-08-31", "2026-09-25 16:10:00", (2027, "Q1")),
    ),
    BOREALIS: (
        _q("10-Q", "2024-06-30", "2024-08-02 16:20:00", (2024, "Q2")),
        _q("10-Q", "2024-09-30", "2024-11-12 16:20:00", (2024, "Q3")),
        _q("10-K", "2024-12-31", "2025-02-20 16:30:00", (2024, "FY")),
        _q("10-Q", "2025-03-31", "2025-05-02 16:20:00", (2025, "Q1")),
    ),
    CORVID: (
        _q("10-K", "2024-12-31", "2025-03-03 16:30:00", (2024, "FY")),
        _q("10-Q", "2025-03-31", "2025-05-06 16:30:00", (2025, "Q1")),
        _q("10-Q", "2025-06-30", "2025-08-05 16:30:00", (2025, "Q2"), (2025, "Q3")),
        _q("10-Q", "2025-09-30", "2025-11-04 16:30:00", (2025, "Q3")),
        _q("10-K", "2025-12-31", "2026-02-24 16:30:00", (2025, "FY")),
        _q("10-Q", "2026-03-31", "2026-05-05 16:30:00", (2026, "Q1")),
        _q("10-Q", "2026-06-30", "2026-08-04 16:30:00", (2026, "Q2")),
    ),
    DYNAMO: (
        _q("10-Q", "2024-06-28", "2024-07-30 16:30:00", (2024, "Q2")),
        _q("10-Q", "2024-09-27", "2024-10-29 16:30:00", (2024, "Q3")),
        _q("10-K", "2024-12-31", "2025-02-24 16:30:00", (2024, "FY")),
        _q("10-Q", "2025-03-28", "2025-04-29 16:30:00", (2025, "Q1")),
        _q("10-Q", "2025-06-27", "2025-07-29 16:30:00", (2025, "Q2")),
        _q("10-Q", "2025-09-26", "2025-10-28 16:30:00", (2025, "Q3")),
        _q("10-K", "2025-12-31", "2026-02-23 16:30:00", (2025, "FY")),
        _q("10-Q", "2026-04-03", "2026-05-05 16:30:00", (2026, "Q1")),
        _q("10-Q", "2026-07-03", "2026-08-04 16:30:00", (2026, "Q2")),
    ),
    EASTFIELD: (
        _q("10-Q", "2024-03-31", "2024-05-03 16:30:00", (2024, "Q1")),
        _q("10-Q", "2024-06-30", "2024-08-02 16:30:00", (2024, "Q2")),
        _q("10-Q", "2024-09-30", "2024-11-01 16:30:00", (2024, "Q3")),
        _q("10-K", "2024-12-31", "2025-02-27 16:30:00", (2024, "FY")),
        _q("10-Q", "2025-03-31", "2025-05-02 16:30:00", (2025, "Q1")),
        _q("10-Q", "2025-09-30", "2025-10-31 16:30:00", (2025, "Q3")),
        _q("10-K", "2025-12-31", "2026-02-26 16:30:00", (2025, "FY")),
        _q("10-Q", "2026-03-31", "2026-05-01 16:30:00", (2026, "Q1")),
        _q("10-Q", "2026-06-30", "2026-07-31 16:30:00", (2026, "Q2")),
    ),
}

_ACME = "Acme Industrial Corp"
_BOREALIS = "Borealis Air Inc"
_CORVID = "Corvid Systems Inc"
_DYNAMO = "Dynamo Motors Co"
_EASTFIELD = "Eastfield Bank Corp"
_BOREALIS_EXHIBIT = ("EX-99", "Earnings release")
_CORVID_EXHIBIT = ("EX-99.01", "Earnings release")

RELEASES = {
    ACME: (
        Release("2024-06-27 16:05:00", None),
        Release(
            "2024-09-26 16:05:00",
            _said(_ACME, "its results for the first quarter of fiscal 2025"),
        ),
        Release(
            "2024-12-19 16:05:00",
            _said(_ACME, "its results for the second quarter of fiscal 2025"),
        ),
        Release(
            "2025-03-11 08:00:00",
            (
                (
                    f"{_ACME} agreed to sell its Tooling division. It estimates that"
                    " the sale will add $0.12 to diluted earnings per share for the"
                    " third quarter of fiscal 2025."
                ),
            ),
            items=("2.02", "8.01", "9.01"),
            exhibit=("EX-99.1", "Press release"),
            other=(("8.01", ("The sale awaits regulatory approval.",)),),
        ),
        Release(
            "2025-03-20 16:05:00",
            _said(_ACME, "its results for the third quarter of fiscal 2025"),
        ),
        Release(
            "2025-06-26 16:05:00",
            _said(_ACME, "its fiscal 2025 fourth quarter and full year results"),
        ),
        Release(
            "2025-09-25 16:05:00",
            _said(_ACME, "its results for the first quarter of fiscal 2026"),
        ),
        Release(
            "2025-12-18 16:05:00",
            _said(_ACME, "its results for the second quarter of fiscal 2026"),
        ),
        Release(
            "2026-03-19 16:05:00",
            _said(_ACME, "its results for the third quarter of fiscal 2026"),
        ),
        Release(
            "2026-06-25 16:05:00",
            _said(_ACME, "its results for the fiscal year ended May 31, 2026"),
        ),
        Release("2026-09-24 16:05:00", None),
    ),
    BOREALIS: (
        Release("2024-07-25 07:00:00", None, exhibit=_BOREALIS_EXHIBIT),
        Release(
            "2024-11-08 07:00:00",
            _said(
                _BOREALIS, "its results for the quarter ended September 30, 2024", "99"
            ),
            exhibit=_BOREALIS_EXHIBIT,
        ),
        Release("2024-11-12 09:00:00", None, form="8-K/A", exhibit=_BOREALIS_EXHIBIT),
        Release(
            "2025-02-06 07:00:00",
            _said(_BOREALIS, "its fourth quarter and full year 2024 results", "99"),
            exhibit=_BOREALIS_EXHIBIT,
        ),
        Release(
            "2025-04-24 07:00:00",
            _said(_BOREALIS, "its results for the first quarter of 2025", "99"),
            exhibit=_BOREALIS_EXHIBIT,
        ),
    ),
    CORVID: (
        Release(
            "2025-02-13 16:05:00",
            _said(_CORVID, "its full-year 2024 results", "99.01"),
            exhibit=_CORVID_EXHIBIT,
        ),
        Release(
            "2025-04-30 16:05:00",
            _said(_CORVID, "its Q1 2025 results", "99.01"),
            exhibit=_CORVID_EXHIBIT,
        ),
        Release(
            "2025-07-30 16:05:00",
            _said(_CORVID, "its second quarter of 2025 results", "99.01"),
            exhibit=("EX-99.01", "Pro forma overview"),
        ),
        Release(
            "2025-10-29 16:05:00",
            _said(_CORVID, "its third-quarter 2025 results", "99.01"),
            exhibit=_CORVID_EXHIBIT,
        ),
        Release(
            "2026-02-12 16:05:00",
            _said(_CORVID, "its fourth quarter and full year 2025 results", "99.01"),
            exhibit=_CORVID_EXHIBIT,
        ),
        Release(
            "2026-04-29 16:05:00",
            _said(_CORVID, "its first quarter of 2026 results", "99.01"),
            exhibit=_CORVID_EXHIBIT,
        ),
        Release(
            "2026-07-29 16:05:00",
            _said(_CORVID, "its results for the quarter ended June 30, 2026", "99.01"),
            exhibit=_CORVID_EXHIBIT,
        ),
    ),
    DYNAMO: (
        Release("2024-07-23 06:45:00", None),
        Release(
            "2024-10-22 06:45:00",
            _said(_DYNAMO, "its third quarter of 2024 earnings"),
        ),
        Release(
            "2025-01-13 08:00:00",
            (
                (
                    f"{_DYNAMO} shared preliminary fourth quarter of 2024 deliveries;"
                    " they appear in Exhibit 99.1."
                ),
            ),
        ),
        Release(
            "2025-02-11 06:45:00",
            _said(_DYNAMO, "its fourth quarter and full year 2024 earnings"),
        ),
        Release(
            "2025-04-22 06:45:00",
            _said(_DYNAMO, "its first quarter of 2025 earnings"),
        ),
        Release("2025-07-22 06:45:00", None, items=("7.01", "9.01")),
        Release(
            "2025-10-21 06:45:00",
            (f"{_DYNAMO} furnished its quarterly earnings release as Exhibit 99.1.",),
        ),
        Release(
            "2026-02-10 06:45:00",
            _said(_DYNAMO, "its fourth quarter and full year 2025 earnings"),
        ),
        Release(
            "2026-04-28 06:45:00",
            _said(_DYNAMO, "its first quarter of 2026 earnings"),
        ),
        Release("2026-07-21 06:45:00", None),
    ),
    EASTFIELD: (
        Release("2024-04-19 07:30:00", None),
        Release("2024-07-19 07:30:00", None),
        Release(
            "2024-10-18 07:30:00",
            _said(_EASTFIELD, "third quarter 2024 earnings"),
        ),
        Release(
            "2025-01-17 07:30:00",
            _said(_EASTFIELD, "fourth quarter and full year 2024 earnings"),
        ),
        Release(
            "2025-04-17 07:30:00",
            _said(_EASTFIELD, "first quarter of 2025 earnings"),
        ),
        Release(
            "2025-07-18 07:30:00",
            _said(_EASTFIELD, "second quarter of 2025 earnings"),
        ),
        Release(
            "2025-10-17 07:30:00",
            _said(_EASTFIELD, "third quarter of 2025 earnings"),
        ),
        Release(
            "2026-01-16 07:30:00",
            _said(_EASTFIELD, "fourth quarter and full year 2025 earnings"),
        ),
        Release(
            "2026-04-17 07:30:00",
            _said(_EASTFIELD, "first quarter 2026 earnings"),
        ),
        Release(
            "2026-07-17 07:30:00",
            _said(_EASTFIELD, "second quarter of 2026 earnings"),
        ),
    ),
}

OLDER_PAGES = {
    EASTFIELD: (
        ("CIK0009990006-submissions-001.json", "2024-07-01", "2025-01-01"),
        ("CIK0009990006-submissions-002.json", "2023-01-01", "2024-07-01"),
    ),
}
"""Each older page's name, and the acceptance dates ``[from, to)`` of its filings;
the rest are in the submissions file."""

START, CUTOFF = date(2024, 7, 1), date(2026, 9, 22)


def filings(
    registrant: Registrant,
) -> list[tuple[SyntheticFiling, Report | Release]]:
    """The registrant's filings, numbered in the order accepted."""
    entries = sorted(
        [*REPORTS[registrant], *RELEASES[registrant]], key=lambda e: e.accepted
    )
    filings = []
    for number, entry in enumerate(entries, start=1):
        day = date.fromisoformat(entry.accepted[:10])
        if isinstance(entry, Report):
            filing = SyntheticFiling(
                accession=f"{registrant.cik}-{day:%y}-{number:06d}",
                form=entry.form,
                filing_date=day,
                accepted=entry.accepted,
                report_date=entry.period,
                primary_document=f"{registrant.stem}-{entry.period:%Y%m%d}.htm",
            )
        else:
            suffix = "a" if entry.form == "8-K/A" else ""
            filing = SyntheticFiling(
                accession=f"{registrant.cik}-{day:%y}-{number:06d}",
                form=entry.form,
                filing_date=day,
                accepted=entry.accepted,
                report_date=day,
                items=entry.items,
                primary_document=f"{registrant.stem}-8k-{day:%Y%m%d}{suffix}.htm",
            )
        filings.append((filing, entry))
    return filings


def _exhibit(registrant: Registrant, filing: SyntheticFiling, release: Release):
    kind, description = release.exhibit
    digits = kind.removeprefix("EX-").replace(".", "")
    name = f"{registrant.stem}-{filing.filing_date:%Y%m%d}-ex{digits}.htm"
    return ((description, name, kind),)


def _in_range(filing: SyntheticFiling) -> bool:
    """Either convention's Eastern date lies in ``[START, CUTOFF]``. Every time here
    lies between 06:00 and 19:00 Eastern, where both readings give its own date."""
    return START <= date.fromisoformat(filing.accepted[:10]) <= CUTOFF


def write_layer(root: Path, repo: Path) -> SyntheticStore:
    """Save the layer's responses under ``root``; ``repo`` holds ``root``."""
    store = SyntheticStore(root, repo, RETRIEVED)
    for registrant in REGISTRANTS:
        listed = filings(registrant)
        pages = OLDER_PAGES.get(registrant, ())
        paged = set()
        entries = []
        for name, since, until in pages:
            inside = [
                filing for filing, _ in listed if since <= filing.accepted[:10] < until
            ]
            paged.update(filing.accession for filing in inside)
            entries.append(older_page_entry(name, inside))
            if START <= date.fromisoformat(entries[-1]["filingTo"]) and (
                date.fromisoformat(entries[-1]["filingFrom"]) <= CUTOFF
            ):
                store.older_page(name, inside, convention=registrant.convention)
        recent = [filing for filing, _ in listed if filing.accession not in paged]
        store.submissions(
            registrant.cik,
            registrant.name,
            recent,
            convention=registrant.convention,
            older_pages=entries,
        )
        facts = [
            (filing.accession, year, period)
            for filing, entry in listed
            if isinstance(entry, Report)
            for year, period in entry.labels
        ]
        store.companyfacts(registrant.cik, registrant.name, facts)
        for filing, entry in listed:
            if isinstance(entry, Report) or "2.02" not in entry.items:
                continue
            if not _in_range(filing):
                continue
            store.index(registrant.cik, filing, _exhibit(registrant, filing, entry))
            if entry.text is None:
                continue
            number = entry.exhibit[0].removeprefix("EX-")
            items = [
                ("2.02", entry.text),
                *entry.other,
                ("9.01", (f"Exhibit {number}: {entry.exhibit[1]}.",)),
            ]
            body = eight_k(registrant.name, items, signed=filing.filing_date)
            store.document(registrant.cik, filing, body)
    return store


def _override(
    override_id: str, kind: EventOverrideKind, rationale: str, **fields
) -> EventOverride:
    return EventOverride(
        override_id=override_id,
        kind=kind,
        **fields,
        rationale=rationale,
        reviewer=REVIEWER,
        recorded_on=REVIEWED_ON,
    )


GAPS = {
    "gap-borealis": (
        "period_gap:cik-0009990002:2025-03-31:2026-07-01",
        (
            "Borealis Air was acquired, and files nothing after its report for"
            " 2025-03-31."
        ),
    ),
    "gap-corvid": (
        "period_gap:cik-0009990003:2024-07-01:2024-12-31",
        (
            "Corvid Systems registered late in 2024; its first periodic report"
            " covers 2024-12-31."
        ),
    ),
    "gap-eastfield": (
        "period_gap:cik-0009990006:2025-03-31:2025-09-30",
        "Eastfield Bank filed no 10-Q for the quarter ended 2025-06-30.",
    ),
}


def review(first: "EventBuild") -> tuple[EventOverride, ...]:
    """The overrides a reviewer records against the layer's first build, sorted."""
    digests = {finding.finding_id: finding.digest for finding in first.findings}
    overrides = [
        _override(
            override_id,
            EventOverrideKind.ACKNOWLEDGE,
            rationale,
            finding_id=finding_id,
            finding_digest=digests[finding_id],
        )
        for override_id, (finding_id, rationale) in GAPS.items()
    ]
    (release,) = [
        placed
        for placed in first.issuers["cik-0009990001"].releases
        if placed.index.accepted == "2025-03-20 16:05:00"
    ]
    page = release.index_artifact
    overrides.append(
        _override(
            "release-acme-2025-02-28",
            EventOverrideKind.SET_RELEASE_FILING,
            "The 8-K of 2025-03-11 estimates a sale's effect on the quarter; the"
            " 8-K of 2025-03-20 furnishes the quarter's results.",
            event_id="cik-0009990001:2025-02-28",
            accession=release.filing.accession,
            citations=(
                OverrideCitation(
                    source_id=SEC_SOURCE_ID,
                    url=page.url,
                    artifact_sha256=page.artifact.content_sha256,
                    locator=page.text.find(release.index.accepted),
                ),
            ),
        )
    )
    overrides.append(
        _override(
            "keep-borealis-same-day",
            EventOverrideKind.RETAIN_UNRESOLVED,
            "EDGAR alone cannot order a 07:00 release against a change before the"
            " open on the same day (EV9).",
            event_id="cik-0009990002:2024-09-30",
            reason=EventReason.SAME_DAY_TRANSITION,
        )
    )
    overrides.append(
        _override(
            "keep-dynamo-no-release",
            EventOverrideKind.RETAIN_UNRESOLVED,
            "Dynamo Motors furnished no results under Item 2.02 for the quarter"
            " ended 2025-06-27.",
            event_id="cik-0009990005:2025-06-27",
            reason=EventReason.NO_RELEASE_FILING,
        )
    )
    return tuple(sorted(overrides, key=lambda override: override.override_id))
