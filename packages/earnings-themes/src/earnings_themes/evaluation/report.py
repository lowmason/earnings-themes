"""A partition's figures from its events' observations (the Stage 11 spec,
§Metrics; R12.2, R12.5, R12.7, R12.8, R12.10, R13.1).

The application gathers the observations from the runs (A8); this module reads
nothing and prints nothing.

- **Events are the clusters.** Every interval resamples whole events (R12.7). The
  label figures resample the events that hold labels.
- **Label figures** take the joint label for support precision and judge agreement,
  and the claim label for scorer AUC (FP21). A missing label leaves its target out;
  it is never a negative.
- **Not estimated.** Sector prevalence and source-selection bias are reported with
  their reason (R12.2, D1).
"""

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import combinations
from typing import Literal

from earnings_themes.codebook import Codebook
from earnings_themes.evaluation.agreement import cohen_kappa, fleiss_kappa, gwet_ac1
from earnings_themes.evaluation.align import Span, UnitIndex, units_over
from earnings_themes.evaluation.bootstrap import BootstrapPlan, estimate
from earnings_themes.evaluation.cells import (
    EventCells,
    GoldReading,
    event_cells,
    level_one,
)
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.evaluation.records import (
    Figure,
    Metric,
    PartitionReport,
    ReadingAgreement,
)
from earnings_themes.evaluation.scores import (
    Tally,
    char_counts,
    evidence_recall_counts,
    f1,
    gs5_shares,
    hard_negative_counts,
    macro_f1,
    per_theme,
    precision,
    rare_themes,
    ratio,
    recall,
    release_tally,
    theme_tallies,
    total,
    unit_tally,
)
from earnings_themes.evaluation.verdicts import families, family_verdict, trial_verdict
from earnings_themes.gold import Gold
from earnings_themes.split import Partition
from earnings_themes.support.metrics import precision_value, ranked_auc
from earnings_themes.support.records import JudgeTrial

NOT_ESTIMATED = "not estimated from a pilot sample (R12.2, D1)"


@dataclass(frozen=True)
class Accepted:
    """One accepted assignment: its theme, and its evidence spans in the event's
    document."""

    theme_id: str
    spans: tuple[Span, ...]


@dataclass(frozen=True)
class EventObservation:
    """One event: its signed gold, its document's units, the run's accepted
    assignments, whether its kept attempt is ``confirmed`` (R13.1), and two
    retention counts, each (kept, offered): quotes (R12.8 (i)) and support targets,
    accepted over assessed (R12.8 (ii))."""

    event_id: str
    gold: Gold
    index: UnitIndex
    accepted: tuple[Accepted, ...]
    release_confirmed: bool
    quotes: tuple[int, int]
    targets: tuple[int, int]


@dataclass(frozen=True)
class LabelledTarget:
    """One labelled support target: the user's claim and joint labels (FP21),
    whether the run accepted it, each scorer view's joint score, and its four judge
    trials."""

    target_id: str
    event_id: str
    claim_label: Literal[0, 1] | None
    joint_label: Literal[0, 1] | None
    accepted: bool
    scores: Mapping[str, float | None]
    trials: tuple[JudgeTrial, ...]


@dataclass(frozen=True)
class _Event:
    observation: EventObservation
    cells: EventCells
    tallies: dict[str, Tally]
    rolled: dict[str, Tally]
    units: Tally
    chars: tuple[int, int]
    evidence: tuple[int, int]
    release: Tally | None
    negatives: dict[str, tuple[int, int]]


def _accepted(index: UnitIndex, accepted: Iterable[Accepted]):
    spans: dict[str, tuple[Span, ...]] = {}
    for row in accepted:
        spans[row.theme_id] = tuple(sorted({*spans.get(row.theme_id, ()), *row.spans}))
    return spans, {theme: units_over(index, s) for theme, s in spans.items()}


def _event(observation: EventObservation, roots: Mapping[str, str]) -> _Event:
    spans, units = _accepted(observation.index, observation.accepted)
    predicted = set(spans)
    gold = observation.gold
    cells = event_cells(gold, observation.index, predicted)
    up = {roots.get(t, t) for t in predicted}
    rolled = event_cells(gold, observation.index, up, theme_map=roots)
    negatives = hard_negative_counts(gold, observation.index, units)
    return _Event(
        observation=observation,
        cells=cells,
        tallies=theme_tallies(cells, predicted),
        rolled=theme_tallies(rolled, up),
        units=unit_tally(cells, units),
        chars=char_counts(cells, spans),
        evidence=evidence_recall_counts(cells, units),
        release=release_tally(
            observation.release_confirmed, gold.release_identification.label
        ),
        negatives={kind.value: counts for kind, counts in negatives.items()},
    )


def _counts(**counts: int) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(counts.items()))


def _summed(pairs: Iterable[tuple[int, int]]) -> float | None:
    rows = list(pairs)
    return ratio(sum(a for a, _ in rows), sum(b for _, b in rows))


def _tally_counts(tally: Tally, **more: int) -> tuple[tuple[str, int], ...]:
    return _counts(tp=tally.tp, fp=tally.fp, fn=tally.fn, **more)


class _Figures:
    def __init__(self, plan: BootstrapPlan) -> None:
        self.plan = plan
        self.out: list[Figure] = []

    def add[T](
        self,
        metric: Metric,
        per_event: Mapping[str, T],
        statistic: Callable[[Sequence[T]], float | None],
        counts: tuple[tuple[str, int], ...] = (),
        qualifier: str | None = None,
    ) -> None:
        result = estimate(per_event, statistic, self.plan)
        self.out.append(
            Figure(
                metric=metric,
                qualifier=qualifier,
                point=result.point,
                interval=result.interval,
                counts=counts,
            )
        )


def _event_figures(
    figures: _Figures, events: Mapping[str, _Event], themes: int
) -> None:
    def tallies(name: str) -> dict[str, Iterable[Tally]]:
        return {e: getattr(x, name).values() for e, x in events.items()}

    def merged(name: str) -> Tally:
        return total(t for x in events.values() for t in getattr(x, name).values())

    release = {e: x.release for e, x in events.items()}
    shown = total(t for t in release.values() if t is not None)
    ambiguous = sum(t is None for t in release.values())
    for metric, measure in (
        (Metric.RELEASE_PRECISION, precision),
        (Metric.RELEASE_RECALL, recall),
    ):
        figures.add(
            metric,
            release,
            lambda drawn, m=measure: m(total(t for t in drawn if t is not None)),
            _tally_counts(shown, ambiguous=ambiguous),
        )
    left = sum(len(x.cells.uncertain) for x in events.values())
    for micro, macro, name in (
        (Metric.THEME_F1_MICRO, Metric.THEME_F1_MACRO, "tallies"),
        (Metric.THEME_F1_ROLLUP_MICRO, Metric.THEME_F1_ROLLUP_MACRO, "rolled"),
    ):
        figures.add(
            micro,
            tallies(name),
            lambda drawn: f1(total(t for event in drawn for t in event)),
            _tally_counts(merged(name), uncertain_left_out=left),
        )
        scored = len(per_theme(getattr(x, name) for x in events.values()))
        figures.add(
            macro,
            {e: getattr(x, name) for e, x in events.items()},
            lambda drawn: macro_f1(per_theme(drawn)),
            _counts(themes_scored=scored, themes_left_out=themes - scored),
        )
    units = {e: x.units for e, x in events.items()}
    unit_total = total(units.values())
    for metric, measure in (
        (Metric.SPAN_UNIT_PRECISION, precision),
        (Metric.SPAN_UNIT_RECALL, recall),
        (Metric.SPAN_UNIT_F1, f1),
    ):
        figures.add(
            metric,
            units,
            lambda drawn, m=measure: m(total(drawn)),
            _tally_counts(unit_total),
        )
    chars = {e: x.chars for e, x in events.items()}
    figures.add(
        Metric.SPAN_CHAR_JACCARD,
        chars,
        _summed,
        _counts(
            shared=sum(a for a, _ in chars.values()),
            union=sum(b for _, b in chars.values()),
        ),
    )
    for metric, pick in (
        (Metric.RETENTION_QUOTES, lambda x: x.observation.quotes),
        (Metric.RETENTION_TARGETS, lambda x: x.observation.targets),
        (Metric.GOLD_EVIDENCE_RECALL, lambda x: x.evidence),
    ):
        pairs = {e: pick(x) for e, x in events.items()}
        figures.add(
            metric,
            pairs,
            _summed,
            _counts(
                kept=sum(a for a, _ in pairs.values()),
                offered=sum(b for _, b in pairs.values()),
            ),
        )
    kinds = sorted({k for x in events.values() for k in x.negatives})
    for kind in (None, *kinds):
        pairs = {
            e: tuple(
                (named, hit)
                for k, (named, hit) in x.negatives.items()
                if kind is None or k == kind
            )
            for e, x in events.items()
        }
        figures.add(
            Metric.HARD_NEGATIVE_FALSE_ACCEPTANCE,
            pairs,
            lambda drawn: ratio(
                sum(hit for event in drawn for _, hit in event),
                sum(named for event in drawn for named, _ in event),
            ),
            _counts(
                named=sum(n for rows in pairs.values() for n, _ in rows),
                accepted=sum(h for rows in pairs.values() for _, h in rows),
            ),
            qualifier=kind,
        )
    rare = rare_themes(x.cells for x in events.values())
    rare_tallies = {
        e: tuple(t for theme, t in x.tallies.items() if theme in rare)
        for e, x in events.items()
    }
    figures.add(
        Metric.RARE_THEME_RECALL,
        rare_tallies,
        lambda drawn: recall(total(t for event in drawn for t in event)),
        _counts(rare_themes=len(rare)),
    )
    counts = {e: x.observation.gold.counts for e, x in events.items()}
    for metric, key in (
        (Metric.GS5_EDITED_SHARE, "edited"),
        (Metric.GS5_REJECTED_SHARE, "rejected"),
        (Metric.GS5_ADDED_SHARE, "added"),
    ):
        figures.add(metric, counts, lambda drawn, k=key: gs5_shares(drawn)[k])
    no_theme = {e: x.observation.gold.no_theme for e, x in events.items()}
    figures.add(
        Metric.NO_THEME_SHARE,
        no_theme,
        lambda drawn: ratio(sum(drawn), len(drawn)),
        _counts(no_theme=sum(no_theme.values()), bundles=len(no_theme)),
    )


def _label_figures(
    figures: _Figures, labelled: Sequence[LabelledTarget], events: Iterable[str]
) -> None:
    by_event: dict[str, tuple[LabelledTarget, ...]] = {
        e: tuple(t for t in labelled if t.event_id == e) for e in events
    }
    by_event = {e: ts for e, ts in by_event.items() if ts}

    def joint_accepted(drawn) -> float | None:
        return precision_value(
            [
                t.joint_label
                for ts in drawn
                for t in ts
                if t.accepted and t.joint_label is not None
            ]
        )

    figures.add(
        Metric.SUPPORT_PRECISION,
        by_event,
        joint_accepted,
        _counts(
            labelled=sum(t.joint_label is not None for t in labelled),
            accepted=sum(t.accepted for t in labelled),
            accepted_unlabelled=sum(
                t.accepted and t.joint_label is None for t in labelled
            ),
        ),
    )
    for view in sorted({v for t in labelled for v in t.scores}):

        def auc(drawn, v=view) -> float | None:
            rows = [
                (t.claim_label, t.scores.get(v))
                for ts in drawn
                for t in ts
                if t.claim_label is not None and t.scores.get(v) is not None
            ]
            return ranked_auc(
                [s for label, s in rows if label == 1],
                [s for label, s in rows if label == 0],
            )

        scored = [
            t
            for t in labelled
            if t.claim_label is not None and t.scores.get(view) is not None
        ]
        figures.add(
            Metric.SCORER_AUC,
            by_event,
            auc,
            _counts(
                positive=sum(t.claim_label == 1 for t in scored),
                negative=sum(t.claim_label == 0 for t in scored),
            ),
            qualifier=view,
        )
    trials = [trial for t in labelled for trial in t.trials]
    for family in families(trials):
        _agreement(
            figures,
            by_event,
            family,
            lambda t, f=family: (family_verdict(t.trials, f), False),
        )
        for presentation in sorted({x.presentation.value for x in trials}):

            def verdict(t: LabelledTarget, f=family, p=presentation):
                trial = next(
                    (
                        x
                        for x in t.trials
                        if x.identity.family == f and x.presentation.value == p
                    ),
                    None,
                )
                return (0, True) if trial is None else trial_verdict(trial)

            _agreement(figures, by_event, f"{family}:{presentation}", verdict)


def _agreement(
    figures: _Figures,
    by_event: Mapping[str, tuple[LabelledTarget, ...]],
    qualifier: str,
    verdict: Callable[[LabelledTarget], tuple[int, bool]],
) -> None:
    pairs = {
        e: tuple(
            (verdict(t)[0], t.joint_label) for t in ts if t.joint_label is not None
        )
        for e, ts in by_event.items()
    }
    unsure = sum(
        verdict(t)[1]
        for ts in by_event.values()
        for t in ts
        if t.joint_label is not None
    )
    counts = _counts(labels=sum(len(p) for p in pairs.values()), uncertain=unsure)
    for metric, measure in (
        (Metric.JUDGE_KAPPA, cohen_kappa),
        (Metric.JUDGE_AC1, gwet_ac1),
    ):
        figures.add(
            metric,
            pairs,
            lambda drawn, m=measure: m([p for event in drawn for p in event]),
            counts,
            qualifier=qualifier,
        )


def partition_report(
    observations: Sequence[EventObservation],
    labelled: Sequence[LabelledTarget],
    codebook: Codebook,
    plan: BootstrapPlan,
    *,
    partition: Partition,
) -> PartitionReport:
    """Every §Metrics figure for one partition's events and labels."""
    if partition not in (Partition.TRAIN, Partition.DEV):
        raise EvaluationError(EvaluationProblem.WRONG_PARTITION, partition.value)
    ids = [o.event_id for o in observations]
    if len(ids) != len(set(ids)):
        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "events")
    for observation in observations:
        if observation.gold.partition is not partition or (
            observation.gold.event_id != observation.event_id
        ):
            raise EvaluationError(
                EvaluationProblem.WRONG_PARTITION, observation.event_id
            )
    for target in labelled:
        if target.event_id not in ids:
            raise EvaluationError(EvaluationProblem.UNKNOWN_EVENT, target.target_id)
    if len({t.target_id for t in labelled}) != len(labelled):
        raise EvaluationError(EvaluationProblem.DUPLICATE_TARGET, "labels")
    roots = level_one(codebook)
    events = {o.event_id: _event(o, roots) for o in observations}
    figures = _Figures(plan)
    _event_figures(figures, events, len(codebook.themes))
    _label_figures(figures, labelled, sorted(ids))
    for metric in (Metric.SECTOR_PREVALENCE, Metric.SOURCE_SELECTION_BIAS):
        figures.out.append(
            Figure(metric=metric, point=None, interval=None, reason=NOT_ESTIMATED)
        )
    return PartitionReport(
        partition=partition,
        in_sample=partition is Partition.TRAIN,
        events=tuple(sorted(ids)),
        figures=tuple(figures.out),
    )


def compare_readings(
    reference: GoldReading, other: GoldReading, index: UnitIndex
) -> ReadingAgreement:
    """``other`` scored against ``reference``, as a run is against gold: its present
    themes as predictions, and their units as evidence (GS19, A6(3))."""
    theirs = event_cells(other, index)
    mine = event_cells(reference, index, theirs.present)
    return ReadingAgreement(
        release_agrees=reference.release_identification.label
        == other.release_identification.label,
        theme_f1=f1(total(theme_tallies(mine, theirs.present).values())),
        unit_f1=f1(unit_tally(mine, theirs.units)),
        dangling=mine.dangling + theirs.dangling,
    )


def stability_figures(
    runs: Sequence[Sequence[EventObservation]],
    codebook: Codebook,
    plan: BootstrapPlan,
) -> tuple[Figure, ...]:
    """FP12's k fresh runs over one partition's events (R12.10): Fleiss' κ over
    event × theme presence, for every codebook theme, and the mean pairwise Jaccard
    of the runs' accepted evidence units and of their accepted (theme, unit)
    pairs."""
    if len(runs) < 2:
        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "runs")
    events = sorted(o.event_id for o in runs[0])
    if any(sorted(o.event_id for o in run) != events for run in runs):
        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "runs")
    themes = sorted(t.theme_id for t in codebook.themes)
    per_event: dict[str, tuple[tuple[frozenset, frozenset, frozenset], ...]] = {}
    for event_id in events:
        rows = []
        for run in runs:
            o = next(x for x in run if x.event_id == event_id)
            _, units = _accepted(o.index, o.accepted)
            pairs = frozenset((t, u) for t, us in units.items() for u in us)
            rows.append((frozenset(units), frozenset(u for _, u in pairs), pairs))
        per_event[event_id] = tuple(rows)

    def kappa(drawn) -> float | None:
        return fleiss_kappa(
            [
                [int(theme in run[0]) for run in event]
                for event in drawn
                for theme in themes
            ]
        )

    def jaccard(position: int):
        def mean(drawn) -> float | None:
            values = []
            for a, b in combinations(range(len(runs)), 2):
                left = {(i, x) for i, e in enumerate(drawn) for x in e[a][position]}
                right = {(i, x) for i, e in enumerate(drawn) for x in e[b][position]}
                union = left | right
                if union:
                    values.append(len(left & right) / len(union))
            return sum(values) / len(values) if values else None

        return mean

    figures = _Figures(plan)
    count = _counts(runs=len(runs), events=len(events), themes=len(themes))
    figures.add(Metric.STABILITY_FLEISS_KAPPA, per_event, kappa, count)
    figures.add(Metric.STABILITY_UNIT_JACCARD, per_event, jaccard(1), count)
    figures.add(Metric.STABILITY_ASSIGNMENT_JACCARD, per_event, jaccard(2), count)
    return tuple(figures.out)
