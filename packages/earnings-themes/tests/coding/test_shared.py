"""Shared configuration and source-binding gates over invented records only."""

from dataclasses import replace

import pytest
from earnings_core import digest
from earnings_themes.coding import (
    coding_configuration,
    source_bindings,
    validate_proposal_support,
)
from earnings_themes.coding.records import CodingError


def test_coding_configuration_reproduces_existing_manifest(assessed_case):
    record = assessed_case.proposals.record
    keys = (
        "source_run_id",
        "source_run_hash",
        "documents",
        "codebook",
        "classifier_identity",
        "coding_policy",
        "ceilings",
        "requested_claim_order",
        "schema_hash",
        "coding_version",
        "validator_version",
        "cache_mode",
    )
    material = coding_configuration(**{key: getattr(record, key) for key in keys})
    assert set(material) == set(keys)
    assert digest(material) == record.configuration_hash
    bindings = source_bindings(assessed_case.sources)
    assert set(bindings) == {
        "source_run_id",
        "source_run_hash",
        "documents",
        "codebook",
    }
    assert bindings == {key: getattr(record, key) for key in bindings}
    validate_proposal_support(
        assessed_case.proposals, assessed_case.support, assessed_case.sources
    )


def test_source_run_id_is_bound_even_when_manifest_hash_is_unchanged(assessed_case):
    support = assessed_case.support
    altered = replace(
        support, record=support.record.model_copy(update={"source_run_id": "other"})
    )
    with pytest.raises(CodingError, match="^(input_changed|storage_corrupt)$"):
        validate_proposal_support(
            assessed_case.proposals, altered, assessed_case.sources
        )


def test_shared_gate_uses_support_outcome_uniqueness_check(assessed_case):
    support = assessed_case.support
    altered = replace(support, outcomes=(*support.outcomes, support.outcomes[0]))
    with pytest.raises(CodingError):
        validate_proposal_support(
            assessed_case.proposals, altered, assessed_case.sources
        )


def test_shared_gate_requires_current_proposal_configuration(assessed_case):
    proposals = assessed_case.proposals
    altered = replace(
        proposals,
        record=proposals.record.model_copy(update={"configuration_hash": "f" * 64}),
    )
    with pytest.raises(CodingError, match="^input_changed$"):
        validate_proposal_support(altered, assessed_case.support, assessed_case.sources)


def test_shared_gate_uses_support_outcome_order_check(assignment_case_factory):
    case = assignment_case_factory(themes=("capacity", "demand"))
    assert len(case.support.outcomes) == 2
    altered = replace(case.support, outcomes=tuple(reversed(case.support.outcomes)))
    with pytest.raises(CodingError):
        validate_proposal_support(case.proposals, altered, case.sources)
