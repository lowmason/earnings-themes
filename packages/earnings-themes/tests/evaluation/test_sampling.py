"""The label sampler: IDs only, seeded-hash order, round-robin, capped, and
extensible (the Stage 11 spec, A4; FP8)."""

import inspect
from collections import Counter
from dataclasses import fields

import pytest
from earnings_themes.evaluation.problems import (
    EvaluationError,
    EvaluationProblem,
    first_duplicate,
)
from earnings_themes.evaluation.sampling import PoolTarget, sample_targets

POOL = tuple(
    PoolTarget(f"{event}-{theme}-{n}", event, theme)
    for event in ("e1", "e2", "e3")
    for theme in ("capacity", "demand")
    for n in range(3)
)


def test_the_sampler_sees_only_ids() -> None:
    assert list(inspect.signature(sample_targets).parameters) == [
        "pool",
        "seed",
        "size",
        "cap",
    ]
    assert [f.name for f in fields(PoolTarget)] == ["target_id", "event_id", "theme_id"]


def test_the_known_sample() -> None:
    """Pins the digest ranks and the round-robin (R14.6)."""
    assert sample_targets(POOL, seed=19, size=7, cap=3) == (
        "e1-demand-1",
        "e2-capacity-1",
        "e3-demand-0",
        "e1-capacity-2",
        "e2-demand-1",
        "e3-capacity-0",
        "e1-demand-2",
    )


def test_rounds_take_one_target_per_event_and_alternate_themes() -> None:
    drawn = sample_targets(POOL, seed=19, size=9, cap=3)
    events = [t.split("-")[0] for t in drawn]
    assert sorted(events[:3]) == ["e1", "e2", "e3"]
    assert Counter(events) == {"e1": 3, "e2": 3, "e3": 3}
    for event in ("e1", "e2", "e3"):
        themes = [t.split("-")[1] for t in drawn if t.startswith(event)]
        assert themes[0] != themes[1]


def test_the_cap_and_the_size_bound_the_sample() -> None:
    assert len(sample_targets(POOL, seed=19, size=100, cap=2)) == 6
    assert len(sample_targets(POOL, seed=19, size=4, cap=3)) == 4
    assert sample_targets((), seed=19, size=4, cap=3) == ()


def test_a_larger_size_extends_the_same_sample() -> None:
    small = sample_targets(POOL, seed=19, size=5, cap=3)
    large = sample_targets(POOL, seed=19, size=8, cap=3)
    assert large[:5] == small


def test_the_seed_decides_the_order_and_nothing_else_does() -> None:
    assert sample_targets(POOL, seed=19, size=9, cap=3) == sample_targets(
        tuple(reversed(POOL)), seed=19, size=9, cap=3
    )
    assert sample_targets(POOL, seed=19, size=9, cap=3) != sample_targets(
        POOL, seed=20, size=9, cap=3
    )


def test_a_repeated_target_is_refused_by_its_id() -> None:
    with pytest.raises(EvaluationError) as refused:
        sample_targets((*POOL, POOL[4]), seed=19, size=3, cap=3)
    assert refused.value.problem is EvaluationProblem.DUPLICATE_TARGET
    assert refused.value.subject == "e1-demand-1"


def test_first_duplicate_names_the_first_repeated_id() -> None:
    assert first_duplicate(["a", "b", "c", "b", "a"]) == "b"
    assert first_duplicate(["a", "b"]) is None
    assert first_duplicate([]) is None
