"""The event-clustered bootstrap: deterministic under its seed, events drawn whole,
and undefined resamples counted (the Stage 11 spec, A3; R12.7)."""

import random

import pytest
from earnings_themes.evaluation.bootstrap import BootstrapPlan, estimate

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
