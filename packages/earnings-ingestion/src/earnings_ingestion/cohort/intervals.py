"""Effective membership intervals from the anchor and the announced changes.

Each security's statements, its anchor row and its changes, must form one sequence.
It starts from the anchor, a member if the anchor lists it; additions and removals
then alternate, each strictly after the anchor's date. Identical claims from several
items are one transition. Otherwise:

- an addition and a removal on one date are ``ambiguous``: the evidence cannot say
  whether the security was a member that day;
- any other break is ``conflicting``: an addition while a member, a removal while not
  one, a change on or before the anchor's date, or one transition stated with two
  timings.

A security whose statements break the sequence has every statement marked and no
interval until a reviewer rejects the wrong ones (``reject_assertion``); its finding
holds the freeze meanwhile. Statements first published after the cutoff are
``withheld`` and never applied (P-C4). Conflicting statements are never merged.
"""

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import NamedTuple

from earnings_ingestion.cohort.findings import make_finding
from earnings_ingestion.cohort.records import (
    AssertedAction,
    AssertionStatus,
    BoundBasis,
    BoundTiming,
    Finding,
    FindingKind,
    MembershipInterval,
)


@dataclass(frozen=True)
class Statement:
    """What one evidence item says about one security, before any judgement."""

    assertion_id: str
    security_id: str
    action: AssertedAction
    on: date
    timing: BoundTiming
    evidence_id: str
    published_on: date


@dataclass(frozen=True)
class Membership:
    statuses: dict[str, AssertionStatus]
    rejected_by: dict[str, str]
    """Each rejected assertion's ``reject_assertion`` override."""
    intervals: tuple[MembershipInterval, ...]
    supports: dict[str, MembershipInterval]
    """The interval each supported assertion belongs to."""
    findings: tuple[Finding, ...]


class _Break(NamedTuple):
    status: AssertionStatus
    detail: str


def _sequence(
    security_id: str, statements: list[Statement], anchor_date: date | None
) -> list[MembershipInterval] | _Break:
    anchored = [s for s in statements if s.action is AssertedAction.MEMBER_AT]
    days: dict[date, dict[AssertedAction, list[Statement]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for statement in statements:
        if statement.action is not AssertedAction.MEMBER_AT:
            days[statement.on][statement.action].append(statement)
    transitions = []
    for day in sorted(days):
        actions = days[day]
        if len(actions) > 1:
            return _Break(AssertionStatus.AMBIGUOUS, f"added and removed on {day}")
        ((action, group),) = actions.items()
        timings = sorted({statement.timing.value for statement in group})
        if len(timings) > 1:
            return _Break(
                AssertionStatus.CONFLICTING, f"{action} on {day} with timings {timings}"
            )
        if anchor_date is not None and day <= anchor_date:
            return _Break(
                AssertionStatus.CONFLICTING,
                f"{action} on {day}, on or before the anchor's date {anchor_date}",
            )
        transitions.append((day, action, group[0].timing, group))

    intervals: list[MembershipInterval] = []
    start = None
    if anchored:
        ids = [statement.assertion_id for statement in anchored]
        start = (anchor_date, BoundBasis.ANCHOR_SNAPSHOT, BoundTiming.UNSPECIFIED, ids)
    for day, action, timing, group in transitions:
        ids = [statement.assertion_id for statement in group]
        if action is AssertedAction.ADDED:
            if start is not None:
                return _Break(
                    AssertionStatus.CONFLICTING, f"added on {day} while a member"
                )
            start = (day, BoundBasis.ANNOUNCED, timing, ids)
            continue
        if start is None:
            return _Break(
                AssertionStatus.CONFLICTING, f"removed on {day} while not a member"
            )
        intervals.append(_interval(security_id, start, day, timing, ids))
        start = None
    if start is not None:
        intervals.append(_interval(security_id, start, None, None, []))
    return intervals


def _interval(security_id, start, end, end_timing, end_ids) -> MembershipInterval:
    day, basis, timing, ids = start
    return MembershipInterval(
        security_id=security_id,
        effective_from=day,
        effective_from_basis=basis,
        effective_from_timing=timing,
        effective_to=end,
        effective_to_timing=end_timing,
        assertion_ids=tuple(sorted([*ids, *end_ids])),
    )


def _finding(security_id: str, flaw: _Break, statements, resolved_by) -> Finding:
    kind = (
        FindingKind.MEMBERSHIP_AMBIGUITY
        if flaw.status is AssertionStatus.AMBIGUOUS
        else FindingKind.MEMBERSHIP_CONFLICT
    )
    return make_finding(
        kind,
        security_id,
        f"{security_id}: {flaw.detail}",
        blocking=True,
        security_id=security_id,
        evidence_ids=[statement.evidence_id for statement in statements],
        resolved_by=resolved_by,
    )


def reconstruct(
    statements: Iterable[Statement],
    *,
    anchor_date: date | None,
    cutoff: date,
    rejections: Mapping[str, str],
) -> Membership:
    """Statuses, intervals, and findings; ``rejections`` maps an assertion id to the
    ``reject_assertion`` override that sets it aside."""
    statements = tuple(statements)
    unknown = set(rejections) - {statement.assertion_id for statement in statements}
    if unknown:
        raise ValueError(f"rejections name no assertion: {sorted(unknown)}")
    by_security: dict[str, list[Statement]] = defaultdict(list)
    for statement in statements:
        by_security[statement.security_id].append(statement)

    statuses: dict[str, AssertionStatus] = {}
    rejected_by: dict[str, str] = {}
    intervals: list[MembershipInterval] = []
    findings: list[Finding] = []
    for security_id in sorted(by_security):
        live = []
        for statement in by_security[security_id]:
            if statement.published_on > cutoff:
                statuses[statement.assertion_id] = AssertionStatus.WITHHELD
            else:
                live.append(statement)
        rejected = [s for s in live if s.assertion_id in rejections]
        withheld = set(rejections) & {
            s.assertion_id for s in by_security[security_id] if s not in live
        }
        first = _sequence(security_id, live, anchor_date)
        if withheld or (rejected and not isinstance(first, _Break)):
            ids = sorted(withheld | {s.assertion_id for s in rejected})
            raise ValueError(
                f"{ids}: only a conflicting or ambiguous assertion can be rejected"
            )
        kept = [s for s in live if s.assertion_id not in rejections]
        result = first if not rejected else _sequence(security_id, kept, anchor_date)
        for statement in rejected:
            statuses[statement.assertion_id] = first.status
            rejected_by[statement.assertion_id] = rejections[statement.assertion_id]
        if isinstance(result, _Break):
            for statement in kept:
                statuses[statement.assertion_id] = result.status
            findings.append(_finding(security_id, result, live, ()))
            continue
        if isinstance(first, _Break):
            overrides = [rejected_by[s.assertion_id] for s in rejected]
            findings.append(_finding(security_id, first, live, overrides))
        for statement in kept:
            statuses[statement.assertion_id] = AssertionStatus.SUPPORTED
        intervals.extend(result)

    supports = {
        assertion_id: interval
        for interval in intervals
        for assertion_id in interval.assertion_ids
    }
    return Membership(
        statuses=statuses,
        rejected_by=rejected_by,
        intervals=tuple(intervals),
        supports=supports,
        findings=tuple(findings),
    )


def roster(intervals: Iterable[MembershipInterval], day: date) -> frozenset[str]:
    """The securities whose intervals contain ``day``."""
    return frozenset(i.security_id for i in intervals if i.contains(day))


def count_findings(
    intervals: tuple[MembershipInterval, ...],
    *,
    anchor_date: date | None,
    cutoff: date,
    expected: int,
) -> tuple[Finding, ...]:
    """A blocking finding for each date, from the anchor's to the cutoff, on which
    the roster changes to a size other than ``expected``."""
    if anchor_date is None:
        return ()
    bounds = {
        bound
        for interval in intervals
        for bound in (interval.effective_from, interval.effective_to)
        if bound is not None and anchor_date < bound <= cutoff
    }
    findings = []
    for day in sorted({anchor_date, *bounds}):
        members = sorted(roster(intervals, day))
        if len(members) != expected:
            findings.append(
                make_finding(
                    FindingKind.MEMBER_COUNT,
                    day.isoformat(),
                    f"{len(members)} members on {day}, expected {expected}:"
                    f" {', '.join(members) or 'none'}",
                    blocking=True,
                )
            )
    return tuple(findings)
