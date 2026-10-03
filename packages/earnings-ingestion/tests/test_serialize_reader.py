"""The canonical-fixture format reads back losslessly (plan 9): Stage 6 loads each
pilot document from ``data/runs/events/canonical/<doc_id>.json`` this way."""

import json
from pathlib import Path

import pytest
from earnings_ingestion.canonical.serialize import from_fixture_json, to_fixture_json

REPO = Path(__file__).resolve().parents[3]
FIXTURES = sorted((REPO / "tests" / "fixtures" / "canonical").glob("*.json"))


def test_the_eight_stage_1_fixtures_are_read() -> None:
    assert len(FIXTURES) == 8


@pytest.mark.parametrize("path", FIXTURES, ids=lambda path: path.stem)
def test_a_committed_fixture_reads_back_to_the_same_bytes(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    result = from_fixture_json(text)
    assert result.document.source_document_id == path.stem
    assert to_fixture_json(result) == text


def test_the_masks_keep_the_manifests_policy() -> None:
    result = from_fixture_json(FIXTURES[0].read_text(encoding="utf-8"))
    assert result.masked.policy_id == result.manifest.mask_policy_id
    assert result.masked.policy_version == result.manifest.mask_policy_version


def test_a_missing_part_is_refused() -> None:
    data = json.loads(FIXTURES[0].read_text(encoding="utf-8"))
    del data["masks"]
    with pytest.raises(ValueError, match="exactly document, elements, manifest"):
        from_fixture_json(json.dumps(data))


def test_an_element_of_another_document_is_refused() -> None:
    data = json.loads(FIXTURES[0].read_text(encoding="utf-8"))
    data["elements"][0]["doc_id"] = "other@walker-1#0000000000000000"
    with pytest.raises(ValueError, match="another document"):
        from_fixture_json(json.dumps(data))
