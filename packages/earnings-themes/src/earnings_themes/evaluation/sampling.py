"""The label sample (the Stage 11 spec, A4 and §Preregistration; FP8).

- **The pool** is the partition's ``assessed`` and ``flagged`` targets; ``refused``
  and ``incomplete`` targets are left out (``label_pool``).
- **The sampler** sees only target, event and theme IDs, so it cannot sample by a
  score, a judge answer or an outcome.
- **Seeded-hash order.** Events, an event's themes, and a theme's targets are each
  ordered by the digest of the seed and their IDs. Within an event the sampler
  round-robins across its themes; across events it takes one target per event per
  round, at most ``cap`` from any event, until it holds ``size`` or every event is
  at its cap or exhausted.
- **Extension.** With the cap fixed, a larger size draws a sample that begins with
  the smaller one, so a preregistered extension adds to the labels already written
  (§Failure handling).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from earnings_core import digest

from earnings_themes.evaluation.problems import (
    EvaluationError,
    EvaluationProblem,
    first_duplicate,
)
from earnings_themes.support.records import ReviewOutcome, ReviewStatus, TargetRecord

POOL = (ReviewStatus.ASSESSED, ReviewStatus.FLAGGED)


@dataclass(frozen=True)
class PoolTarget:
    """A target the sampler may draw: its ID, its event, and its proposed theme."""

    target_id: str
    event_id: str
    theme_id: str


def label_pool(
    targets: Sequence[TargetRecord],
    outcomes: Sequence[ReviewOutcome],
    events_by_doc: Mapping[str, str],
) -> tuple[PoolTarget, ...]:
    """The ``assessed`` and ``flagged`` targets, each with its event (FP8)."""
    status = {outcome.target_id: outcome.status for outcome in outcomes}
    pool = []
    for record in targets:
        if status.get(record.target_id) not in POOL:
            continue
        event_id = events_by_doc.get(record.target.doc_id)
        if event_id is None:
            raise EvaluationError(EvaluationProblem.UNKNOWN_EVENT, record.target_id)
        pool.append(PoolTarget(record.target_id, event_id, record.target.theme_id))
    return tuple(pool)


def _rank(seed: int, *ids: str) -> str:
    return digest({"seed": seed, "ids": list(ids)})


def sample_targets(
    pool: Sequence[PoolTarget], *, seed: int, size: int, cap: int
) -> tuple[str, ...]:
    """The sampled target IDs, in draw order."""
    if (duplicate := first_duplicate(t.target_id for t in pool)) is not None:
        raise EvaluationError(EvaluationProblem.DUPLICATE_TARGET, duplicate)
    themes: dict[str, dict[str, list[str]]] = {}
    for target in pool:
        by_theme = themes.setdefault(target.event_id, {})
        by_theme.setdefault(target.theme_id, []).append(target.target_id)
    queues: dict[str, list[str]] = {}
    for event_id, by_theme in themes.items():
        lanes = [
            sorted(ids, key=lambda i, t=theme: _rank(seed, event_id, t, i))
            for theme, ids in sorted(
                by_theme.items(), key=lambda kv: _rank(seed, event_id, kv[0])
            )
        ]
        depth = max(len(lane) for lane in lanes)
        queue = [lane[r] for r in range(depth) for lane in lanes if r < len(lane)]
        queues[event_id] = queue[:cap]
    events = sorted(queues, key=lambda e: _rank(seed, e))
    drawn = [queues[e][r] for r in range(cap) for e in events if r < len(queues[e])]
    return tuple(drawn[:size])
