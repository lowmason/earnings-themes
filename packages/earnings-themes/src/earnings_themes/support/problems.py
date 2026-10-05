"""Fixed support refusal vocabulary; no source-bearing error details."""

from enum import StrEnum

from earnings_core import RejectionReason


class SupportProblem(StrEnum):
    MALFORMED_RECORD = "malformed_record"
    WRONG_SOURCE_RUN = "wrong_source_run"
    WRONG_DOCUMENT = "wrong_document"
    UNKNOWN_CLAIM = "unknown_claim"
    DUPLICATE_CLAIM = "duplicate_claim"
    UNKNOWN_QUOTE = "unknown_quote"
    DUPLICATE_QUOTE = "duplicate_quote"
    INVALID_QUOTE = "invalid_quote"
    MASKS_MISMATCH = "masks_mismatch"
    INVALID_BUNDLE = "invalid_bundle"
    WRONG_CODEBOOK = "wrong_codebook"
    CODEBOOK_NOT_APPROVED = "codebook_not_approved"
    UNKNOWN_THEME = "unknown_theme"
    DUPLICATE_THEME = "duplicate_theme"
    PARENT_CYCLE = "parent_cycle"
    UNKNOWN_PARENT = "unknown_parent"
    INPUT_CHANGED = "input_changed"
    INVALID_PANEL = "invalid_panel"
    INPUT_TOO_LONG = "input_too_long"
    REPLAY_MISS = "replay_miss"
    CACHE_CORRUPT = "cache_corrupt"
    TRANSPORT_ERROR = "transport_error"
    MODEL_MISMATCH = "model_mismatch"
    TOOL_CALL_REFUSED = "tool_call_refused"
    MALFORMED_REPLY = "malformed_reply"
    INVALID_REFERENCES = "invalid_references"
    SCORER_FAILED = "scorer_failed"
    SCORER_EXHAUSTED = "scorer_exhausted"
    JUDGE_EXHAUSTED = "judge_exhausted"
    TOKENS_EXHAUSTED = "tokens_exhausted"
    STORAGE_CORRUPT = "storage_corrupt"
    UNEXPECTED_ERROR = "unexpected_error"


REASONS = frozenset(
    {p.value for p in SupportProblem} | {r.value for r in RejectionReason}
)


class SupportError(ValueError):
    """A fixed reason only; unknown caller text is never printed."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            reason
            if isinstance(reason, str) and reason in REASONS
            else "unexpected_error"
        )


_TRUSTED_EXCEPTION_TYPES = {
    Exception: "Exception",
    RuntimeError: "RuntimeError",
    ValueError: "ValueError",
    TypeError: "TypeError",
    AttributeError: "AttributeError",
    KeyError: "KeyError",
    IndexError: "IndexError",
    OSError: "OSError",
    OverflowError: "OverflowError",
    AssertionError: "AssertionError",
    NotImplementedError: "NotImplementedError",
    TimeoutError: "TimeoutError",
    ConnectionError: "ConnectionError",
}


def unexpected_error(error: Exception) -> SupportError:
    """Only exact trusted builtin type identities supply a diagnostic name."""
    safe = SupportError("unexpected_error")
    safe.diagnostic = _TRUSTED_EXCEPTION_TYPES.get(type(error), "Exception")
    return safe
