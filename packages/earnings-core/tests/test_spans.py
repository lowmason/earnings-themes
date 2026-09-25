import pytest
from earnings_core.spans import TextSpan
from pydantic import ValidationError


def test_a_span_is_half_open() -> None:
    span = TextSpan(start=2, end=5)
    assert span.slice_of("abcdefg") == "cde"
    assert span.length == 3


@pytest.mark.parametrize(
    ("start", "end"),
    [(True, 5), (1.0, 5), ("1", 5), (1, 5.0), (-1, 5)],
    ids=["bool", "float", "numeric-string", "float-end", "negative"],
)
def test_offsets_are_strict_non_negative_integers(start: object, end: object) -> None:
    with pytest.raises(ValidationError):
        TextSpan(start=start, end=end)


@pytest.mark.parametrize(("start", "end"), [(3, 3), (5, 2)], ids=["empty", "reversed"])
def test_a_span_is_never_empty_or_reversed(start: int, end: int) -> None:
    with pytest.raises(ValidationError, match="empty or reversed"):
        TextSpan(start=start, end=end)


def test_offsets_count_code_points_not_bytes_or_utf16_units() -> None:
    text = "Up \U0001f4c8 at the caf\u00e9"
    span = TextSpan(start=text.index("at"), end=text.index("at") + 2)
    assert span.slice_of(text) == "at"
    utf8_start = text.encode("utf-8").index(b"at")
    utf16_start = text.encode("utf-16-le").index("at".encode("utf-16-le")) // 2
    assert utf8_start != span.start
    assert utf16_start != span.start


def test_slicing_past_the_text_raises_rather_than_truncates() -> None:
    with pytest.raises(ValueError, match="runs past"):
        TextSpan(start=2, end=9).slice_of("abc")


def test_containment_and_overlap() -> None:
    outer = TextSpan(start=0, end=10)
    inner = TextSpan(start=2, end=5)
    crossing = TextSpan(start=8, end=12)
    after = TextSpan(start=10, end=12)
    assert outer.contains(inner)
    assert outer.contains(outer)
    assert not inner.contains(outer)
    assert outer.overlaps(crossing)
    assert not outer.contains(crossing)
    assert not outer.overlaps(after)


def test_a_span_is_immutable_and_round_trips_through_json() -> None:
    span = TextSpan(start=4, end=9)
    with pytest.raises(ValidationError):
        span.start = 0
    assert TextSpan.model_validate_json(span.model_dump_json()) == span
