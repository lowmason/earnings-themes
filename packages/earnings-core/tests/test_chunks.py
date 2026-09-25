import pytest
from earnings_core.chunks import TextChunk
from earnings_core.elements import ElementType
from earnings_core.rejections import Rejection, RejectionReason
from earnings_core.spans import TextSpan
from pydantic import ValidationError


def test_a_local_span_converts_to_the_same_document_text(sample) -> None:
    turn = sample.element(ElementType.SPEAKER_TURN, "CFO:")
    chunk = TextChunk.of(sample.document, turn.span)
    local_start = chunk.text.index("Margins held")
    local = TextSpan(start=local_start, end=local_start + len("Margins held"))
    converted = chunk.to_document_span(local)
    assert converted == sample.span_of("Margins held")
    assert converted.slice_of(sample.text) == local.slice_of(chunk.text)


def test_local_offsets_are_not_document_offsets(sample) -> None:
    turn = sample.element(ElementType.SPEAKER_TURN, "CFO:")
    chunk = TextChunk.of(sample.document, turn.span)
    local = TextSpan(start=0, end=4)
    assert local.slice_of(chunk.text) == "CFO:"
    assert local.slice_of(sample.text) != "CFO:"


def test_a_local_span_past_its_chunk_is_rejected(sample) -> None:
    chunk = TextChunk.of(sample.document, sample.span_of("Margins held"))
    outcome = chunk.to_document_span(TextSpan(start=0, end=len(chunk.text) + 1))
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.OUTSIDE_CHUNK


def test_a_chunk_cannot_run_past_its_document(sample) -> None:
    with pytest.raises(ValueError, match="runs past"):
        TextChunk.of(sample.document, TextSpan(start=0, end=len(sample.text) + 1))


def test_chunk_text_must_fill_its_span(sample) -> None:
    chunk = TextChunk.of(sample.document, sample.span_of("Margins held"))
    with pytest.raises(ValidationError, match="characters for a span"):
        TextChunk(
            doc_id=chunk.doc_id,
            canonical_hash=chunk.canonical_hash,
            span=chunk.span,
            text=chunk.text + " ",
        )


def test_a_chunk_carries_its_documents_identity(sample) -> None:
    chunk = TextChunk.of(sample.document, sample.span_of("Margins held"))
    assert (chunk.doc_id, chunk.canonical_hash) == (
        sample.document.doc_id,
        sample.document.canonical_hash,
    )
    assert TextChunk.model_validate_json(chunk.model_dump_json()) == chunk
