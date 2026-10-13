"""Agreement between raters (the Stage 11 spec, A3 and §Preregistration; R8.4,
R12.10; RC §7).

- **Cohen's κ** and **Gwet's AC1** compare two raters' binary answers over the same
  items: a judge family's verdict and the user's label (FP9, FP21).
- **Fleiss' κ** compares any fixed number of raters, at least two, over the same
  items: k fresh runs' event × theme presence (FP12).

An empty population, or one whose chance agreement is total, is ``None``, never a
number (A §Non-negotiables).

``judge_agreement`` is the one estimate of a judge's agreement with the joint
label, for the report's figures and calibration's floor test alike (R8.4, D19-15).
"""

from collections.abc import Iterable, Sequence

from earnings_themes.evaluation.bootstrap import BootstrapPlan, Estimate, estimate
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem


def _shares(pairs: Sequence[tuple[int, int]]) -> tuple[float, float, float] | None:
    """Observed agreement, and each rater's share of 1s; ``None`` with no items."""
    if not pairs:
        return None
    for index, pair in enumerate(pairs):
        if len(pair) != 2 or any(answer not in (0, 1) for answer in pair):
            raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, f"pairs[{index}]")
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    return observed, sum(a for a, _ in pairs) / n, sum(b for _, b in pairs) / n


def cohen_kappa(pairs: Sequence[tuple[int, int]]) -> float | None:
    """Cohen's κ for two raters' binary answers."""
    shares = _shares(pairs)
    if shares is None:
        return None
    observed, first, second = shares
    chance = first * second + (1 - first) * (1 - second)
    return None if chance == 1 else (observed - chance) / (1 - chance)


def gwet_ac1(pairs: Sequence[tuple[int, int]]) -> float | None:
    """Gwet's AC1 for two raters' binary answers; its chance agreement is at most
    one half, so it is defined whenever there is an item."""
    shares = _shares(pairs)
    if shares is None:
        return None
    observed, first, second = shares
    mean = (first + second) / 2
    chance = 2 * mean * (1 - mean)
    return (observed - chance) / (1 - chance)


def judge_agreement(
    targets: Iterable[tuple[str, int | None, int, bool]],
    plan: BootstrapPlan,
) -> tuple[Estimate, Estimate, int, int]:
    """A judge's Cohen's κ and Gwet's AC1 against the joint label, each with its
    event-clustered interval, and the labels and uncertain verdicts behind them.

    Each target is its event, its joint label, the judge's binary verdict, and
    whether that verdict is uncertain. A target without a joint label is left out,
    so the bootstrap resamples only the events holding one (D19-10), and only its
    labelled targets' uncertain verdicts are counted."""
    per_event: dict[str, list[tuple[int, int]]] = {}
    uncertain = 0
    for event_id, label, verdict, unsure in targets:
        if label is None:
            continue
        per_event.setdefault(event_id, []).append((verdict, label))
        uncertain += unsure
    pairs = {event_id: tuple(rows) for event_id, rows in per_event.items()}
    kappa, ac1 = (
        estimate(pairs, lambda drawn, m=measure: m([p for e in drawn for p in e]), plan)
        for measure in (cohen_kappa, gwet_ac1)
    )
    return kappa, ac1, sum(map(len, pairs.values())), uncertain


def fleiss_kappa(ratings: Sequence[Sequence[int]]) -> float | None:
    """Fleiss' κ: one row per item, holding each rater's category."""
    if not ratings:
        return None
    raters = len(ratings[0])
    if raters < 2:
        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "ratings[0]")
    for index, row in enumerate(ratings):
        if len(row) != raters:
            raise EvaluationError(
                EvaluationProblem.MALFORMED_RECORD, f"ratings[{index}]"
            )
    categories = sorted({c for row in ratings for c in row})
    counts = [[list(row).count(c) for c in categories] for row in ratings]
    items = len(counts)
    observed = (
        sum(
            (sum(n * n for n in row) - raters) / (raters * (raters - 1))
            for row in counts
        )
        / items
    )
    shares = [
        sum(row[j] for row in counts) / (items * raters) for j in range(len(categories))
    ]
    chance = sum(p * p for p in shares)
    return None if chance == 1 else (observed - chance) / (1 - chance)
