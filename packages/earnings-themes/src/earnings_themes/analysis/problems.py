"""Closed analytical reasons; arbitrary source diagnostics never escape."""

from earnings_themes.coding.records import REASONS as CODING_REASONS
from earnings_themes.extraction.records import ExtractionProblem

ANALYSIS_REASONS = (
    frozenset(CODING_REASONS)
    | frozenset(problem.value for problem in ExtractionProblem)
    | frozenset(
        {
            "malformed_record",
            "storage_corrupt",
            "input_changed",
            "mixed_codebook",
            "policy_mismatch",
            "rights_restricted",
            "empty_denominator",
            "copy_processing_conflict",
            "empty_selection",
            "unexpected_error",
            "not_processed",
            "processing_failed",
            "extraction_partial",
            "classification_incomplete",
            "assessment_refused",
            "assessment_incomplete",
            "assessment_flagged",
            "calibration_required",
            "policy_review",
            "valid_unmatched",
            "no_theme_unconfirmed",
            "explicit_no_theme",
            "no_eligible_units",
            "transcript_not_in_scope",
            "not_yet_checked",
            "not_found",
            "no_confirmed_release",
            "parse_failed",
            "unsupported_media_type",
            "no_native_text",
            "invalid_elements",
            "period_end_outside_window",
            "no_release_filing",
            "several_release_filings",
            "published_after_cutoff",
            "member_at_publication",
            "not_member_at_publication",
            "same_day_transition",
            "snapshot_withheld",
            "raw_snapshot_missing",
            "policy_unavailable",
            "browser_unavailable",
            "startup_failure",
            "timeout",
            "blocked_required_resource",
            "document_load_failure",
            "capture_failure",
            "not_requested",
            "withheld",
            "replay_dispatch_forbidden",
        }
    )
)


class AnalysisError(ValueError):
    """Only a closed reason is printable, even for malformed exceptions."""

    def __init__(self, reason: str) -> None:
        self.reason = (
            reason
            if type(reason) is str and reason in ANALYSIS_REASONS
            else "unexpected_error"
        )
        super().__init__(self.reason)
