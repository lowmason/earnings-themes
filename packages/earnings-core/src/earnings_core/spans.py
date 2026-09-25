"""TextSpan: a half-open range of Unicode code points in one canonical text (R3.2)."""

from typing import Self

from pydantic import NonNegativeInt, model_validator

from earnings_core._model import ContractModel


class TextSpan(ContractModel):
    """Zero-based, half-open ``[start, end)`` code-point offsets; never empty.

    Offsets index a Python ``str``, so they count code points: not UTF-8 bytes, not
    UTF-16 code units, and not model tokens (A §505, R3.2).
    """

    start: NonNegativeInt
    end: NonNegativeInt

    @model_validator(mode="after")
    def _start_before_end(self) -> Self:
        if self.start >= self.end:
            raise ValueError(f"span [{self.start}, {self.end}) is empty or reversed")
        return self

    @property
    def length(self) -> int:
        return self.end - self.start

    def contains(self, other: "TextSpan") -> bool:
        """True when ``other`` lies wholly inside this span; equal spans contain each other."""
        return self.start <= other.start and other.end <= self.end

    def overlaps(self, other: "TextSpan") -> bool:
        """True when the two spans share at least one code point."""
        return self.start < other.end and other.start < self.end

    def slice_of(self, text: str) -> str:
        """The spanned characters of ``text``; raises rather than truncate a short text."""
        if self.end > len(text):
            raise ValueError(
                f"span [{self.start}, {self.end}) runs past a text of length {len(text)}"
            )
        return text[self.start : self.end]
