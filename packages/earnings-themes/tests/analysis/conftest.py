"""Audited invented analytical fixtures; no protected documents or examples."""

import pytest

from .cases import make_counting_case, make_families, make_inputs, make_policy


@pytest.fixture
def analysis_inputs(codebook, template, tmp_path, no_network):
    result = make_inputs(codebook, template, tmp_path / "accepted")
    yield result
    assert no_network == []


@pytest.fixture
def review_analysis_inputs(codebook, template, tmp_path, no_network):
    result = make_inputs(codebook, template, tmp_path / "review", review=True)
    yield result
    assert no_network == []


@pytest.fixture
def analysis_policy():
    return make_policy()


@pytest.fixture
def family_map(analysis_inputs):
    return make_families(analysis_inputs.sources.codebook)


@pytest.fixture
def counting_case(analysis_inputs):
    return make_counting_case(
        analysis_inputs.sources.codebook, analysis_inputs.assignment_policy.reference
    )
