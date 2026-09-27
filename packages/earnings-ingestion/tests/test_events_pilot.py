"""djia-pilot/1 (the Stage 5 spec, §Pilot selection; SV10 to SV12): the selection
paths on event rows built directly, and the underfilled pilot of the synthetic event
layer, frozen beside its event manifest and loaded with its chain."""

import random
import shutil
from collections import Counter
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.identity import operative_hash
from earnings_ingestion.cohort.records import BoundTiming, UniverseManifest
from earnings_ingestion.events.build import build_events
from earnings_ingestion.events.freeze import (
    freeze_events,
    load_event_manifest,
    serialize,
)
from earnings_ingestion.events.layer import review, write_layer
from earnings_ingestion.events.pilot import (
    Pilot,
    PilotRefusal,
    PilotRefused,
    freeze_pilot,
    frozen_pilots,
    load_pilot,
    ordering,
    pilot_path,
    pilot_seed,
    quarter,
    quarters,
    select,
    select_pilot,
    transitions,
)
from earnings_ingestion.events.records import (
    EventManifest,
    EventManifestDefinition,
    EventOverridesFile,
    EventReason,
    EventRow,
    EventStatus,
    IdentificationMethod,
    MembershipTransition,
    SelectionReason,
    TransitionKind,
    content_hash,
    pilot_content_hash,
)
from earnings_ingestion.events.saved import SavedResponses

ROOT = Path(__file__).resolve().parents[3]
COHORT = ROOT / "tests" / "fixtures" / "cohort" / "manifests" / "djia-synthetic-v1.json"
NOW = datetime(2026, 9, 28, 18, 0, tzinfo=UTC)
START, STOP = date(2024, 7, 1), date(2026, 7, 1)
ENDS = (
    date(2024, 9, 30),
    date(2024, 12, 31),
    date(2025, 3, 31),
    date(2025, 6, 30),
    date(2025, 9, 30),
    date(2025, 12, 31),
    date(2026, 3, 31),
    date(2026, 6, 30),
)
SEED = pilot_seed("a" * 64, "b" * 64)
ENTRY, EXIT = TransitionKind.ENTRY, TransitionKind.EXIT
BOUNDARY = SelectionReason.MEMBERSHIP_BOUNDARY
ELIGIBLE = EventStatus.ELIGIBLE


def event(issuer: int, period_end: date) -> EventRow:
    """An eligible event, published 25 days after its period end."""
    cik = f"{issuer:010d}"
    published = datetime.combine(period_end + timedelta(days=25), time(20, 5), UTC)
    release = f"{cik}-{period_end:%y}-{period_end.month:06d}"
    return EventRow(
        event_id=f"cik-{cik}:{period_end.isoformat()}",
        issuer_id=f"cik-{cik}",
        cik=cik,
        period_end=period_end,
        reported_fiscal_year=None,
        reported_fiscal_quarter=None,
        periodic_accession=f"{cik}-{period_end:%y}-{period_end.month + 100:06d}",
        periodic_form="10-Q",
        release_accession=release,
        candidate_accessions=(release,),
        identification_method=IdentificationMethod.STATED_PERIOD,
        filing_acceptance_time=published,
        first_publication_time=published,
        source_timezone="America/New_York",
        first_publication_source_id="sec-edgar",
        membership_assertion_id=f"added-{issuer}",
        eligibility_status=EventStatus.ELIGIBLE,
        eligibility_reason=EventReason.MEMBER_AT_PUBLICATION,
        retained=False,
        override_ids=(),
    )


def ineligible(issuer: int, period_end: date) -> EventRow:
    return event(issuer, period_end).model_copy(
        update={
            "eligibility_status": EventStatus.INELIGIBLE,
            "eligibility_reason": EventReason.NOT_MEMBER_AT_PUBLICATION,
        }
    )


def transition(issuer: int, kind: TransitionKind, day: date) -> MembershipTransition:
    return MembershipTransition(
        issuer_id=f"cik-{issuer:010d}",
        kind=kind,
        effective_date=day,
        assertion_ids=(f"{kind}-{issuer}",),
    )


def forty() -> tuple[list[EventRow], list[MembershipTransition]]:
    """76 eligible events of ten issuers, and eight ineligible ones of an eleventh.
    Issuers 1 and 2 enter on 2024-10-01 and leave on 2026-03-01, so their events run
    from 2024Q3 through 2025Q4, and each one's two transitions have different
    targets: step 1 takes one event per issuer, so step 2 must add a row."""
    rows = [event(n, end) for n in (1, 2) for end in ENDS[:6]]
    rows += [event(n, end) for n in range(3, 11) for end in ENDS]
    rows += [ineligible(11, end) for end in ENDS]
    moves = [
        transition(n, kind, day)
        for n in (1, 2)
        for kind, day in ((ENTRY, date(2024, 10, 1)), (EXIT, date(2026, 3, 1)))
    ]
    return rows, moves


def run(rows, moves=()):
    return select(rows, moves, SEED, start=START, stop=STOP)


STEPS = list(SelectionReason)


def obeys_the_steps(events: list[EventRow], rows, seed: str) -> None:
    """Replay the pilot: the steps come in order, and each row of steps 1, 3, and 5
    is the choice its rule makes at that moment, with ties broken by ``h``."""
    h = ordering(seed)
    eligible = {e.event_id: e for e in events if e.eligibility_status is ELIGIBLE}
    reasons = [row.selection_reason for row in rows]
    assert reasons == sorted(reasons, key=STEPS.index)
    covered = [
        eligible[row.event_id].issuer_id
        for row in rows
        if row.selection_reason is SelectionReason.ISSUER_COVERAGE
    ]
    assert covered == sorted({e.issuer_id for e in eligible.values()}, key=h)
    taken: list[EventRow] = []
    for row in rows:
        chosen = eligible[row.event_id]
        per_quarter = Counter(quarter(e.period_end) for e in taken)
        per_issuer = Counter(e.issuer_id for e in taken)
        left = [e for e in eligible.values() if e not in taken]

        def distance(event: EventRow) -> int:
            return min(
                abs((event.period_end - e.period_end).days)
                for e in taken
                if e.issuer_id == event.issuer_id
            )

        expected = chosen
        if row.selection_reason is SelectionReason.ISSUER_COVERAGE:
            own = [e for e in left if e.issuer_id == chosen.issuer_id]
            expected = min(
                own, key=lambda e: (per_quarter[quarter(e.period_end)], h(e.event_id))
            )
        elif row.selection_reason is SelectionReason.QUARTER_COVERAGE:
            earlier = [
                q for q in quarters(START, STOP) if q < quarter(chosen.period_end)
            ]
            assert all(per_quarter[q] for q in earlier)
            assert per_quarter[quarter(chosen.period_end)] == 0
            same = [
                e for e in left if quarter(e.period_end) == quarter(chosen.period_end)
            ]
            expected = min(same, key=lambda e: (per_issuer[e.issuer_id], h(e.event_id)))
        elif row.selection_reason is SelectionReason.LONGITUDINAL_FILL:
            fewest = min(per_issuer[e.issuer_id] for e in left)
            pool = [e for e in left if per_issuer[e.issuer_id] == fewest]
            expected = min(pool, key=lambda e: (-distance(e), h(e.event_id)))
        assert chosen == expected
        taken.append(chosen)


def test_the_seed_is_the_hash_of_its_three_inputs() -> None:
    canonical = (
        '{"eligible_event_manifest_hash":"' + "a" * 64 + '",'
        '"selection_policy_version":"djia-pilot/1",'
        '"universe_operative_hash":"' + "b" * 64 + '"}'
    )
    assert SEED == sha256_hex(canonical.encode())
    assert ordering(SEED)("cik-0000000001") == sha256_hex(
        f"{SEED}:cik-0000000001".encode()
    )
    assert quarters(START, STOP) == (
        "2024Q3",
        "2024Q4",
        "2025Q1",
        "2025Q2",
        "2025Q3",
        "2025Q4",
        "2026Q1",
        "2026Q2",
    )


def test_with_40_or_more_eligible_events_the_pilot_holds_exactly_40() -> None:
    rows, moves = forty()
    chosen = run(rows, moves)
    assert (chosen.target, chosen.underfilled, len(chosen.rows)) == (40, False, 40)
    assert [row.selection_order for row in chosen.rows] == list(range(1, 41))
    events = {row.event_id: row for row in rows}
    picked = [events[row.event_id] for row in chosen.rows]
    assert {row.issuer_id for row in picked} == {f"cik-{n:010d}" for n in range(1, 11)}
    assert {quarter(row.period_end) for row in picked} == set(quarters(START, STOP))
    obeys_the_steps(rows, chosen.rows, SEED)
    dates = {
        f"cik-{n:010d}:{end}": day
        for n in (1, 2)
        for end, day in (
            ("2024-09-30", date(2024, 10, 1)),
            ("2025-12-31", date(2026, 3, 1)),
        )
    }
    reasons = {row.event_id: row.selection_reason for row in chosen.rows}
    for n in (1, 2):
        ends = [f"cik-{n:010d}:2024-09-30", f"cik-{n:010d}:2025-12-31"]
        assert BOUNDARY in {reasons[target] for target in ends}
    added = [e for e, reason in reasons.items() if reason is BOUNDARY]
    h = ordering(SEED)
    assert added == sorted(added, key=lambda e: (dates[e], h(e)))
    assert Counter(reasons.values()) == {
        SelectionReason.ISSUER_COVERAGE: 10,
        SelectionReason.MEMBERSHIP_BOUNDARY: 4,
        SelectionReason.LONGITUDINAL_FILL: 26,
    }
    assert set(Counter(row.issuer_id for row in picked).values()) == {4}
    assert chosen.unmatched_transitions == ()


@pytest.mark.parametrize(
    ("count", "target"), [(19, None), (20, 20), (39, 39), (40, 40)]
)
def test_the_event_count_guards(count, target) -> None:
    """Issuer-major, so the first 20 events already span all eight quarters."""
    rows = [event(n, end) for n in range(1, 6) for end in ENDS][:count]
    if target is None:
        with pytest.raises(PilotRefused) as refused:
            run(rows)
        assert refused.value.reason is PilotRefusal.BLOCKED
        assert str(refused.value) == "blocked: 19 eligible events, fewer than 20"
        return
    chosen = run(rows)
    assert (chosen.target, chosen.underfilled) == (target, target < 40)
    assert {row.event_id for row in chosen.rows} == {row.event_id for row in rows}


@pytest.mark.parametrize("issuers", [40, 41])
def test_more_than_40_issuers_needs_a_scope_decision(issuers) -> None:
    rows = [event(n, ENDS[n % 8]) for n in range(1, issuers + 1)]
    if issuers == 40:
        chosen = run(rows)
        reasons = {row.selection_reason for row in chosen.rows}
        assert (len(chosen.rows), reasons) == (40, {SelectionReason.ISSUER_COVERAGE})
        return
    with pytest.raises(PilotRefused) as refused:
        run(rows)
    assert str(refused.value) == (
        "scope_decision_needed: 41 issuers have eligible events, more than 40"
    )


def test_mandatory_cases_beyond_the_target_refuse_before_filling() -> None:
    """Forty issuers, and issuer 1's entry and exit have different targets: step 1
    takes 40 events, and step 2 must add the other."""
    rows = [event(n, ENDS[n % 8]) for n in range(2, 41)]
    rows += [event(1, ENDS[1]), event(1, ENDS[2])]
    moves = [
        transition(1, ENTRY, date(2025, 1, 1)),
        transition(1, EXIT, date(2025, 5, 1)),
    ]
    with pytest.raises(PilotRefused) as refused:
        run(rows, moves)
    assert str(refused.value) == (
        "mandatory_overflow: steps 1 to 3 take 41 events, more than the target 40"
    )


def test_a_quarter_with_no_eligible_event_refuses() -> None:
    kept = [end for n, end in enumerate(ENDS) if n not in (3, 6)]
    rows = [event(n, end) for n in range(1, 6) for end in kept]
    with pytest.raises(PilotRefused) as refused:
        run(rows)
    assert str(refused.value) == (
        "quarter_uncovered: no eligible event in 2025Q2, 2026Q1"
    )


def on(row: EventRow, published: datetime) -> EventRow:
    """``row``, accepted and first published at ``published``."""
    return row.model_copy(
        update={
            "filing_acceptance_time": published,
            "first_publication_time": published,
        }
    )


@pytest.mark.parametrize(
    ("kind", "published"),
    [
        (ENTRY, datetime(2025, 5, 1, 18, 0, tzinfo=UTC)),
        (EXIT, datetime(2025, 5, 1, 14, 0, tzinfo=UTC)),
    ],
    ids=["entry", "exit"],
)
def test_the_member_side_includes_the_transitions_own_day(kind, published) -> None:
    """P7-20: the member side includes the transition's own Eastern date, since
    eligibility has already placed a same-day release against the bound's timing.
    Issuer 12's only eligible event is published on that day, so the transition is
    matched."""
    rows, moves = forty()
    move = transition(12, kind, date(2025, 5, 1))
    chosen = run([*rows, on(event(12, date(2025, 3, 31)), published)], [*moves, move])
    assert move not in chosen.unmatched_transitions


def others() -> list[EventRow]:
    """Issuers 3 to 10, members throughout, with an eligible event in every
    quarter."""
    return [event(n, end) for n in range(3, 11) for end in ENDS]


def test_an_exit_is_matched_only_within_the_spell_it_closes() -> None:
    """Issuer 1 leaves on 2025-03-01, returns on 2025-05-01, and leaves again on
    2025-06-01, with no release in its second spell. Both bounds of that spell are
    reported: the release of 2025-01-25 is the first spell's, not the second's."""
    rows = [event(1, end) for end in ENDS[:2]] + others()
    moves = [
        transition(1, EXIT, date(2025, 3, 1)),
        transition(1, ENTRY, date(2025, 5, 1)),
        transition(1, EXIT, date(2025, 6, 1)),
    ]
    assert run(rows, moves).unmatched_transitions == tuple(moves[1:])


def test_an_entry_is_matched_only_within_the_spell_it_opens() -> None:
    """Issuer 1 joins on 2025-03-01, leaves on 2025-04-01, and returns on
    2025-10-01, with no release in its first spell. Both bounds of that spell are
    reported: the release of 2025-10-25 is the later spell's."""
    rows = [event(1, end) for end in ENDS[4:]] + others()
    moves = [
        transition(1, ENTRY, date(2025, 3, 1)),
        transition(1, EXIT, date(2025, 4, 1)),
        transition(1, ENTRY, date(2025, 10, 1)),
    ]
    assert run(rows, moves).unmatched_transitions == tuple(moves[:2])


def test_an_entry_adds_its_target_in_the_order_of_the_spell_it_opens() -> None:
    """Issuer 21's release of 2025-10-25 is the target of its entry of 2025-10-01,
    not of its entry of 2025-03-01, whose spell is empty. So issuer 22's target,
    from its exit of 2025-06-01, is added first. Under ``SEED``, step 1 takes
    neither target."""
    rows = [event(21, end) for end in ENDS[4:]]
    rows += [event(22, end) for end in ENDS[:3]] + others()
    moves = [
        transition(21, ENTRY, date(2025, 3, 1)),
        transition(21, EXIT, date(2025, 4, 1)),
        transition(22, EXIT, date(2025, 6, 1)),
        transition(21, ENTRY, date(2025, 10, 1)),
    ]
    chosen = run(rows, moves)
    added = [row.event_id for row in chosen.rows if row.selection_reason is BOUNDARY]
    assert added == ["cik-0000000022:2025-03-31", "cik-0000000021:2025-09-30"]
    assert chosen.unmatched_transitions == tuple(moves[:2])


@pytest.mark.parametrize(
    "published",
    [datetime(2025, 5, 1, 18, 0, tzinfo=UTC), datetime(2025, 6, 2, 14, 0, tzinfo=UTC)],
    ids=["on-the-entry", "on-the-exit"],
)
def test_a_spell_includes_both_of_its_bounds(published) -> None:
    """Issuer 12 is a member from 2025-05-01 to 2025-06-02, and its only eligible
    event is published on one of those days, so both transitions are matched."""
    rows, moves = forty()
    spell = [
        transition(12, ENTRY, date(2025, 5, 1)),
        transition(12, EXIT, date(2025, 6, 2)),
    ]
    row = on(event(12, date(2025, 3, 31)), published)
    assert run([*rows, row], [*moves, *spell]).unmatched_transitions == ()


def test_shuffled_input_gives_a_byte_identical_pilot() -> None:
    rows, moves = forty()
    events = EventManifestDefinition(
        corpus_id="djia-direct",
        event_manifest_version=1,
        universe_id="djia-direct",
        universe_version=1,
        universe_operative_hash="b" * 64,
        discovery_policy_version="release-id/1",
        eligibility_policy_version="eligibility/1",
        public_information_cutoff=date(2026, 9, 22),
        content_hash="a" * 64,
        created_at=NOW,
    )

    def pilot(rows, moves) -> bytes:
        return serialize(Pilot(events, 1, SEED, run(rows, moves)).manifest(1, NOW))

    first = pilot(rows, moves)
    for n in range(3):
        shuffled = list(rows)
        random.Random(n).shuffle(shuffled)
        assert pilot(shuffled, list(reversed(moves))) == first


@pytest.fixture(scope="module")
def universe() -> UniverseManifest:
    return load_manifest(COHORT)


@pytest.fixture(scope="module")
def frozen(universe, tmp_path_factory) -> Path:
    """The reviewed layer's event manifest, frozen in a corpus directory."""
    root = tmp_path_factory.mktemp("events")
    layer = write_layer(root / "data" / "raw" / "events", root)
    saved = SavedResponses(layer.store)

    def build(overrides=()):
        return build_events(
            universe,
            saved,
            EventOverridesFile(schema_version=1, overrides=overrides),
            corpus_id="djia-synthetic",
        )

    directory = root / "corpus"
    freeze_events(build(review(build())), saved, directory, now=NOW)
    return directory


@pytest.fixture
def corpus(frozen, tmp_path) -> Path:
    return Path(shutil.copytree(frozen, tmp_path / "corpus"))


def events_of(directory: Path) -> EventManifest:
    return load_event_manifest(directory / "events-v1.json")


def test_the_transitions_are_issuer_level_entries_and_exits_in_scope(universe) -> None:
    """Dynamo's class B joins a member issuer: no transition. Acme's removal is
    withheld, and the anchor starts are lower bounds: none either."""
    assert transitions(universe) == (
        MembershipTransition(
            issuer_id="cik-0009990002",
            kind=EXIT,
            effective_date=date(2024, 11, 8),
            assertion_ids=("index-2024-11-01:borealis-common:removed",),
        ),
        MembershipTransition(
            issuer_id="cik-0009990003",
            kind=ENTRY,
            effective_date=date(2024, 11, 8),
            assertion_ids=("index-2024-11-01:corvid-common:added",),
        ),
        MembershipTransition(
            issuer_id="cik-0009990006",
            kind=EXIT,
            effective_date=date(2026, 6, 22),
            assertion_ids=("index-2026-06-16:eastfield-common:removed",),
        ),
    )


def dynamo(universe: UniverseManifest, a_to: date, b_from: date) -> UniverseManifest:
    """The synthetic universe, with Dynamo's class A leaving on ``a_to`` and its class
    B joining on ``b_from``."""
    (eastfield,) = [
        a
        for a in universe.assertions
        if a.membership_assertion_id == "index-2026-06-16:eastfield-common:removed"
    ]
    removal = eastfield.model_copy(
        update={
            "membership_assertion_id": "index-2026-06-16:dynamo-class-a:removed",
            "security_id": "dynamo-class-a",
        }
    )
    intervals = []
    for interval in universe.intervals:
        if interval.security_id == "dynamo-class-a":
            interval = interval.model_copy(
                update={
                    "effective_to": a_to,
                    "effective_to_timing": BoundTiming.BEFORE_OPEN,
                    "assertion_ids": (
                        removal.membership_assertion_id,
                        *interval.assertion_ids,
                    ),
                }
            )
        elif interval.security_id == "dynamo-class-b":
            interval = interval.model_copy(update={"effective_from": b_from})
        intervals.append(interval)
    return universe.model_copy(
        update={
            "assertions": (*universe.assertions, removal),
            "intervals": tuple(intervals),
        }
    )


@pytest.mark.parametrize(
    ("a_to", "b_from", "expected"),
    [
        (date(2026, 6, 22), date(2026, 6, 22), []),
        (
            date(2026, 6, 22),
            date(2026, 6, 29),
            [(EXIT, date(2026, 6, 22)), (ENTRY, date(2026, 6, 29))],
        ),
        (date(2026, 9, 22), date(2026, 9, 23), [(EXIT, date(2026, 9, 22))]),
        (
            date(2024, 7, 1),
            date(2024, 7, 8),
            [(EXIT, date(2024, 7, 1)), (ENTRY, date(2024, 7, 8))],
        ),
    ],
    ids=["handoff", "gap", "cutoff", "start"],
)
def test_a_handoff_is_no_transition_and_a_gap_is_two(
    universe, a_to, b_from, expected
) -> None:
    """Scope is ``[period_end_start, public_information_cutoff]``, both ends
    included: an exit on 2024-07-01 and one on 2026-09-22 are in it."""
    found = transitions(dynamo(universe, a_to, b_from))
    assert [
        (t.kind, t.effective_date) for t in found if t.issuer_id == "cik-0009990005"
    ] == expected


def test_an_anchor_start_in_scope_is_never_an_entry(universe) -> None:
    """Acme's roster snapshot, moved into scope, is still a lower bound."""
    intervals = tuple(
        interval.model_copy(update={"effective_from": date(2024, 7, 2)})
        if interval.security_id == "acme-common"
        else interval
        for interval in universe.intervals
    )
    found = transitions(universe.model_copy(update={"intervals": intervals}))
    assert found == transitions(universe)


def test_the_synthetic_pilot_is_underfilled_and_takes_every_event(
    corpus, universe
) -> None:
    events = events_of(corpus)
    pilot = select_pilot(events, universe)
    chosen = pilot.selection
    eligible = {
        row.event_id: row
        for row in events.rows
        if row.eligibility_status is EventStatus.ELIGIBLE
    }
    assert (chosen.target, chosen.underfilled, len(eligible)) == (27, True, 27)
    assert {row.event_id for row in chosen.rows} == set(eligible)
    reasons = {row.event_id: row.selection_reason for row in chosen.rows}
    for target in ("cik-0009990003:2024-12-31", "cik-0009990006:2026-03-31"):
        assert reasons[target] in (BOUNDARY, SelectionReason.ISSUER_COVERAGE)
    assert [r.event_id for r in chosen.rows if r.selection_reason is BOUNDARY] == [
        "cik-0009990003:2024-12-31",
        "cik-0009990006:2026-03-31",
    ]
    assert Counter(reasons.values()) == {
        SelectionReason.ISSUER_COVERAGE: 4,
        SelectionReason.MEMBERSHIP_BOUNDARY: 2,
        SelectionReason.QUARTER_COVERAGE: 4,
        SelectionReason.LONGITUDINAL_FILL: 17,
    }
    assert [(t.issuer_id, t.kind) for t in chosen.unmatched_transitions] == [
        ("cik-0009990002", EXIT)
    ]
    obeys_the_steps(list(events.rows), chosen.rows, pilot.seed)
    assert len({row.issuer_id for row in eligible.values()}) == 4
    quartered = {quarter(row.period_end) for row in eligible.values()}
    assert quartered == set(quarters(START, STOP))


def test_the_pilot_freezes_beside_its_event_manifest(corpus, universe) -> None:
    pilot = select_pilot(events_of(corpus), universe)
    first = freeze_pilot(pilot, universe, corpus, now=NOW)
    assert (first.created, first.path.name) == (True, "pilot-v1.json")
    assert first.manifest.definition.pilot_id == "djia-synthetic-pilot"
    assert load_pilot(first.path, universe) == first.manifest
    again = freeze_pilot(pilot, universe, corpus, now=NOW)
    assert (again.created, again.path) == (False, first.path)
    assert sorted(path.name for path in corpus.iterdir()) == [
        "events-v1.evidence.json",
        "events-v1.json",
        "pilot-v1.json",
    ]


def moved(universe: UniverseManifest) -> UniverseManifest:
    intervals = tuple(
        interval.model_copy(update={"effective_from": date(2024, 11, 9)})
        if interval.security_id == "corvid-common"
        else interval
        for interval in universe.intervals
    )
    return universe.model_copy(update={"intervals": intervals})


@pytest.mark.parametrize(
    ("tamper", "message"),
    [
        ("rename", "holds version 1"),
        ("edit", "does not hash to its content_hash"),
        ("no events", "which the pilot names, is not in"),
        ("other events", "is not the event manifest the pilot names"),
        ("universe", "operative hash"),
        ("seed", "selection_seed does not recompute"),
        ("stray", "not eligible events of events-v1.json"),
    ],
)
def test_loading_rechecks_the_chain(
    corpus, universe, tmp_path, tamper, message
) -> None:
    frozen = freeze_pilot(
        select_pilot(events_of(corpus), universe), universe, corpus, now=NOW
    )
    path, reader = frozen.path, universe
    if tamper == "rename":
        path = corpus / "pilot-v2.json"
        shutil.copy(frozen.path, path)
    elif tamper == "edit":
        text = frozen.path.read_text().replace(
            '"underfilled": true', '"underfilled": false'
        )
        path = tmp_path / "pilot-v1.json"
        path.write_text(text)
    elif tamper == "no events":
        (tmp_path / "alone").mkdir()
        path = Path(shutil.copy(frozen.path, tmp_path / "alone" / "pilot-v1.json"))
    elif tamper == "other events":
        other = events_of(corpus)
        rows = tuple(
            row.model_copy(update={"reported_fiscal_quarter": "Q9"})
            if row.event_id == "cik-0009990001:2024-08-31"
            else row
            for row in other.rows
        )
        other = rehashed(other.model_copy(update={"rows": rows}))
        (tmp_path / "other").mkdir()
        (tmp_path / "other" / "events-v1.json").write_bytes(serialize(other))
        path = Path(shutil.copy(frozen.path, tmp_path / "other" / "pilot-v1.json"))
    elif tamper == "universe":
        reader = moved(universe)
    else:
        manifest = frozen.manifest
        if tamper == "seed":
            seed = manifest.definition.model_copy(update={"selection_seed": "c" * 64})
            manifest = manifest.model_copy(update={"definition": seed})
        else:
            first = manifest.rows[0].model_copy(
                update={"event_id": "cik-0009990002:2024-09-30"}
            )
            manifest = manifest.model_copy(update={"rows": (first, *manifest.rows[1:])})
        definition = manifest.definition.model_copy(
            update={"content_hash": pilot_content_hash(manifest)}
        )
        path.write_bytes(
            serialize(manifest.model_copy(update={"definition": definition}))
        )
    with pytest.raises(ValueError, match=message):
        load_pilot(path, reader)
    if tamper in ("rename", "edit"):
        with pytest.raises(ValueError, match=message):
            frozen_pilots(path.parent)


def rehashed(manifest: EventManifest) -> EventManifest:
    definition = manifest.definition.model_copy(
        update={"content_hash": content_hash(manifest)}
    )
    return manifest.model_copy(update={"definition": definition})


def test_select_pilot_reads_only_the_universe_its_event_manifest_read(
    corpus, universe
) -> None:
    """The policy's name is in the operative projection (EV4), so a universe naming
    another policy is refused even when an event manifest was built from it."""
    events = events_of(corpus)
    with pytest.raises(ValueError, match="operative hash"):
        select_pilot(events, moved(universe))
    other = universe.model_copy(
        update={
            "definition": universe.definition.model_copy(
                update={"selection_policy_version": "djia-pilot/2"}
            )
        }
    )
    read = events.definition.model_copy(
        update={"universe_operative_hash": operative_hash(other)}
    )
    built = rehashed(events.model_copy(update={"definition": read}))
    with pytest.raises(ValueError, match="names djia-pilot/2, not djia-pilot/1"):
        select_pilot(built, other)


def test_a_changed_event_fact_or_policy_reseeds_and_a_universe_version_does_not(
    corpus, universe
) -> None:
    """SV11 for the pilot (P7-2)."""
    events = events_of(corpus)
    pilot = select_pilot(events, universe)
    rows = tuple(
        row.model_copy(update={"reported_fiscal_quarter": "Q9"})
        if row.event_id == "cik-0009990001:2024-08-31"
        else row
        for row in events.rows
    )
    changed = select_pilot(rehashed(events.model_copy(update={"rows": rows})), universe)
    assert changed.seed != pilot.seed
    assert changed.content_hash != pilot.content_hash
    renumbered = universe.model_copy(
        update={
            "definition": universe.definition.model_copy(update={"universe_version": 2})
        }
    )
    again = select_pilot(events, renumbered)
    assert (again.seed, again.content_hash) == (pilot.seed, pilot.content_hash)
    assert again.manifest(1, NOW).definition.universe_version == 2
    assert pilot_seed("a" * 64, "b" * 64, "djia-pilot/2") != SEED
    manifest = pilot.manifest(1, NOW)
    policy = manifest.definition.model_copy(
        update={"selection_policy_version": "djia-pilot/2"}
    )
    assert pilot_content_hash(manifest.model_copy(update={"definition": policy})) != (
        manifest.definition.content_hash
    )


def test_a_new_event_manifest_version_gives_the_next_pilot(corpus, universe) -> None:
    first = freeze_pilot(
        select_pilot(events_of(corpus), universe), universe, corpus, now=NOW
    )
    events = events_of(corpus)
    rows = tuple(
        row.model_copy(update={"reported_fiscal_quarter": "Q9"})
        if row.event_id == "cik-0009990001:2024-08-31"
        else row
        for row in events.rows
    )
    definition = events.definition.model_copy(update={"event_manifest_version": 2})
    second = rehashed(
        events.model_copy(update={"rows": rows, "definition": definition})
    )
    (corpus / "events-v2.json").write_bytes(serialize(second))
    frozen = freeze_pilot(select_pilot(second, universe), universe, corpus, now=NOW)
    assert (frozen.created, frozen.path.name) == (True, "pilot-v2.json")
    assert frozen.manifest.definition.event_manifest_version == 2
    assert load_pilot(first.path, universe) == first.manifest
    assert pilot_path(corpus, 2) == frozen.path


def test_a_refrozen_universe_gives_the_next_pilot_beside_the_old_ones(
    corpus, universe
) -> None:
    """A cohort refrozen with changed facts has a new operative hash. Its pilot
    freezes as the next version beside the old universe's, and each loads with its
    own universe only."""
    first = freeze_pilot(
        select_pilot(events_of(corpus), universe), universe, corpus, now=NOW
    )
    refrozen = moved(universe)
    events = events_of(corpus)
    definition = events.definition.model_copy(
        update={
            "event_manifest_version": 2,
            "universe_operative_hash": operative_hash(refrozen),
        }
    )
    second = rehashed(events.model_copy(update={"definition": definition}))
    (corpus / "events-v2.json").write_bytes(serialize(second))
    frozen = freeze_pilot(select_pilot(second, refrozen), refrozen, corpus, now=NOW)
    assert (frozen.created, frozen.path.name) == (True, "pilot-v2.json")
    again = freeze_pilot(
        select_pilot(events_of(corpus), universe), universe, corpus, now=NOW
    )
    assert (again.created, again.path) == (False, first.path)
    assert frozen_pilots(corpus) == [first.manifest, frozen.manifest]
    assert load_pilot(first.path, universe) == first.manifest
    assert load_pilot(frozen.path, refrozen) == frozen.manifest
    with pytest.raises(ValueError, match="operative hash"):
        load_pilot(first.path, refrozen)
