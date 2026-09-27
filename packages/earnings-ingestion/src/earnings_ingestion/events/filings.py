"""An issuer's filings, read from saved responses and placed on the Eastern calendar
(the Stage 5 spec, §Store, client, and readers, and §Acceptance time).

``issuer_filings`` reads the issuer's saved submissions file, and each older page
whose ``filingFrom``-``filingTo`` range meets ``[start, cutoff]``. A page that states
no range is read. Every other page is skipped by its dates, and the skip is
recorded (R1.1).

It then places each filing the build reads (plan 7, P7-8):

- **With its index page saved**, a filing takes the page's Accepted value as its
  acceptance time, and its submissions row is cross-checked against it. A row that
  follows neither convention is a blocking ``acceptance_time_mismatch``.
- **An original periodic report** without its index page is placed by its file's
  convention, which the file's cross-checked rows establish, or by both conventions
  when they establish none. It is visible when it was accepted by the cutoff. When
  the two readings fall on either side of the cutoff, or the row has no value, it
  is ``acceptance_time_unknown``, which blocks until its index page is saved
  (``earnings-pipeline events discover --filing``).
- **An Item 2.02 8-K or 8-K/A** is read from its index page, which discovery saved
  for every one that either convention places in the range. One without a value,
  filed on or after ``start``, is ``acceptance_time_unknown`` in the same way.

A saved response that is missing, unreadable, or for another accession is a
problem: no review can settle it, so the build stops and lists it. Each missing
response's URL is also listed in ``missing``, which discovery fetches next.
"""

from dataclasses import dataclass
from datetime import date, datetime

from earnings_ingestion.cohort.locators import CitableArtifact
from earnings_ingestion.events.acceptance import (
    AcceptanceTimeError,
    FileSurvey,
    accepted_instant,
    eastern_date,
    eastern_dates,
    survey,
)
from earnings_ingestion.events.records import (
    EventFinding,
    EventFindingKind,
    SkippedPage,
    event_finding,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.sec.data import (
    Filing,
    Registrant,
    SecDataError,
    read_submissions,
    read_submissions_page,
)
from earnings_ingestion.sec.filing_index import FilingIndex, read_filing_index
from earnings_ingestion.sec.urls import (
    filing_index_url,
    submissions_page_url,
    submissions_url,
)

PERIODIC_FORMS = frozenset({"10-Q", "10-K", "10-QT", "10-KT"})
RELEASE_FORMS = frozenset({"8-K", "8-K/A"})
RESULTS_ITEM = "2.02"


@dataclass(frozen=True)
class SavedFile:
    """A submissions file or older page, as read."""

    artifact: CitableArtifact
    filings: tuple[Filing, ...]
    survey: FileSurvey


@dataclass(frozen=True)
class Placed:
    """A filing the build reads, with the file that lists it and its index page."""

    filing: Filing
    file: SavedFile
    index: FilingIndex | None = None
    index_artifact: CitableArtifact | None = None
    instant: datetime | None = None
    """The index page's Accepted value, as a UTC instant."""

    @property
    def accepted_on(self) -> date | None:
        """The Eastern date of ``instant``."""
        return None if self.instant is None else eastern_date(self.instant)


@dataclass(frozen=True)
class IssuerFilings:
    cik: str
    registrant: Registrant | None
    files: tuple[SavedFile, ...]
    skipped: tuple[SkippedPage, ...]
    periodic: tuple[Placed, ...]
    """Original periodic reports with a report date, accepted by the cutoff."""
    releases: tuple[Placed, ...]
    """Item 2.02 8-Ks and 8-K/As accepted in ``[start, cutoff]``, with index pages."""
    findings: tuple[EventFinding, ...]
    problems: tuple[str, ...]
    missing: tuple[str, ...]
    """The URLs of responses the build reads that are not saved."""


def _unknown(issuer_id: str, filing: Filing, why: str) -> EventFinding:
    return event_finding(
        EventFindingKind.ACCEPTANCE_TIME_UNKNOWN,
        filing.accession,
        f"{filing.form} {filing.accession}, filed {filing.filing_date}: {why}",
        issuer_id=issuer_id,
    )


class _Reader:
    """Saved responses, read with each failure kept as a problem."""

    def __init__(self, saved: SavedResponses) -> None:
        self.saved = saved
        self.problems: list[str] = []
        self.missing: list[str] = []

    def get(self, url: str) -> CitableArtifact | None:
        try:
            artifact = self.saved.get(url)
        except (FileNotFoundError, ValueError) as exc:
            self.problems.append(f"{url}: {exc}")
            return None
        if artifact is None:
            self.problems.append(f"nothing saved from {url}: run events discover")
            self.missing.append(url)
        return artifact

    def files(
        self, cik: str, start: date, cutoff: date
    ) -> tuple[
        Registrant | None,
        list[tuple[CitableArtifact, tuple[Filing, ...]]],
        list[SkippedPage],
    ]:
        """The submissions file and the older pages in range, with their filings."""
        main = self.get(submissions_url(cik))
        if main is None:
            return None, [], []
        try:
            registrant = read_submissions(main.text.body)
        except SecDataError as exc:
            self.problems.append(f"{main.url}: {exc}")
            return None, [], []
        if registrant.cik != cik:
            self.problems.append(
                f"{main.url} is the submissions file of CIK {registrant.cik}"
            )
            return None, [], []
        listed = [(main, registrant.filings)]
        skipped = []
        for page in registrant.older_pages:
            url = submissions_page_url(page.name)
            dated = page.filing_from is not None and page.filing_to is not None
            if dated and (page.filing_to < start or page.filing_from > cutoff):
                skipped.append(
                    SkippedPage(
                        url=url, filing_from=page.filing_from, filing_to=page.filing_to
                    )
                )
                continue
            artifact = self.get(url)
            if artifact is None:
                continue
            try:
                listed.append((artifact, read_submissions_page(artifact.text.body)))
            except SecDataError as exc:
                self.problems.append(f"{url}: {exc}")
        return registrant, listed, skipped

    def indexes(
        self, cik: str, filings: list[Filing]
    ) -> dict[str, tuple[FilingIndex, CitableArtifact, datetime]]:
        """Every saved index page of ``filings``, with its Accepted instant."""
        found = {}
        for filing in filings:
            url = filing_index_url(cik, filing.accession)
            if url not in self.saved or filing.accession in found:
                continue
            artifact = self.get(url)
            if artifact is None:
                continue
            try:
                index = read_filing_index(artifact.text.body)
                instant = accepted_instant(index.accepted)
            except (SecDataError, AcceptanceTimeError) as exc:
                self.problems.append(f"{url}: {exc}")
                continue
            if index.accession != filing.accession:
                self.problems.append(f"{url} is the index page of {index.accession}")
                continue
            found[filing.accession] = (index, artifact, instant)
        return found


def issuer_filings(
    saved: SavedResponses,
    cik: str,
    issuer_id: str,
    *,
    start: date,
    cutoff: date,
) -> IssuerFilings:
    """Read the issuer's saved filings, and place each one the build reads."""
    reader = _Reader(saved)
    registrant, listed, skipped = reader.files(cik, start, cutoff)
    indexes = reader.indexes(cik, [f for _, filings in listed for f in filings])
    instants = {accession: found[2] for accession, found in indexes.items()}
    findings = []
    files = []
    for artifact, filings in listed:
        checked = survey(artifact.url, filings, instants)
        files.append(SavedFile(artifact=artifact, filings=filings, survey=checked))
        for check in checked.mismatches:
            written = "no value" if check.written is None else check.written.isoformat()
            findings.append(
                event_finding(
                    EventFindingKind.ACCEPTANCE_TIME_MISMATCH,
                    check.accession,
                    f"{artifact.url} gives {written} for {check.accession}, whose"
                    f" index page says {indexes[check.accession][0].accepted} Eastern",
                    issuer_id=issuer_id,
                )
            )
    periodic, releases = [], []
    for file in files:
        for filing in file.filings:
            found = indexes.get(filing.accession)
            placed = Placed(filing, file, *found) if found else Placed(filing, file)
            if filing.form in PERIODIC_FORMS and filing.report_date is not None:
                visible = _visible(placed, file.survey, cutoff)
                if visible is None:
                    findings.append(_unknown(issuer_id, filing, _why(filing, cutoff)))
                elif visible:
                    periodic.append(placed)
            elif filing.form in RELEASE_FORMS and RESULTS_ITEM in filing.items:
                if found is not None:
                    if start <= placed.accepted_on <= cutoff:
                        releases.append(placed)
                elif filing.accepted_at is None:
                    if filing.filing_date >= start:
                        findings.append(
                            _unknown(issuer_id, filing, "no acceptanceDateTime")
                        )
                elif any(
                    start <= day <= cutoff
                    for day in eastern_dates(filing.accepted_at).values()
                ):
                    url = filing_index_url(cik, filing.accession)
                    if url not in saved:
                        reader.problems.append(
                            f"nothing saved from {url}: run events discover"
                        )
                        reader.missing.append(url)
    return IssuerFilings(
        cik=cik,
        registrant=registrant,
        files=tuple(files),
        skipped=tuple(skipped),
        periodic=tuple(sorted(periodic, key=lambda p: p.filing.accession)),
        releases=tuple(sorted(releases, key=lambda p: p.filing.accession)),
        findings=tuple(sorted(findings, key=lambda f: f.finding_id)),
        problems=tuple(reader.problems),
        missing=tuple(reader.missing),
    )


def _visible(placed: Placed, checked: FileSurvey, cutoff: date) -> bool | None:
    """Whether a periodic report was accepted by the cutoff; ``None`` when that
    turns on a convention its file does not establish, or on a missing value."""
    if placed.accepted_on is not None:
        return placed.accepted_on <= cutoff
    written = placed.filing.accepted_at
    if written is None:
        return None
    dates = eastern_dates(written)
    if checked.convention in dates:
        return dates[checked.convention] <= cutoff
    sides = {day <= cutoff for day in dates.values()}
    return sides.pop() if len(sides) == 1 else None


def _why(filing: Filing, cutoff: date) -> str:
    if filing.accepted_at is None:
        return "no acceptanceDateTime"
    readings = sorted(
        {day.isoformat() for day in eastern_dates(filing.accepted_at).values()}
    )
    return (
        f"acceptanceDateTime {filing.accepted_at.isoformat()} falls on"
        f" {' or '.join(readings)}, either side of the cutoff {cutoff}, and its file"
        " establishes no convention"
    )
