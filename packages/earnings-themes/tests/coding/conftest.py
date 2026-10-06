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


@pytest.fixture
def assignment_case_factory(
    coding_case, coding_policy, classifier_identity, template, tmp_path
):
    counter = 0

    def make(
        *,
        themes=("capacity",),
        claims=("An invented operating claim.",),
        documents=1,
        book=None,
        attributes=None,
        bundle=None,
    ):
        nonlocal counter
        counter += 1
        root = tmp_path / f"assignments-{counter}"
        sources = make_sources(
            book or coding_case.codebook,
            bundle or invented_bundle("invented-first"),
            template,
            other_bundles=tuple(
                invented_bundle(f"invented-{i}") for i in range(1, documents)
            ),
            claim_texts=claims,
        )
        job = make_proposal_job(sources, coding_policy, classifier_identity, root)
        replies = [
            {
                "theme_ids": themes,
                "attributes": (attributes or [{}])[i % len(attributes or [{}])],
            }
            for i in range(len(sources.stored_run.claims))
        ]
        proposals, _ = job.run(replies)
        return make_assessed_case(proposals, sources, root)

    return make


@pytest.fixture
def multilabel_decisions(assignment_case_factory):
    case = assignment_case_factory(themes=("capacity", "demand"))
    return case.decide(FixturePolicy(case.proposals, case.support)), case.support


@pytest.fixture
def two_claim_decisions(assignment_case_factory):
    case = assignment_case_factory(
        claims=("An invented equipment claim.", "A second invented equipment claim.")
    )
    return case.decide(FixturePolicy(case.proposals, case.support)), case.support


@pytest.fixture
def two_document_decisions(assignment_case_factory):
    case = assignment_case_factory(documents=2)
    return case.decide(FixturePolicy(case.proposals, case.support)), case.support
