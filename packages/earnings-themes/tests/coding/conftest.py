"""Invented approved coding fixtures; source examples are never resolved."""

import pytest
from earnings_themes.coding.input import resolve_coding_input

from .cases import invented_bundle, invented_codebook, make_sources


@pytest.fixture
def coding_case(codebook, template, no_network):
    yield make_sources(invented_codebook(codebook), invented_bundle(), template)
    assert no_network == []


@pytest.fixture
def coding_input(coding_case):
    claim = coding_case.stored_run.claims[0]
    return resolve_coding_input(coding_case, claim.doc_id, claim.claim_id)
