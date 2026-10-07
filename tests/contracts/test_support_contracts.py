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
        claim_id="c-0-10-1-0",
        doc_id="d",
        window_id="w-0-10",
        attempt=1,
        claim="Invented claim.",
        quote_ids=("q-0-10",),
    )
    expected = """{
 "attempt": 1,
 "claim": "Invented claim.",
 "claim_id": "c-0-10-1-0",
 "doc_id": "d",
 "quote_ids": [
  "q-0-10"
 ],
 "schema_version": 1,
 "window_id": "w-0-10"
}
"""
    assert record_json(claim) == expected.encode("utf-8")


def test_support_keeps_theme_examples_outside_assessment_contract():
    from earnings_themes.support.records import (
        EvidenceReference,
        JudgeAnswer,
        ReviewOutcome,
        ThemeSnapshot,
    )

    assert "examples" not in ThemeSnapshot.model_fields
    assert "quote_text" not in EvidenceReference.model_fields
    assert "accepted" not in ReviewOutcome.model_fields
    assert "new_theme" not in JudgeAnswer.model_fields
    assert "claim" not in JudgeAnswer.model_fields
    assert "definition" not in JudgeAnswer.model_fields


def test_default_support_import_does_not_export_concrete_adapters():
    from earnings_themes import support

    exports = tuple(name for name in vars(support) if not name.startswith("_"))
    assert "MiniCheckScorer" not in exports
    assert "DebertaScorer" not in exports
    assert "JudgeBinding" not in exports


def test_support_public_seams_retain_implemented_objects():
    from earnings_themes import support
    from earnings_themes.support import metrics, records
    from earnings_themes.support.assess import assess_target
    from earnings_themes.support.resolve import resolve_target
    from earnings_themes.support.run import assess_run
    from earnings_themes.support.store import (
        read_support_run,
        reverify_support_run,
        write_support_run,
    )

    expected = {
        "Target": records.Target,
        "SupportSources": records.SupportSources,
        "ResolvedInput": records.ResolvedInput,
        "resolve_target": resolve_target,
        "assess_target": assess_target,
        "assess_run": assess_run,
        "write_support_run": write_support_run,
        "read_support_run": read_support_run,
        "reverify_support_run": reverify_support_run,
        "HumanLabel": metrics.HumanLabel,
        "ContinuousSignal": metrics.ContinuousSignal,
        "Acceptance": metrics.Acceptance,
        "MetricReport": metrics.MetricReport,
        "auc_roc": metrics.auc_roc,
        "accepted_claim_precision": metrics.accepted_claim_precision,
    }
    for name, implementation in expected.items():
        assert name in support.__all__, name
        assert getattr(support, name) is implementation, name
