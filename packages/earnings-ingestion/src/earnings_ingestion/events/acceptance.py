"""EDGAR acceptance time (EV10 of the Stage 5 spec, §Acceptance time).

- A filing's acceptance time is its index page's "Accepted" value, which is Eastern
  wall time. ``accepted_instant`` localizes it to America/New_York and returns the UTC
  instant. A wall time that daylight saving repeats or skips is refused, never
  guessed.
- SEC's submissions ``acceptanceDateTime`` is only a cross-check. SEC writes it in two
  conventions, one per file (the spec's Finding 1): the true UTC instant, or the
  instant's Eastern wall-clock digits followed by ``Z``. ``convention_of`` names the
  one a row uses, and ``None`` is a mismatch, which blocks.
- A file's convention is the one its cross-checked rows share (``survey``). It is
  never inferred from the file's dates.
- Every date judgment uses the Eastern calendar date (``eastern_date``).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from earnings_ingestion.sec.data import Filing

SOURCE_TIMEZONE = "America/New_York"
EASTERN = ZoneInfo(SOURCE_TIMEZONE)


class Convention(StrEnum):
    UTC = "utc"
    """The value is the instant."""
    EASTERN_DIGITS = "eastern_digits"
    """The value is the instant's Eastern wall-clock digits, followed by ``Z``."""


class AcceptanceTimeError(ValueError):
    """An Accepted value that daylight saving repeats or skips."""


def accepted_instant(accepted: str) -> datetime:
    """The UTC instant of an index page's Accepted text, ``YYYY-MM-DD HH:MM:SS``."""
    wall = datetime.combine(
        date.fromisoformat(accepted[:10]),
        time.fromisoformat(accepted[11:]),
        tzinfo=EASTERN,
    )
    if wall.utcoffset() != wall.replace(fold=1).utcoffset():
        raise AcceptanceTimeError(
            f"{accepted} is repeated or skipped in {SOURCE_TIMEZONE}"
        )
    return wall.astimezone(UTC)


def eastern_date(instant: datetime) -> date:
    return instant.astimezone(EASTERN).date()


def convention_of(written: datetime | None, instant: datetime) -> Convention | None:
    """The convention of a row's ``acceptanceDateTime``, given the instant its index
    page states; ``None`` when it follows neither."""
    if written is None:
        return None
    if written == instant:
        return Convention.UTC
    if (
        written.utcoffset() == timedelta(0)
        and written.replace(tzinfo=EASTERN) == instant
    ):
        return Convention.EASTERN_DIGITS
    return None


def eastern_dates(written: datetime) -> dict[Convention, date]:
    """The Eastern date ``written`` gives under each convention it can follow: a value
    with a non-zero offset can only be the instant it states."""
    dates = {Convention.UTC: eastern_date(written)}
    if written.utcoffset() == timedelta(0):
        dates[Convention.EASTERN_DIGITS] = written.date()
    return dates


@dataclass(frozen=True)
class CrossCheck:
    """A submissions row checked against its filing's index page."""

    accession: str
    written: datetime | None
    instant: datetime
    convention: Convention | None
    pointer: str
    """The JSON pointer of the row's ``acceptanceDateTime``."""


@dataclass(frozen=True)
class FileSurvey:
    """A submissions file or older page, and the cross-checks of its rows."""

    name: str
    checks: tuple[CrossCheck, ...]

    @property
    def conventions(self) -> frozenset[Convention]:
        return frozenset(c.convention for c in self.checks if c.convention is not None)

    @property
    def convention(self) -> Convention | None:
        """The convention every matching row shares; ``None`` when no row matched, or
        the rows follow both."""
        return next(iter(self.conventions)) if len(self.conventions) == 1 else None

    @property
    def mixed(self) -> bool:
        return len(self.conventions) > 1

    @property
    def mismatches(self) -> tuple[CrossCheck, ...]:
        return tuple(check for check in self.checks if check.convention is None)


def survey(
    name: str, filings: Iterable[Filing], instants: Mapping[str, datetime]
) -> FileSurvey:
    """Cross-check each of a file's filings whose index page gives an instant."""
    return FileSurvey(
        name=name,
        checks=tuple(
            CrossCheck(
                accession=filing.accession,
                written=filing.accepted_at,
                instant=instants[filing.accession],
                convention=convention_of(
                    filing.accepted_at, instants[filing.accession]
                ),
                pointer=filing.pointer("acceptanceDateTime"),
            )
            for filing in filings
            if filing.accession in instants
        ),
    )
