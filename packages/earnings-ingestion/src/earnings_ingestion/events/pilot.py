"""``djia-pilot/1``: the feasibility pilot, drawn by rule from a frozen event manifest
(the Stage 5 spec, §Pilot selection, step 5; EV4, EV8).

- **Inputs.** ``E`` is the event manifest's ``eligible`` rows, and ``U`` their
  issuers. The membership transitions come from the universe manifest the event
  manifest read, which must have the operative hash it records (plan 7, P7-20). No
  acquisition, parse, or later outcome is an input.
- **Seed and order.** The seed is the SHA-256 of the canonical JSON of the event
  manifest's content hash, the policy's name, and the universe's operative hash.
  ``h(x)`` is the SHA-256 of ``<seed>:<x>``. Every order and tie uses ``h``, so the
  input's row order cannot matter.
- **Guards.** More than 40 issuers refuses with ``scope_decision_needed``, and fewer
  than 20 events with ``blocked``. From 20 to 39 events, the target is every event,
  and the pilot is ``underfilled``. Otherwise the target is 40.
- **Steps.** Issuer coverage; membership boundaries; quarter coverage, which refuses
  with ``quarter_uncovered`` when a quarter has no eligible event; a refusal with
  ``mandatory_overflow`` when those steps take more than the target; and the
  longitudinal fill.
- **Transitions.** An issuer's membership is the union of its securities' intervals,
  by day. An entry is a start, not an ``anchor_snapshot``, whose day before no
  interval of the issuer holds. An exit is an end whose day no interval holds. So a
  second security joining a member issuer is neither, and nor is a same-day handoff.
  Those dated in ``[period_end_start, public_information_cutoff]`` are in scope. The
  member side of an entry is on or after its date, and of an exit on or before it:
  eligibility has already placed each release against the bound's timing. It stays
  within the membership spell the transition opens or closes, so an event of another
  spell never represents it: an entry's reaches up to the issuer's next exit in
  scope, and an exit's back to its previous entry in scope, both ends included. This
  clarifies ``djia-pilot/1`` (2026-09-27); it moves no v1 record.

Freezing follows the event manifest's rules (P6-14). Loading rechecks the chain: the
pilot's hash and name, the event manifest it names, and that manifest's universe,
whose operative hash is computed again.
"""

from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from pathlib import Path

from earnings_core import sha256_hex

from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.freeze import repeated_content
from earnings_ingestion.cohort.identity import operative_hash
from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.events.acceptance import EASTERN
from earnings_ingestion.events.build import EPOCH
from earnings_ingestion.events.eligibility import span
from earnings_ingestion.events.freeze import (
    load_event_manifest,
    manifest_path,
    serialize,
)
from earnings_ingestion.events.records import (
    EventManifest,
    EventManifestDefinition,
    EventRow,
    EventStatus,
    MembershipTransition,
    PilotDefinition,
    PilotManifest,
    PilotRow,
    SelectionReason,
    TransitionKind,
    content_hash,
    pilot_content_hash,
)
from earnings_ingestion.fetch.store import write_new

PILOT_POLICY = "djia-pilot/1"
PILOT_SIZE = 40
MINIMUM_EVENTS = 20


class PilotRefusal(StrEnum):
    SCOPE_DECISION_NEEDED = "scope_decision_needed"
    BLOCKED = "blocked"
    QUARTER_UNCOVERED = "quarter_uncovered"
    MANDATORY_OVERFLOW = "mandatory_overflow"


class PilotRefused(ValueError):
    """``djia-pilot/1`` refuses: nothing is selected, and nothing is written."""

    def __init__(self, reason: PilotRefusal, detail: str) -> None:
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}: {detail}")


def pilot_seed(
    event_manifest_hash: str, universe_operative_hash: str, policy: str = PILOT_POLICY
) -> str:
    """The seed: SHA-256 of the canonical JSON of the three inputs (EV4)."""
    return digest(
        {
            "eligible_event_manifest_hash": event_manifest_hash,
            "selection_policy_version": policy,
            "universe_operative_hash": universe_operative_hash,
        }
    )


def ordering(seed: str) -> Callable[[str], str]:
    """``h``: SHA-256 of the UTF-8 string ``<seed>:<x>``."""
    return lambda x: sha256_hex(f"{seed}:{x}".encode())


def quarter(day: date) -> str:
    """The calendar quarter of ``day``, such as ``2024Q3``."""
    return f"{day.year}Q{(day.month - 1) // 3 + 1}"


def quarters(start: date, stop: date) -> tuple[str, ...]:
    """The calendar quarters of the period ends in ``[start, stop)``."""
    found = []
    year, number = start.year, (start.month - 1) // 3 + 1
    while date(year, 3 * number - 2, 1) < stop:
        found.append(f"{year}Q{number}")
        year, number = (year + 1, 1) if number == 4 else (year, number + 1)
    return tuple(found)


def transitions(universe: UniverseManifest) -> tuple[MembershipTransition, ...]:
    """The universe's issuer-level entries and exits in scope, sorted by date, issuer,
    and kind."""
    definition = universe.definition
    start, cutoff = definition.period_end_start, definition.public_information_cutoff
    actions = {
        a.membership_assertion_id: a.asserted_action for a in universe.assertions
    }
    found: dict[tuple[date, str, TransitionKind], set[str]] = {}
    for issuer in universe.issuers:
        held = [i for i in universe.intervals if i.security_id in issuer.security_ids]
        for interval in held:
            bounds = span(interval, actions)
            day = interval.effective_from
            if not bounds.anchor and not any(
                other.contains(day - timedelta(days=1)) for other in held
            ):
                key = (day, issuer.issuer_id, TransitionKind.ENTRY)
                found.setdefault(key, set()).update(bounds.start.assertion_ids)
            day = interval.effective_to
            if day is not None and not any(other.contains(day) for other in held):
                key = (day, issuer.issuer_id, TransitionKind.EXIT)
                found.setdefault(key, set()).update(bounds.end.assertion_ids)
    return tuple(
        MembershipTransition(
            issuer_id=issuer_id,
            kind=kind,
            effective_date=day,
            assertion_ids=tuple(sorted(ids)),
        )
        for (day, issuer_id, kind), ids in sorted(found.items())
        if start <= day <= cutoff
    )


def _published(row: EventRow) -> date:
    return row.first_publication_time.astimezone(EASTERN).date()


def _member_side(
    transition: MembershipTransition,
    moves: Sequence[MembershipTransition],
    events: list[EventRow],
    h: Callable[[str], str],
) -> EventRow | None:
    """The transition's nearest eligible event on its member side, if any, within
    the membership spell it opens or closes. Among ``moves``, the issuer's next exit
    ends an entry's spell, and its previous entry starts an exit's; both ends are
    included."""
    day = transition.effective_date
    own = [move for move in moves if move.issuer_id == transition.issuer_id]
    exits = [m.effective_date for m in own if m.kind is TransitionKind.EXIT]
    entries = [m.effective_date for m in own if m.kind is TransitionKind.ENTRY]
    if transition.kind is TransitionKind.ENTRY:
        until = min((d for d in exits if d > day), default=date.max)
        after = [row for row in events if day <= _published(row) <= until]
        return min(
            after,
            key=lambda row: (row.first_publication_time, h(row.event_id)),
            default=None,
        )
    since = max((d for d in entries if d < day), default=date.min)
    before = [row for row in events if since <= _published(row) <= day]
    return min(
        before,
        key=lambda row: (-row.first_publication_time.timestamp(), h(row.event_id)),
        default=None,
    )


@dataclass(frozen=True)
class Selection:
    target: int
    underfilled: bool
    rows: tuple[PilotRow, ...]
    unmatched_transitions: tuple[MembershipTransition, ...]


def select(
    rows: Iterable[EventRow],
    transitions: Iterable[MembershipTransition],
    seed: str,
    *,
    start: date,
    stop: date,
) -> Selection:
    """Run the guards and the five steps over ``rows``' eligible events, whose period
    ends lie in ``[start, stop)``."""
    h = ordering(seed)
    eligible = sorted(
        (row for row in rows if row.eligibility_status is EventStatus.ELIGIBLE),
        key=lambda row: row.event_id,
    )
    by_issuer: dict[str, list[EventRow]] = {}
    for row in eligible:
        by_issuer.setdefault(row.issuer_id, []).append(row)
    if len(by_issuer) > PILOT_SIZE:
        raise PilotRefused(
            PilotRefusal.SCOPE_DECISION_NEEDED,
            f"{len(by_issuer)} issuers have eligible events, more than {PILOT_SIZE}",
        )
    if len(eligible) < MINIMUM_EVENTS:
        raise PilotRefused(
            PilotRefusal.BLOCKED,
            f"{len(eligible)} eligible events, fewer than {MINIMUM_EVENTS}",
        )
    underfilled = len(eligible) < PILOT_SIZE
    target = len(eligible) if underfilled else PILOT_SIZE

    chosen: list[tuple[EventRow, SelectionReason]] = []
    selected: set[str] = set()
    per_quarter: Counter[str] = Counter()
    per_issuer: Counter[str] = Counter()

    def take(row: EventRow, reason: SelectionReason) -> None:
        chosen.append((row, reason))
        selected.add(row.event_id)
        per_quarter[quarter(row.period_end)] += 1
        per_issuer[row.issuer_id] += 1

    for issuer in sorted(by_issuer, key=h):
        row = min(
            by_issuer[issuer],
            key=lambda r: (per_quarter[quarter(r.period_end)], h(r.event_id)),
        )
        take(row, SelectionReason.ISSUER_COVERAGE)

    unmatched, boundary = [], []
    moves = sorted(transitions, key=lambda t: (t.effective_date, t.issuer_id, t.kind))
    for transition in moves:
        events = by_issuer.get(transition.issuer_id, [])
        row = _member_side(transition, moves, events, h)
        if row is None:
            unmatched.append(transition)
        else:
            boundary.append(((transition.effective_date, h(row.event_id)), row))
    for _, row in sorted(boundary, key=lambda pair: pair[0]):
        if row.event_id not in selected:
            take(row, SelectionReason.MEMBERSHIP_BOUNDARY)

    window = quarters(start, stop)
    held = {quarter(row.period_end) for row in eligible}
    if empty := [q for q in window if q not in held]:
        raise PilotRefused(
            PilotRefusal.QUARTER_UNCOVERED, f"no eligible event in {', '.join(empty)}"
        )
    for each in window:
        if per_quarter[each]:
            continue
        row = min(
            (r for r in eligible if quarter(r.period_end) == each),
            key=lambda r: (per_issuer[r.issuer_id], h(r.event_id)),
        )
        take(row, SelectionReason.QUARTER_COVERAGE)

    if len(chosen) > target:
        raise PilotRefused(
            PilotRefusal.MANDATORY_OVERFLOW,
            f"steps 1 to 3 take {len(chosen)} events, more than the target {target}",
        )

    while len(chosen) < target:
        left = {
            issuer: [r for r in events if r.event_id not in selected]
            for issuer, events in by_issuer.items()
        }
        left = {issuer: events for issuer, events in left.items() if events}
        fewest = min(per_issuer[issuer] for issuer in left)
        pool = [
            r for i, events in left.items() if per_issuer[i] == fewest for r in events
        ]

        def distance(row: EventRow) -> int:
            return min(
                abs((row.period_end - taken.period_end).days)
                for taken, _ in chosen
                if taken.issuer_id == row.issuer_id
            )

        row = min(pool, key=lambda r: (-distance(r), h(r.event_id)))
        take(row, SelectionReason.LONGITUDINAL_FILL)

    return Selection(
        target=target,
        underfilled=underfilled,
        rows=tuple(
            PilotRow(event_id=row.event_id, selection_order=n, selection_reason=reason)
            for n, (row, reason) in enumerate(chosen, 1)
        ),
        unmatched_transitions=tuple(unmatched),
    )


@dataclass(frozen=True)
class Pilot:
    """A selection, and what it was drawn from: ready to freeze."""

    events: EventManifestDefinition
    universe_version: int
    seed: str
    selection: Selection

    @property
    def pilot_id(self) -> str:
        """``<corpus_id>-pilot``: the corpus alone, whatever the policy."""
        return f"{self.events.corpus_id}-pilot"

    def manifest(self, version: int, created_at: datetime) -> PilotManifest:
        events, selection = self.events, self.selection
        draft = PilotManifest(
            definition=PilotDefinition(
                pilot_id=self.pilot_id,
                pilot_version=version,
                universe_version=self.universe_version,
                universe_operative_hash=events.universe_operative_hash,
                event_manifest_version=events.event_manifest_version,
                eligible_event_manifest_hash=events.content_hash,
                selection_policy_version=PILOT_POLICY,
                selection_seed=self.seed,
                target=selection.target,
                underfilled=selection.underfilled,
                content_hash="0" * 64,
                created_at=created_at,
            ),
            rows=selection.rows,
            unmatched_transitions=selection.unmatched_transitions,
        )
        hashed = draft.definition.model_copy(
            update={"content_hash": pilot_content_hash(draft)}
        )
        return draft.model_copy(update={"definition": hashed})

    @property
    def content_hash(self) -> str:
        return self.manifest(1, EPOCH).definition.content_hash


def select_pilot(events: EventManifest, universe: UniverseManifest) -> Pilot:
    """``djia-pilot/1`` over a frozen event manifest and the universe it read."""
    definition = events.definition
    if content_hash(events) != definition.content_hash:
        raise ValueError("the event manifest does not hash to its content_hash")
    operative = operative_hash(universe)
    if operative != definition.universe_operative_hash:
        raise ValueError(
            "the universe's operative hash is not the one the event manifest read"
        )
    named = universe.definition.selection_policy_version
    if named != PILOT_POLICY:
        raise ValueError(f"the universe names {named}, not {PILOT_POLICY}")
    seed = pilot_seed(definition.content_hash, operative)
    selection = select(
        events.rows,
        transitions(universe),
        seed,
        start=universe.definition.period_end_start,
        stop=universe.definition.period_end_stop,
    )
    return Pilot(
        events=definition,
        universe_version=universe.definition.universe_version,
        seed=seed,
        selection=selection,
    )


@dataclass(frozen=True)
class FrozenPilot:
    manifest: PilotManifest
    path: Path
    created: bool
    """False when an existing version already held this content."""


def pilot_path(directory: Path, version: int) -> Path:
    return directory / f"pilot-v{version}.json"


def check_chain(
    manifest: PilotManifest, directory: Path, universe: UniverseManifest
) -> EventManifest:
    """The event manifest ``manifest`` names, in ``directory``, once the chain to it
    and to ``universe`` checks."""
    definition = manifest.definition
    path = manifest_path(directory, definition.event_manifest_version)
    if not path.exists():
        raise ValueError(f"{path.name}, which the pilot names, is not in {directory}")
    events = load_event_manifest(path)
    if events.definition.content_hash != definition.eligible_event_manifest_hash:
        raise ValueError(f"{path.name} is not the event manifest the pilot names")
    hashes = {
        operative_hash(universe),
        definition.universe_operative_hash,
        events.definition.universe_operative_hash,
    }
    if len(hashes) != 1:
        raise ValueError(
            "the universe's operative hash is not the one the pilot and its event"
            " manifest read"
        )
    seed = pilot_seed(
        definition.eligible_event_manifest_hash,
        definition.universe_operative_hash,
        definition.selection_policy_version,
    )
    if seed != definition.selection_seed:
        raise ValueError("selection_seed does not recompute from its inputs")
    eligible = {
        row.event_id
        for row in events.rows
        if row.eligibility_status is EventStatus.ELIGIBLE
    }
    if strays := [
        row.event_id for row in manifest.rows if row.event_id not in eligible
    ]:
        raise ValueError(f"not eligible events of {path.name}: {strays}")
    return events


def _read_pilot(path: Path) -> PilotManifest:
    """A frozen pilot, refused unless its hash and its name check."""
    manifest = PilotManifest.model_validate_json(path.read_bytes())
    definition = manifest.definition
    if pilot_content_hash(manifest) != definition.content_hash:
        raise ValueError(f"{path} does not hash to its content_hash")
    if path.name != pilot_path(path.parent, definition.pilot_version).name:
        raise ValueError(f"{path} holds version {definition.pilot_version}")
    return manifest


def load_pilot(path: Path, universe: UniverseManifest) -> PilotManifest:
    """A frozen pilot, refused unless its hash, its name, and its chain check."""
    manifest = _read_pilot(path)
    check_chain(manifest, path.parent, universe)
    return manifest


def frozen_pilots(directory: Path) -> list[PilotManifest]:
    """Every frozen version in ``directory``, oldest first, each refused unless its
    hash and its name check. Versions may have read different universes, so their
    chains are not checked here: ``load_pilot`` checks one's. Refused if they name
    more than one ``pilot_id``, which is ``<corpus_id>-pilot`` whatever the policy
    (a file names its version, not its corpus), or if two hold one content (PR #6's
    review, F22)."""
    pilots = sorted(
        (_read_pilot(path) for path in directory.glob("pilot-v*.json")),
        key=lambda m: m.definition.pilot_version,
    )
    if len(named := sorted({m.definition.pilot_id for m in pilots})) > 1:
        raise ValueError(f"{directory} holds more than one pilot: {named}")
    repeated_content(
        [
            (
                pilot_path(directory, m.definition.pilot_version).name,
                m.definition.content_hash,
            )
            for m in pilots
        ]
    )
    return pilots


def freeze_pilot(
    pilot: Pilot, universe: UniverseManifest, directory: Path, *, now: datetime
) -> FrozenPilot:
    """Freeze ``pilot`` beside the event manifest it names, or return the version
    that holds it. Either way, the chain of the version returned checks against
    ``universe``; earlier versions read under another universe do not block. Refused
    if ``directory`` holds another corpus's pilot."""
    existing = frozen_pilots(directory)
    if existing and (held := existing[0].definition.pilot_id) != pilot.pilot_id:
        raise ValueError(f"{directory} holds {held}, not {pilot.pilot_id}")
    for manifest in existing:
        if manifest.definition.content_hash == pilot.content_hash:
            check_chain(manifest, directory, universe)
            version = manifest.definition.pilot_version
            return FrozenPilot(manifest, pilot_path(directory, version), created=False)
    version = 1 + max((m.definition.pilot_version for m in existing), default=0)
    manifest = pilot.manifest(version, now)
    check_chain(manifest, directory, universe)
    write_new(pilot_path(directory, version), serialize(manifest))
    return FrozenPilot(manifest, pilot_path(directory, version), created=True)
