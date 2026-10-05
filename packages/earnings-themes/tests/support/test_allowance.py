"""Offline reservations, settlement and atomic ceiling checks."""

import pytest
from earnings_themes.extraction.adapters import Usage
from earnings_themes.support.allowance import Allowance, reserved_judge_tokens
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import SupportCeilings


def ceilings(**changes):
    values = {
        "scorer_per_target": 2,
        "scorer_per_document": 3,
        "scorer_per_run": 4,
        "judge_per_target": 5,
        "judge_per_document": 6,
        "judge_per_run": 7,
        "tokens_per_document": 100,
        "tokens_per_run": 150,
    }
    return SupportCeilings(**(values | changes))


@pytest.mark.parametrize(
    "field", ["scorer_per_target", "scorer_per_document", "scorer_per_run"]
)
def test_scorer_checks_every_limit_atomically(field):
    allowance = Allowance(ceilings(**{field: 1}))
    allowance.reserve_scorer("SECRET_ID", "SECRET_DOC")
    before = allowance.snapshot()
    with pytest.raises(SupportError, match="^scorer_exhausted$"):
        allowance.reserve_scorer("SECRET_ID", "SECRET_DOC")
    assert allowance.snapshot() == before
    assert "SECRET" not in repr(before) + str(allowance)


@pytest.mark.parametrize(
    "field", ["judge_per_target", "judge_per_document", "judge_per_run"]
)
def test_four_trials_and_retry_each_reserve(field):
    allowance = Allowance(ceilings(**{field: 5}))
    for _ in range(5):
        allowance.reserve_judge("t", "d", 1, 1)
    with pytest.raises(SupportError, match="^judge_exhausted$"):
        allowance.reserve_judge("t", "d", 1, 1)
    assert len(allowance.snapshot()) == 5


@pytest.mark.parametrize("field", ["tokens_per_document", "tokens_per_run"])
def test_tokens_full_reservation_and_atomic_exhaustion(field):
    allowance = Allowance(ceilings(**{field: 11}))
    allowance.reserve_judge("t", "d", 5, 6)
    before = allowance.snapshot()
    with pytest.raises(SupportError, match="^tokens_exhausted$"):
        allowance.reserve_judge("t", "d", 0, 1)
    assert allowance.snapshot() == before


def test_unknown_retains_reservation_known_releases_unused_and_overspend_blocks():
    allowance = Allowance(ceilings(tokens_per_run=15, tokens_per_document=15))
    first = allowance.reserve_judge("t", "d", 5, 5)
    allowance.settle(first, None)
    assert allowance.snapshot()[0].unreported
    second = allowance.reserve_judge("t", "d", 2, 3)
    allowance.settle(second, Usage(prompt_tokens=1, completion_tokens=1))
    third = allowance.reserve_judge("t", "d", 1, 2)
    allowance.settle(third, Usage(prompt_tokens=4, completion_tokens=4))
    with pytest.raises(SupportError, match="tokens_exhausted"):
        allowance.reserve_judge("t", "d", 0, 1)
    row = allowance.snapshot()[2]
    assert row.reserved_tokens == 3
    assert row.actual_prompt_tokens == row.actual_completion_tokens == 4


def test_settlement_is_once_only_and_invalid_usage_is_atomic():
    allowance = Allowance(ceilings())
    reservation = allowance.reserve_judge("t", "d", 3, 3)
    before = allowance.snapshot()
    with pytest.raises(SupportError, match="malformed_record"):
        allowance.settle(
            reservation, Usage.model_construct(prompt_tokens=True, completion_tokens=1)
        )
    assert allowance.snapshot() == before
    allowance.settle(reservation, None)
    with pytest.raises(SupportError, match="malformed_record"):
        allowance.settle(reservation, None)


@pytest.mark.parametrize("a,b", [(True, 1), (1, True), (-1, 1), (1, 0), (1.5, 1)])
def test_invalid_tokens_safe(a, b):
    with pytest.raises(SupportError, match="^malformed_record$"):
        reserved_judge_tokens(a, b)


@pytest.mark.parametrize("target", [None, {}, True, 1])
def test_invalid_id_refused_safely(target):
    allowance = Allowance(ceilings())
    with pytest.raises(SupportError, match="malformed_record"):
        allowance.reserve_scorer(target, "d")
    assert allowance.snapshot() == ()
