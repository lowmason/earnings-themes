"""``issuer-time/1``: the pinned pilot's split by issuer and time (Stage 6 spec, §The
split; GS6, GS7).

- **Inputs.** Each pilot event's ``event_id``, ``issuer_id``, and ``period_end``, and
  the events that are Stage 1 fixtures. No document, state, or outcome (P-C7).
- **Windows.** The calendar quarter of ``period_end``: train 2024Q3-2025Q2, dev
  2025Q3-2025Q4, test 2026Q1-2026Q2.
- **Issuers.** An issuer's events go to the partition of its earliest event. A later
  event whose window is another partition is ``excluded``,
  ``issuer_in_earlier_partition``.
- **Fixtures.** A Stage 1 fixture's event whose window is dev or test is
  ``excluded``, ``fixture_train_or_exclude``: fixtures are never held out. The issuer
  check comes first.
- **Bundles.** A bundle is an event, so every document of an event, with its copies
  and revisions, takes the event's partition (R12.1, R12.3).

The manifest is written once. A changed rule is a new version, never an edit.
"""

from collections.abc import Collection, Iterable
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import PositiveInt, StringConstraints, model_validator

from earnings_themes.records import (
    IdPart,
    Part,
    Pin,
    RecordError,
    Sha256Hex,
    ThemesRecord,
    digest,
    parse,
    read_json,
)

SPLIT_POLICY = "issuer-time/1"

Quarter = Annotated[str, StringConstraints(pattern=r"^[0-9]{4}Q[1-4]$")]


class Partition(StrEnum):
    """Where ``issuer-time/1`` puts an event."""

    TRAIN = "train"
    DEV = "dev"
    TEST = "test"
    EXCLUDED = "excluded"


class ExclusionReason(StrEnum):
    """Why an event is in no partition."""

    ISSUER_IN_EARLIER_PARTITION = "issuer_in_earlier_partition"
    FIXTURE_TRAIN_OR_EXCLUDE = "fixture_train_or_exclude"


class SplitWindow(Part):
    """One partition's quarters, first and last inclusive."""

    partition: Partition
    first: Quarter
    last: Quarter


WINDOWS = (
    SplitWindow(partition=Partition.TRAIN, first="2024Q3", last="2025Q2"),
    SplitWindow(partition=Partition.DEV, first="2025Q3", last="2025Q4"),
    SplitWindow(partition=Partition.TEST, first="2026Q1", last="2026Q2"),
)


class SplitEvent(Part):
    """One pilot event, as the rule reads it."""

    event_id: IdPart
    issuer_id: IdPart
    period_end: date


class SplitRow(Part):
    """One pilot event and its partition."""

    event_id: IdPart
    issuer_id: IdPart
    period_end: date
    partition: Partition
    reason: ExclusionReason | None = None

    @model_validator(mode="after")
    def _reason_exactly_when_excluded(self) -> Self:
        if (self.partition is Partition.EXCLUDED) != (self.reason is not None):
            raise ValueError("an excluded event has a reason, and only it")
        return self


class SplitManifest(ThemesRecord):
    """``split-v<N>.json``: the frozen split of one pinned pilot."""

    split_policy: Literal["issuer-time/1"]
    split_version: PositiveInt
    windows: tuple[SplitWindow, ...]
    pin: Pin
    rows: tuple[SplitRow, ...]
    content_hash: Sha256Hex

    @model_validator(mode="after")
    def _one_row_per_event(self) -> Self:
        ids = [row.event_id for row in self.rows]
        if ids != sorted(set(ids)):
            raise ValueError("rows are sorted by event_id, and each event is in one")
        if self.windows != WINDOWS:
            raise ValueError(f"{SPLIT_POLICY}'s windows are fixed")
        return self

    def partition_of(self, event_id: str) -> Partition:
        """The partition of one pilot event; ``KeyError`` for any other."""
        for row in self.rows:
            if row.event_id == event_id:
                return row.partition
        raise KeyError(event_id)

    def events_in(self, partition: Partition) -> tuple[str, ...]:
        """The events of one partition, by ``event_id``."""
        return tuple(row.event_id for row in self.rows if row.partition == partition)


def quarter(day: date) -> str:
    """The calendar quarter of ``day``, such as ``2024Q3``."""
    return f"{day.year}Q{(day.month - 1) // 3 + 1}"


def window_of(day: date) -> Partition:
    """The partition whose window holds ``day``'s quarter."""
    named = quarter(day)
    for window in WINDOWS:
        if window.first <= named <= window.last:
            return window.partition
    raise ValueError(f"{named} is in no window of {SPLIT_POLICY}")


def split_hash(manifest: SplitManifest) -> str:
    """The content hash: every field but ``content_hash`` itself."""
    return digest(manifest.model_dump(mode="json", exclude={"content_hash"}))


def split_events(
    events: Iterable[SplitEvent],
    pin: Pin,
    *,
    fixture_event_ids: Collection[str] = frozenset(),
    version: int = 1,
) -> SplitManifest:
    """Split ``events`` by ``issuer-time/1``."""
    events = sorted(events, key=lambda event: event.event_id)
    if len({event.event_id for event in events}) != len(events):
        raise ValueError("an event is listed twice")
    home: dict[str, Partition] = {}
    for event in sorted(events, key=lambda event: (event.period_end, event.event_id)):
        home.setdefault(event.issuer_id, window_of(event.period_end))
    rows = []
    for event in events:
        window = window_of(event.period_end)
        reason = None
        if window is not home[event.issuer_id]:
            reason = ExclusionReason.ISSUER_IN_EARLIER_PARTITION
        elif event.event_id in fixture_event_ids and window is not Partition.TRAIN:
            reason = ExclusionReason.FIXTURE_TRAIN_OR_EXCLUDE
        rows.append(
            SplitRow(
                event_id=event.event_id,
                issuer_id=event.issuer_id,
                period_end=event.period_end,
                partition=Partition.EXCLUDED if reason else window,
                reason=reason,
            )
        )
    draft = SplitManifest(
        split_policy=SPLIT_POLICY,
        split_version=version,
        windows=WINDOWS,
        pin=pin,
        rows=tuple(rows),
        content_hash="0" * 64,
    )
    return draft.model_copy(update={"content_hash": split_hash(draft)})


def load_split(path: Path) -> SplitManifest:
    """A frozen split, refused unless it hashes to its ``content_hash``."""
    manifest = parse(read_json(path), SplitManifest, path.name)
    if split_hash(manifest) != manifest.content_hash:
        raise RecordError(path.name, ("does not hash to its content_hash",))
    return manifest
