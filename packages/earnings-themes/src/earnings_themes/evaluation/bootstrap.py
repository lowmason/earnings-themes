"""The event-clustered percentile bootstrap (the Stage 11 spec, A3; R12.7; FP9).

- **Events are the unit.** A resample draws as many events as the partition holds,
  with replacement, from its events in sorted order, by ``random.Random(seed)``'s
  ``randrange``. The statistic sees the drawn events' observations in draw order.
- **Undefined resamples.** A resample whose statistic is ``None`` is skipped and
  counted. When more than ``max_undefined_share`` of the resamples are undefined, or
  none is defined, the interval is undefined (FP9: preregistered).
- **The interval** is the two percentiles at ``(1 - level) / 2`` and its complement,
  each by linear interpolation between order statistics.

The same seed, resample count and observations give the same interval, so a pilot
figure reproduces (R14.6).
"""

import math
import random
from collections.abc import Callable, Mapping, Sequence

from pydantic import Field, NonNegativeInt, PositiveInt

from earnings_themes.records import Part


class BootstrapPlan(Part):
    """How every interval is drawn; preregistered (FP9)."""

    seed: int
    resamples: PositiveInt
    level: float = Field(gt=0, lt=1)
    max_undefined_share: float = Field(ge=0, lt=1)


class Interval(Part):
    """A percentile interval, or ``None`` bounds with the reason in its counts."""

    lower: float | None
    upper: float | None
    level: float
    resamples: PositiveInt
    undefined: NonNegativeInt


class Estimate(Part):
    """A point estimate over every event, and its interval."""

    point: float | None
    interval: Interval


def _quantile(ordered: Sequence[float], share: float) -> float:
    position = share * (len(ordered) - 1)
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def estimate[T](
    per_event: Mapping[str, T],
    statistic: Callable[[Sequence[T]], float | None],
    plan: BootstrapPlan,
) -> Estimate:
    """``statistic`` over every event once, and its event-clustered interval."""
    events = sorted(per_event)
    point = statistic([per_event[e] for e in events]) if events else None
    rng = random.Random(plan.seed)
    values: list[float] = []
    for _ in range(plan.resamples if events else 0):
        drawn = [per_event[events[rng.randrange(len(events))]] for _ in events]
        value = statistic(drawn)
        if value is not None:
            values.append(value)
    undefined = plan.resamples - len(values)
    if not values or undefined / plan.resamples > plan.max_undefined_share:
        lower = upper = None
    else:
        values.sort()
        tail = (1 - plan.level) / 2
        lower, upper = _quantile(values, tail), _quantile(values, 1 - tail)
    return Estimate(
        point=point,
        interval=Interval(
            lower=lower,
            upper=upper,
            level=plan.level,
            resamples=plan.resamples,
            undefined=undefined,
        ),
    )
