"""κ, AC1 and Fleiss' κ, with hand-computed known answers (the Stage 11 spec, A3)."""

import pytest
from earnings_themes.evaluation.agreement import cohen_kappa, fleiss_kappa, gwet_ac1
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem

PAIRS = [(1, 1)] * 20 + [(1, 0)] * 5 + [(0, 1)] * 10 + [(0, 0)] * 15
"""Observed 0.7; the first rater says 1 for 0.5, the second for 0.6."""


def test_cohen_kappa_known_answer() -> None:
    assert cohen_kappa(PAIRS) == pytest.approx(0.4)


def test_gwet_ac1_known_answer() -> None:
    assert gwet_ac1(PAIRS) == pytest.approx(0.205 / 0.505)


def test_fleiss_kappa_known_answer() -> None:
    ratings = [[1, 1, 1], [1, 1, 0], [0, 0, 0], [1, 0, 0]]
    assert fleiss_kappa(ratings) == pytest.approx(1 / 3)


def test_undefined_agreement_is_none() -> None:
    assert cohen_kappa([]) is None
    assert gwet_ac1([]) is None
    assert fleiss_kappa([]) is None
    assert cohen_kappa([(1, 1), (1, 1)]) is None
    assert fleiss_kappa([[0, 0], [0, 0]]) is None
    assert gwet_ac1([(1, 1), (1, 1)]) == pytest.approx(1.0)


def test_malformed_ratings_are_refused() -> None:
    with pytest.raises(EvaluationError, match="malformed_record"):
        cohen_kappa([(2, 1)])
    with pytest.raises(EvaluationError, match="malformed_record"):
        fleiss_kappa([[1], [0]])
    with pytest.raises(EvaluationError, match="malformed_record"):
        fleiss_kappa([[1, 0], [0, 1, 1]])


@pytest.mark.parametrize("pair", [(2, 1), (1, -1), (1,), (1, 0, 1), ()])
@pytest.mark.parametrize("statistic", [cohen_kappa, gwet_ac1], ids=lambda f: f.__name__)
def test_a_malformed_pair_is_refused_by_its_field_path(statistic, pair) -> None:
    with pytest.raises(EvaluationError) as refusal:
        statistic([(1, 1), (0, 0), pair])
    assert refusal.value.problem is EvaluationProblem.MALFORMED_RECORD
    assert refusal.value.subject == "pairs[2]"
    assert str(refusal.value) == "pairs[2]: malformed_record"


def test_the_first_malformed_pair_is_the_one_named() -> None:
    with pytest.raises(EvaluationError) as refusal:
        cohen_kappa([(1, 1), (3, 0), (1,)])
    assert refusal.value.subject == "pairs[1]"


def test_fewer_than_two_raters_names_the_first_row() -> None:
    with pytest.raises(EvaluationError) as refusal:
        fleiss_kappa([[1], [0]])
    assert refusal.value.problem is EvaluationProblem.MALFORMED_RECORD
    assert refusal.value.subject == "ratings[0]"
    assert str(refusal.value) == "ratings[0]: malformed_record"


def test_a_row_of_another_length_names_that_row() -> None:
    with pytest.raises(EvaluationError) as refusal:
        fleiss_kappa([[1, 0], [0, 1], [0, 1, 1], [1, 1, 1, 1]])
    assert refusal.value.problem is EvaluationProblem.MALFORMED_RECORD
    assert refusal.value.subject == "ratings[2]"
    assert str(refusal.value) == "ratings[2]: malformed_record"
