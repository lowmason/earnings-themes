"""Local views (the Stage 6 spec, §Anchoring and validation): the drafter's text
alone, and the verification view with every quote marked in place."""

from earnings_themes.anchoring import SpanPointer, anchor
from earnings_themes.gold import GoldQuote, Origin
from earnings_themes.synthetic import TEXT
from earnings_themes.view import marked, render_text


def quote(synthetic, quote_id: str, text: str, **context) -> GoldQuote:
    pointer = anchor(synthetic.bundle, text, **context)
    assert isinstance(pointer, SpanPointer)
    return GoldQuote(
        **pointer.model_dump(), quote_id=quote_id, origin=Origin.DRAFTED_ACCEPTED
    )


def test_the_text_view_holds_the_text_in_a_fence(synthetic) -> None:
    view = render_text(synthetic.bundle)
    assert view.startswith(f"# {synthetic.bundle.name}\n")
    assert f"```text\n{TEXT.rstrip()}\n```\n" in view


def test_a_fence_is_longer_than_any_backticks_in_the_text(synthetic) -> None:
    bundle = synthetic.bundle
    document = bundle.document.model_copy(update={"canonical_text": "Code ```` here"})
    view = render_text(type(bundle)(bundle.name, document, (), ()))
    assert "`````text\nCode ```` here\n`````" in view


def test_each_quote_is_marked_in_place_and_nested_marks_close_inside_out(
    synthetic,
) -> None:
    outer = quote(synthetic, "q1", "Revenue grew in every region. Margins held steady.")
    inner = quote(synthetic, "q2", "Margins held steady.")
    text = marked(TEXT, (inner, outer))
    assert (
        "[[q1>>Revenue grew in every region. [[q2>>Margins held steady.<<q2]]<<q1]]"
        in text
    )
    assert (
        text.replace("[[q1>>", "")
        .replace("[[q2>>", "")
        .replace("<<q2]]", "")
        .replace("<<q1]]", "")
        == TEXT
    )
