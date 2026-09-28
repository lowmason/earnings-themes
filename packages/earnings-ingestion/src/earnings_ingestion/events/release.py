"""``release-id/1``: which candidate 8-K first published a slot's results (the Stage 5
spec, §Candidates and ``release-id/1``; plan 7, P7-7).

**Candidates.** Take a slot with period end P. P' is the issuer's next visible period
end, or the cutoff when none is visible. A candidate is an original 8-K accepted after
P and on or before P', on the Eastern calendar, whose submissions items and index page
both give Item 2.02, and whose index page lists an exhibit typed ``EX-99*``. An 8-K/A
in that range is an amendment: recorded, and never chosen by the rule. Any other
Item 2.02 8-K in the range is passed over, with the reason, for review.

**The reading.** Each candidate's primary document is read in walker-1's text:

1. *Item text.* Each line that begins "Item 2.02" opens a section, which runs to the
   next line that begins "Item" and a number, or to the end of the text. A cover page
   that lists the items makes a section that runs to the next Item line: usually the
   next entry, so that the heading stands alone, but when Item 2.02 is the list's last
   entry, the section takes in whatever lies before the next Item line. The sections
   are read together. A document walker-1 cannot read, one that is not HTML, and one
   with no such heading state nothing.
2. *Stated dates.* A full date after "ended" or "ending": a month's name or its
   abbreviation, the day, a comma, and the year. An announcement date or a signature
   date states no period (P7-7).
3. *Stated fiscal periods*, read quarters first, so that a year inside a quarter's
   phrase is not read again as a full year:
   - an ordinal quarter with its year: "third quarter of 2024", "third-quarter 2024",
     "second fiscal quarter of 2025", "first quarter of fiscal 2026", and the
     year-first "fiscal 2025 second quarter";
   - a ``Q`` quarter: "Q3 2024", "Q2 fiscal 2025", and "3Q 2024";
   - a full year: "fiscal 2025", "fiscal year 2025", "full year 2024", and
     "full-year 2024".
4. *Preliminary.* "preliminary", or "expected" with "results" among the next three
   words.

**Resolution.** A stated date matches when it equals P. A fiscal period is judged only
when the slot has labels whose ``fp`` is ``Q1``, ``Q2``, ``Q3``, or ``FY``. It then
matches when it names that quarter, or for ``FY`` the fourth quarter or the full year,
of the year ``fy``. The rule drops each candidate whose judged statements all fail to
match, and each that calls its results preliminary. If one candidate is left, it is
the release filing: ``stated_period`` if it has a matching statement, and otherwise
``sole_candidate``. None left is ``ambiguous`` with ``no_release_filing``, and several
are ``ambiguous`` with ``several_release_filings``.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from earnings_ingestion.cohort.locators import CitableArtifact, LocatorError
from earnings_ingestion.cohort.records import Citation
from earnings_ingestion.events.filings import RESULTS_ITEM, Placed
from earnings_ingestion.events.records import EventReason, IdentificationMethod
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.slots import Slot
from earnings_ingestion.sec.companyfacts import FiscalLabels
from earnings_ingestion.sec.urls import archive_url

RELEASE_POLICY = "release-id/1"

_HEADING = re.compile(
    r"^[^\S\n]*item[^\S\n]+(\d+\.\d+)\b", re.IGNORECASE | re.MULTILINE
)
_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan.": 1,
    "feb.": 2,
    "mar.": 3,
    "apr.": 4,
    "jun.": 6,
    "jul.": 7,
    "aug.": 8,
    "sep.": 9,
    "sept.": 9,
    "oct.": 10,
    "nov.": 11,
    "dec.": 12,
}
_MONTH = "|".join(re.escape(name) for name in sorted(_MONTHS, key=len, reverse=True))
_DATE = re.compile(
    rf"\b(?:ended|ending)\s+(?P<month>{_MONTH})\s+(?P<day>\d{{1,2}}),\s+(?P<year>\d{{4}})\b",
    re.IGNORECASE,
)
_ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4}
_ORDINAL = r"(?P<ordinal>first|second|third|fourth)"
_FISCAL = r"(?:fiscal\s+(?:year\s+)?)"
_QUARTERS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        rf"\b{_ORDINAL}[\s-]+(?:fiscal\s+)?quarter(?:\s+of)?\s+{_FISCAL}?(?P<year>\d{{4}})\b",
        rf"\b{_FISCAL}(?P<year>\d{{4}})\s+{_ORDINAL}[\s-]+quarter\b",
        rf"\bQ(?P<number>[1-4])\s+{_FISCAL}?(?P<year>\d{{4}})\b",
        r"\b(?P<number>[1-4])Q\s+(?P<year>\d{4})\b",
    )
)
_YEARS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        rf"\b{_FISCAL}(?P<year>\d{{4}})\b",
        r"\bfull[\s-]year\s+(?P<year>\d{4})\b",
    )
)
_PRELIMINARY = re.compile(
    r"\bpreliminary\b|\bexpected(?:\s+[\w-]+){0,2}\s+results\b", re.IGNORECASE
)
_JUDGED = frozenset({"Q1", "Q2", "Q3", "FY"})


@dataclass(frozen=True, order=True)
class FiscalPeriod:
    """A fiscal period a text names: ``Q1`` to ``Q4``, or ``FY`` for a full year."""

    year: int
    period: str

    def __str__(self) -> str:
        return f"{self.period} {self.year}"


@dataclass(frozen=True)
class Reading:
    """What ``release-id/1`` reads in one primary document."""

    sections: tuple[tuple[int, int], ...] = ()
    """The Item 2.02 sections, as ``[start, end)`` offsets into walker-1's text."""
    dates: tuple[date, ...] = ()
    periods: tuple[FiscalPeriod, ...] = ()
    preliminary: bool = False
    unread: str | None = None
    """Why no Item 2.02 text was read, when none was."""


def _periods(section: str) -> set[FiscalPeriod]:
    found: set[FiscalPeriod] = set()
    taken: list[tuple[int, int]] = []
    for pattern in (*_QUARTERS, *_YEARS):
        for match in pattern.finditer(section):
            if any(start < match.end() and match.start() < end for start, end in taken):
                continue
            taken.append(match.span())
            groups = match.groupdict()
            if groups.get("ordinal"):
                period = f"Q{_ORDINALS[groups['ordinal'].lower()]}"
            elif groups.get("number"):
                period = f"Q{groups['number']}"
            else:
                period = "FY"
            found.add(FiscalPeriod(int(groups["year"]), period))
    return found


def _dates(section: str) -> set[date]:
    found = set()
    for match in _DATE.finditer(section):
        month = _MONTHS[match["month"].lower()]
        try:
            found.add(date(int(match["year"]), month, int(match["day"])))
        except ValueError:
            continue
    return found


def read_text(text: str) -> Reading:
    """Read walker-1's text of a primary document."""
    headings = list(_HEADING.finditer(text))
    sections = []
    for number, heading in enumerate(headings):
        if heading.group(1) != RESULTS_ITEM:
            continue
        following = headings[number + 1] if number + 1 < len(headings) else None
        end = len(text) if following is None else following.start()
        body = text[heading.start() : end].rstrip()
        sections.append((heading.start(), heading.start() + len(body)))
    if not sections:
        return Reading(unread="it has no Item 2.02 heading")
    dates: set[date] = set()
    periods: set[FiscalPeriod] = set()
    preliminary = False
    for start, end in sections:
        section = text[start:end]
        dates |= _dates(section)
        periods |= _periods(section)
        preliminary = preliminary or _PRELIMINARY.search(section) is not None
    return Reading(
        sections=tuple(sections),
        dates=tuple(sorted(dates)),
        periods=tuple(sorted(periods)),
        preliminary=preliminary,
    )


def read_document(document: CitableArtifact) -> Reading:
    """Read a saved primary document in walker-1's text."""
    if document.text.media_type != "text/html":
        return Reading(unread=f"it is {document.text.media_type}, not HTML")
    try:
        text, _ = document.text.canonical
    except LocatorError as exc:
        return Reading(unread=str(exc))
    return read_text(text)


def _wanted(fiscal_period: str) -> frozenset[str] | None:
    """The periods that match labels of ``fiscal_period``; ``None`` when unjudged."""
    if fiscal_period not in _JUDGED:
        return None
    return frozenset({"Q4", "FY"} if fiscal_period == "FY" else {fiscal_period})


def _matches(period: FiscalPeriod, labels: FiscalLabels | None) -> bool | None:
    """Whether a fiscal period matches the slot's labels; ``None`` when unjudged."""
    wanted = None if labels is None else _wanted(labels.fiscal_period)
    if wanted is None:
        return None
    return period.year == labels.fiscal_year and period.period in wanted


def states_period(
    text: str, period_end: date, fiscal_year: int | None, fiscal_period: str | None
) -> bool:
    """Whether ``text`` states the period ending ``period_end`` as the rule reads a
    statement: a full date after "ended" or "ending" that is ``period_end``, or a
    fiscal period that matches the labels ``fiscal_year`` and ``fiscal_period``,
    judged only for ``Q1``, ``Q2``, ``Q3``, and ``FY``. ``release-content/1`` reads
    an exhibit's whole text this way (plan 8, P8-9)."""
    if period_end in _dates(text):
        return True
    wanted = None if fiscal_period is None else _wanted(fiscal_period)
    if fiscal_year is None or wanted is None:
        return False
    return any(
        period.year == fiscal_year and period.period in wanted
        for period in _periods(text)
    )


@dataclass(frozen=True)
class Candidate:
    """One candidate, as the rule reads and judges it for its slot."""

    placed: Placed
    document: CitableArtifact | None
    reading: Reading
    judged: bool
    """It states a date, or a fiscal period its slot's labels judge."""
    matched: bool
    """One of its statements matches the slot."""

    @property
    def dropped(self) -> str | None:
        """Why the rule drops it; ``None`` when it stays."""
        if self.judged and not self.matched:
            return "it states another period"
        if self.reading.preliminary:
            return "it calls its results preliminary"
        return None

    def item_text(self) -> Citation | None:
        """Its Item 2.02 sections, cited in its primary document's walker-1 text."""
        if self.document is None or not self.reading.sections:
            return None
        return self.document.cite(
            *(
                self.document.text.span(start, end)
                for start, end in self.reading.sections
            )
        )


@dataclass(frozen=True)
class Identification:
    """A slot's candidates, amendments, and release filing under ``release-id/1``."""

    candidates: tuple[Candidate, ...]
    amendments: tuple[Placed, ...]
    passed_over: tuple[tuple[Placed, str], ...]
    """The other Item 2.02 8-Ks in the range, and why each is not a candidate, which
    the build's report prints for review (P7-15)."""
    release: Candidate | None
    method: IdentificationMethod | None
    reason: EventReason | None
    """``no_release_filing`` or ``several_release_filings`` when no release filing is
    identified."""
    problems: tuple[str, ...]


def _passed_over(placed: Placed) -> str | None:
    if RESULTS_ITEM not in placed.index.items:
        return "its index page lists no Item 2.02"
    if not placed.index.exhibits_99():
        return "its index page lists no exhibit typed EX-99*"
    return None


def identify(
    slot: Slot, releases: Sequence[Placed], saved: SavedResponses, *, cutoff: date
) -> Identification:
    """Apply ``release-id/1`` to one slot. ``releases`` are its issuer's placed
    Item 2.02 8-Ks and 8-K/As (``IssuerFilings.releases``)."""
    last = slot.next_period_end or cutoff
    in_range = sorted(
        (p for p in releases if slot.period_end < p.accepted_on <= last),
        key=lambda p: (p.instant, p.filing.accession),
    )
    candidates, amendments, passed_over, problems = [], [], [], []
    for placed in in_range:
        if placed.filing.form != "8-K":
            amendments.append(placed)
            continue
        if why := _passed_over(placed):
            passed_over.append((placed, why))
            continue
        filing = placed.filing
        url = archive_url(slot.cik, filing.accession, filing.primary_document)
        try:
            document = saved.get(url)
        except (FileNotFoundError, ValueError) as exc:
            problems.append(f"{url}: {exc}")
            document = None
        if document is None:
            if not problems or not problems[-1].startswith(url):
                problems.append(f"nothing saved from {url}: run events discover")
            reading = Reading(unread="nothing saved")
        else:
            reading = read_document(document)
        judged = bool(reading.dates) or any(
            _matches(period, slot.labels) is not None for period in reading.periods
        )
        matched = slot.period_end in reading.dates or any(
            _matches(period, slot.labels) for period in reading.periods
        )
        candidates.append(Candidate(placed, document, reading, judged, matched))
    kept = [candidate for candidate in candidates if candidate.dropped is None]
    release = kept[0] if len(kept) == 1 else None
    if release is not None:
        method = (
            IdentificationMethod.STATED_PERIOD
            if release.matched
            else IdentificationMethod.SOLE_CANDIDATE
        )
        reason = None
    else:
        method = None
        reason = (
            EventReason.SEVERAL_RELEASE_FILINGS
            if kept
            else EventReason.NO_RELEASE_FILING
        )
    return Identification(
        candidates=tuple(candidates),
        amendments=tuple(amendments),
        passed_over=tuple(passed_over),
        release=release,
        method=method,
        reason=reason,
        problems=tuple(problems),
    )
