"""Support boundaries retain Stage 7 producer records unchanged."""

from earnings_themes.extraction.records import Claim, Quote
from earnings_themes.records import record_json
from earnings_themes.support.records import Target


def test_producer_records_remain_codebook_free():
    assert "theme" not in Claim.model_fields
    assert "codebook" not in Claim.model_fields
    assert "quote_text" not in Quote.model_fields
    assert "quote_ids" not in Target.model_fields
    assert "claim" not in Target.model_fields


def test_producer_serialization_is_unchanged():
    claim = Claim(
        claim_id="c",
        doc_id="d",
        window_id="w",
        attempt=1,
        claim="Invented claim.",
        quote_ids=("q-0-10",),
    )
    expected = """{
 "attempt": 1,
 "claim": "Invented claim.",
 "claim_id": "c",
 "doc_id": "d",
 "quote_ids": [
  "q-0-10"
 ],
 "schema_version": 1,
 "window_id": "w"
}
"""
    assert record_json(claim) == expected.encode("utf-8")
