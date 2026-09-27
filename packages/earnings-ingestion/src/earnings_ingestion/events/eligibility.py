"""``eligibility/1``: each event's status, its reason, and the assertion that decided
it (the Stage 5 spec, §Eligibility, step 3; plan 7, P7-11).

**Membership at an instant T**, the release filing's acceptance:

- An interval holds T when T is on or after its start and before its end, each judged
  by the bound rules. An ``anchor_snapshot`` start is a lower bound: every release on
  or after its date is inside.
- The issuer is a member when any of its securities' intervals holds T. It is not a
  member when none holds T and none is unordered at T. Otherwise its membership is
  unordered. ``MembershipInterval.contains`` is not used, since it ignores timing.

**The bound rules.** A release on Eastern date d at time t falls before a bound on
Eastern date D when d < D, and after it when d > D. When d = D, a ``before_open``
bound puts it after if t is 09:30 or later, the regular open; an ``after_close`` bound
puts it before if t is before 13:00, NYSE's earliest scheduled close; any other case
is unordered. So no trading calendar is needed (EV13).

**The checks** run in order, and the first that applies decides:

1. a period end outside ``[start, stop)`` is ``period_end_outside_window``;
2. an event with no release filing keeps its identification's reason,
   ``no_release_filing`` or ``several_release_filings``;
3. a publication whose Eastern date is after the cutoff is ``published_after_cutoff``;
4. membership at T gives ``member_at_publication``, ``not_member_at_publication``, or
   ``same_day_transition``.

**``membership_assertion_id``** names the assertion that decided check 4, and is
``None`` when check 1, 2, or 3 decided (P7-11):

- for a member, the assertion that opens an interval holding T. Of several such
  intervals, the one that opened first decides, and of several assertions, the
  smallest ID (P7-11);
- for a non-member, the nearer in days of the ``removed`` assertion closing the last
  interval before T and the ``added`` assertion opening the first interval after T.
  A tie goes to the removal;
- for an unordered case, the assertion of the unordered bound, the smallest ID if
  there are several.
"""

from dataclasses import dataclass
from datetime import date, datetime, time
from enum import StrEnum

from earnings_ingestion.cohort.records import (
    AssertedAction,
    BoundBasis,
    BoundTiming,
    MembershipInterval,
    UniverseManifest,
)
from earnings_ingestion.events.acceptance import EASTERN
from earnings_ingestion.events.records import (
    STATUS_OF,
    UNIDENTIFIED,
    EventReason,
    EventStatus,
)

ELIGIBILITY_POLICY = "eligibility/1"
REGULAR_OPEN = time(9, 30)
EARLIEST_CLOSE = time(13, 0)


class Side(StrEnum):
    """Where a release falls against a bound."""

    BEFORE = "before"
    AFTER = "after"
    UNORDERED = "unordered"


def side(day: date, timing: BoundTiming, instant: datetime) -> Side:
    """The side of a bound on Eastern date ``day``, with ``timing``, on which a
    release accepted at ``instant`` falls."""
    if instant.utcoffset() is None:
        raise ValueError("an acceptance instant carries its offset")
    local = instant.astimezone(EASTERN)
    if local.date() != day:
        return Side.BEFORE if local.date() < day else Side.AFTER
    if timing is BoundTiming.BEFORE_OPEN and local.time() >= REGULAR_OPEN:
        return Side.AFTER
    if timing is BoundTiming.AFTER_CLOSE and local.time() < EARLIEST_CLOSE:
        return Side.BEFORE
    return Side.UNORDERED


@dataclass(frozen=True)
class Bound:
    day: date
    timing: BoundTiming
    assertion_ids: tuple[str, ...]
    """The assertions that set the bound, smallest first."""


@dataclass(frozen=True)
class Span:
    """One interval of one of the issuer's securities."""

    security_id: str
    start: Bound
    anchor: bool
    """The start is an ``anchor_snapshot``: a lower bound."""
    end: Bound | None

    def start_side(self, instant: datetime) -> Side:
        if self.anchor:
            local = instant.astimezone(EASTERN).date()
            return Side.AFTER if local >= self.start.day else Side.BEFORE
        return side(self.start.day, self.start.timing, instant)

    def holds(self, instant: datetime) -> bool | None:
        """Whether the interval holds ``instant``; ``None`` when that is unordered."""
        started = {Side.AFTER: True, Side.BEFORE: False}.get(self.start_side(instant))
        if self.end is None:
            ended = False
        else:
            where = side(self.end.day, self.end.timing, instant)
            ended = {Side.AFTER: True, Side.BEFORE: False}.get(where)
        if started is False or ended is True:
            return False
        if started is True and ended is False:
            return True
        return None


def span(interval: MembershipInterval, actions: dict[str, AssertedAction]) -> Span:
    """An interval, with its assertions split into its start's and its end's."""
    closing = {
        i for i in interval.assertion_ids if actions[i] is AssertedAction.REMOVED
    }
    opening = tuple(sorted(set(interval.assertion_ids) - closing))
    end = None
    if interval.effective_to is not None:
        end = Bound(
            interval.effective_to, interval.effective_to_timing, tuple(sorted(closing))
        )
    return Span(
        security_id=interval.security_id,
        start=Bound(interval.effective_from, interval.effective_from_timing, opening),
        anchor=interval.effective_from_basis is BoundBasis.ANCHOR_SNAPSHOT,
        end=end,
    )


@dataclass(frozen=True)
class IssuerMembership:
    """Every interval of one issuer's securities."""

    issuer_id: str
    spans: tuple[Span, ...]


def memberships(manifest: UniverseManifest) -> dict[str, IssuerMembership]:
    """Each issuer's intervals, keyed by ``issuer_id``."""
    actions = {
        a.membership_assertion_id: a.asserted_action for a in manifest.assertions
    }
    found = {}
    for issuer in manifest.issuers:
        spans = tuple(
            span(interval, actions)
            for interval in sorted(
                manifest.intervals, key=lambda i: (i.security_id, i.effective_from)
            )
            if interval.security_id in issuer.security_ids
        )
        found[issuer.issuer_id] = IssuerMembership(issuer.issuer_id, spans)
    return found


class Standing(StrEnum):
    MEMBER = "member"
    NOT_MEMBER = "not_member"
    UNORDERED = "unordered"


def standing(membership: IssuerMembership, instant: datetime) -> tuple[Standing, str]:
    """The issuer's membership at ``instant``, and the assertion that decides it."""
    spans = membership.spans
    if not spans:
        raise ValueError(f"{membership.issuer_id} has no membership interval")
    held = [(each, each.holds(instant)) for each in spans]
    members = [each for each, holds in held if holds is True]
    if members:
        first = min(members, key=lambda s: (s.start.day, s.start.assertion_ids[0]))
        return Standing.MEMBER, first.start.assertion_ids[0]
    unordered = []
    for each, holds in held:
        if holds is not None:
            continue
        if each.start_side(instant) is Side.UNORDERED:
            unordered.extend(each.start.assertion_ids)
        if each.end is not None and (
            side(each.end.day, each.end.timing, instant) is Side.UNORDERED
        ):
            unordered.extend(each.end.assertion_ids)
    if unordered:
        return Standing.UNORDERED, min(unordered)
    day = instant.astimezone(EASTERN).date()
    ended = [
        each
        for each in spans
        if each.end is not None
        and side(each.end.day, each.end.timing, instant) is Side.AFTER
    ]
    later = [each for each in spans if each not in ended]
    nearest = []
    if ended:
        last = max(each.end.day for each in ended)
        ids = [
            i for each in ended if each.end.day == last for i in each.end.assertion_ids
        ]
        nearest.append(((day - last).days, 0, min(ids)))
    if later:
        first = min(each.start.day for each in later)
        ids = [
            i
            for each in later
            if each.start.day == first
            for i in each.start.assertion_ids
        ]
        nearest.append(((first - day).days, 1, min(ids)))
    return Standing.NOT_MEMBER, min(nearest)[2]


@dataclass(frozen=True)
class Decision:
    status: EventStatus
    reason: EventReason
    membership_assertion_id: str | None


_BY_STANDING = {
    Standing.MEMBER: EventReason.MEMBER_AT_PUBLICATION,
    Standing.NOT_MEMBER: EventReason.NOT_MEMBER_AT_PUBLICATION,
    Standing.UNORDERED: EventReason.SAME_DAY_TRANSITION,
}


def _by(reason: EventReason, assertion_id: str | None = None) -> Decision:
    return Decision(STATUS_OF[reason], reason, assertion_id)


def decide(
    period_end: date,
    published: datetime | None,
    unidentified: EventReason | None,
    membership: IssuerMembership,
    *,
    start: date,
    stop: date,
    cutoff: date,
) -> Decision:
    """Run the checks in order. ``published`` is the release filing's acceptance,
    and ``unidentified`` the identification's reason when there is no release."""
    if not start <= period_end < stop:
        return _by(EventReason.PERIOD_END_OUTSIDE_WINDOW)
    if published is None:
        if unidentified not in UNIDENTIFIED:
            raise ValueError(
                "an event with no release filing is no_release_filing or"
                " several_release_filings"
            )
        return _by(unidentified)
    if published.utcoffset() is None:
        raise ValueError("an acceptance instant carries its offset")
    if published.astimezone(EASTERN).date() > cutoff:
        return _by(EventReason.PUBLISHED_AFTER_CUTOFF)
    state, assertion_id = standing(membership, published)
    return _by(_BY_STANDING[state], assertion_id)
