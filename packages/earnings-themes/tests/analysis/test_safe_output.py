"""Diagnostics expose fixed reasons or hashes, never invented source content."""

from earnings_themes.analysis.problems import AnalysisError


def test_models_hide_all_values(analysis_inputs, counting_case):
    for row in (
        *analysis_inputs.metadata,
        *counting_case.observations,
        *counting_case.coverage,
    ):
        printed = str(row) + repr(row)
        assert "https:" not in printed
        assert "Invented" not in printed
        assert "sha256=" in printed
    assert "data=" not in repr(analysis_inputs.raw_snapshots[0])
    assert "sources=" not in repr(analysis_inputs)
    assert "frames=" not in repr(counting_case.tables)


def test_error_is_closed():
    error = AnalysisError("Invented untrusted diagnostic")
    assert str(error) == "unexpected_error"
    assert "Invented" not in repr(error)


def test_projection_policy_exception_has_closed_diagnostic(analysis_inputs):
    import pytest
    from earnings_themes.analysis import build_observations, reverify_analysis_inputs

    bound = reverify_analysis_inputs(analysis_inputs)

    def fail(view):
        raise RuntimeError("Invented source-bearing policy diagnostic")

    bound.inputs.assignment_policy.evaluate = fail
    with pytest.raises(AnalysisError) as error:
        build_observations(bound)
    assert str(error.value) == "input_changed"
    assert "Invented" not in repr(error.value)
    assert error.value.__suppress_context__
