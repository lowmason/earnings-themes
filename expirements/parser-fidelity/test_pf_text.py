import pytest
from pf_space import fallback_space, find_all, primary_space
from pf_text import build_space_text, extract_document_text


def test_primary_space_deletes_whitespace_and_format_characters_and_keeps_case():
    assert primary_space("Net\xa0Sales \xadrose\u200b 5%") == "NetSalesrose5%"


def test_primary_space_applies_nfkc():
    assert primary_space("\ufb01scal \xbd") == "fiscal1\u20442"


def test_fallback_space_keeps_only_letters_and_digits_without_accents():
    assert (
        fallback_space("Soci\xe9t\xe9 \u201cGr\xe9n\u201d \u2014 Q3\u20192025")
        == "SocieteGrenQ32025"
    )


def test_find_all_counts_overlapping_occurrences():
    assert find_all("aaa", "aa") == [0, 1]
    with pytest.raises(ValueError):
        find_all("abc", "")


def test_build_space_text_maps_every_character_back_to_its_piece_and_offset():
    joined = build_space_text(["A b", "", "cd"], "primary")
    assert joined.text == "Abcd"
    assert joined.origins == ((0, 0), (0, 2), (2, 0), (2, 1))


def test_build_space_text_keeps_combining_marks_with_their_base():
    joined = build_space_text(["xe\u0301y"], "primary")
    assert joined.text == "x\xe9y"
    assert joined.origins == ((0, 0), (0, 1), (0, 3))


def test_build_space_text_fallback_space_maps_expansions():
    joined = build_space_text(["\xe9-\ufb01"], "fallback")
    assert joined.text == "efi"
    assert joined.origins == ((0, 0), (0, 2), (0, 2))


def test_extract_document_text_skips_head_script_and_style():
    html = (
        "<html><head><title>T</title><style>p{}</style></head>"
        "<body><p>One &amp; two</p><script>var x = 1;</script><p>three</p></body></html>"
    )
    assert extract_document_text(html) == "One & twothree"


def test_extract_document_text_recovers_from_an_unclosed_head():
    assert (
        extract_document_text("<head><title>T</title><p>Body text</p>") == "Body text"
    )
