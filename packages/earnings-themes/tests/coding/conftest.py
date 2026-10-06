"""Invented approved coding fixtures; source examples are never resolved."""

import pytest
from earnings_core import sha256_hex
from earnings_themes.coding.input import resolve_coding_input
from earnings_themes.coding.prompt import render_coding
from earnings_themes.coding.records import CodingPolicy
from earnings_themes.extraction.records import Parameters
from earnings_themes.support.records import JudgeIdentity, RuntimeIdentity

from .cases import (
    FixturePolicy,
    invented_bundle,
    invented_codebook,
    make_assessed_case,
    make_proposal_job,
    make_sources,
)


@pytest.fixture
def coding_case(codebook, template, no_network):
    yield make_sources(invented_codebook(codebook), invented_bundle(), template)
    assert no_network == []


@pytest.fixture
def coding_input(coding_case):
    claim = coding_case.stored_run.claims[0]
    return resolve_coding_input(coding_case, claim.doc_id, claim.claim_id)


@pytest.fixture
def classifier_identity():
    return JudgeIdentity(
        family="invented-classifier-family",
        runtime=RuntimeIdentity(
            model_id="invented-classifier",
            revision="fixture-1",
            files=(),
            runtime="scripted",
            runtime_version="1",
            device="cpu",
            precision="float32",
            encoding_version="fixture-1",
        ),
        input_limit=10000,
        output_limit=2048,
        hosting="scripted",
        weight_license=None,
    )


@pytest.fixture
def coding_policy():
    text = "Classify invented claims using only supplied frozen theme IDs."
    return CodingPolicy(
        prompt_text=text,
        prompt_hash=sha256_hex(text.encode("utf-8")),
        parameters=Parameters(max_tokens=64),
    )


@pytest.fixture
def coding_request(coding_input, coding_policy):
    return render_coding(coding_input, coding_policy)


@pytest.fixture
def proposal_job(coding_case, coding_policy, classifier_identity, tmp_path):
    return make_proposal_job(coding_case, coding_policy, classifier_identity, tmp_path)


@pytest.fixture
def assessed_case(proposal_job, tmp_path):
    proposals, _ = proposal_job.run([{"theme_ids": ["capacity"], "attributes": {}}])
    return make_assessed_case(proposals, proposal_job.sources, tmp_path)


@pytest.fixture
def contextual_case(assessed_case, tmp_path):
    return make_assessed_case(
        assessed_case.proposals,
        assessed_case.sources,
        tmp_path / "contextual",
        contribution="contextual",
    )


@pytest.fixture
def fixture_policy(assessed_case):
    return FixturePolicy(assessed_case.proposals, assessed_case.support)
