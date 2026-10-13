"""The event-clustered bootstrap: deterministic under its seed, events drawn whole,
and undefined resamples counted (the Stage 11 spec, A3; R12.7)."""

import math
import random

import pytest
from earnings_themes.evaluation.bootstrap import BootstrapPlan, Interval, estimate
from pydantic import ValidationError

PLAN = BootstrapPlan(seed=7, resamples=200, level=0.9, max_undefined_share=0.1)


def mean(values) -> float | None:
    return sum(values) / len(values) if values else None


def test_the_point_is_the_statistic_over_every_event_once() -> None:
    result = estimate({"b": 3.0, "a": 1.0}, mean, PLAN)
    assert result.point == 2.0


def test_resamples_draw_whole_events_by_the_seeded_order() -> None:
    per_event = {"e2": 0.0, "e1": 1.0, "e3": 1.0}
    rng = random.Random(7)
    events = ["e1", "e2", "e3"]
    expected = sorted(
        mean([per_event[events[rng.randrange(3)]] for _ in events]) for _ in range(200)
    )
    position = 0.05 * 199
    lower = expected[9] + (expected[10] - expected[9]) * (position - 9)
    result = estimate(per_event, mean, PLAN)
    assert result.interval.lower == pytest.approx(lower)
    assert estimate(per_event, mean, PLAN) == result


def test_another_seed_draws_other_resamples() -> None:
    per_event = {f"e{i}": float(i) for i in range(10)}
    first = estimate(per_event, mean, PLAN)
    other = estimate(per_event, mean, PLAN.model_copy(update={"seed": 8}))
    assert first.point == other.point
    assert first.interval != other.interval


def test_a_constant_statistic_has_a_degenerate_interval() -> None:
    result = estimate({"a": 0.5, "b": 0.5}, mean, PLAN)
    assert (result.interval.lower, result.interval.upper) == (0.5, 0.5)
    assert result.interval.undefined == 0


def test_undefined_resamples_are_skipped_and_counted() -> None:
    per_event = {f"e{i}": i == 0 for i in range(10)}

    def needs_e0(drawn) -> float | None:
        return 1.0 if any(drawn) else None

    result = estimate(per_event, needs_e0, PLAN)
    rng = random.Random(7)
    draws = [
        [per_event[f"e{rng.randrange(10)}"] for _ in range(10)] for _ in range(200)
    ]
    expected = sum(not any(drawn) for drawn in draws)
    assert result.interval.undefined == expected
    assert expected > 20
    assert result.interval.lower is None and result.interval.upper is None
    loose = PLAN.model_copy(update={"max_undefined_share": 0.9})
    assert estimate(per_event, needs_e0, loose).interval.lower == 1.0


def test_no_events_is_undefined() -> None:
    result = estimate({}, mean, PLAN)
    assert result.point is None
    assert result.interval.lower is None
    assert result.interval.undefined == PLAN.resamples


@pytest.mark.parametrize("field", ["lower", "upper", "level"])
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_an_interval_holds_finite_numbers(field, value) -> None:
    bounds = {"lower": 0.1, "upper": 0.2, "level": 0.9}
    with pytest.raises(ValidationError, match=field):
        Interval(**{**bounds, field: value}, resamples=10, undefined=0)
    assert Interval(**bounds, resamples=10, undefined=0).lower == 0.1
    assert Interval(lower=None, upper=None, level=0.9, resamples=10, undefined=10)


def test_upper_bound_interpolates_the_upper_percentile() -> None:
    """Seed 8 over 0.0..9.0 has sorted resampled means x[189] = 6.1 and
    x[190] = 6.2, so the 0.95 position 189.05 interpolates to 6.105. Kills an upper
    bound taken at the wrong tail, and floor (6.1) or ceil (6.2) in place of
    interpolation. (The oracle is recomputed from ``random.Random(8)`` alone.)"""
    per_event = {f"e{i}": float(i) for i in range(10)}
    result = estimate(per_event, mean, PLAN.model_copy(update={"seed": 8}))
    assert result.interval.upper == pytest.approx(6.105)


def undefined_for_the_first(count: int):
    """A statistic defined for the point, then undefined for exactly ``count``
    resamples, then defined again: the point is call one, resamples follow."""
    calls = 0

    def statistic(drawn) -> float | None:
        nonlocal calls
        calls += 1
        return None if 1 < calls <= count + 1 else 1.0

    return statistic


def share_plan(share: float) -> BootstrapPlan:
    return PLAN.model_copy(update={"resamples": 100, "max_undefined_share": share})


@pytest.mark.parametrize("share, limit", [(0.5, 50), (0.57, 57)])
def test_an_undefined_count_at_the_limit_keeps_the_interval(share, limit) -> None:
    """Exactly ``share * resamples`` undefined is not "more than" the share. Kills
    ``>=`` for ``>``, and, at 0.57 (0.57 * 100 is 56.99999999999999), a comparison
    made in floating point on the product."""
    result = estimate(
        {"a": 1.0, "b": 2.0}, undefined_for_the_first(limit), share_plan(share)
    )
    assert result.interval.undefined == limit
    assert result.interval.lower == 1.0 and result.interval.upper == 1.0


@pytest.mark.parametrize("share, limit", [(0.5, 50), (0.57, 57)])
def test_one_more_undefined_resample_than_the_limit_drops_the_interval(
    share, limit
) -> None:
    result = estimate(
        {"a": 1.0, "b": 2.0}, undefined_for_the_first(limit + 1), share_plan(share)
    )
    assert result.interval.undefined == limit + 1
    assert result.interval.lower is None and result.interval.upper is None
