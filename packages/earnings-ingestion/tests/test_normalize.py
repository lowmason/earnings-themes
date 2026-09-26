"""N1 and V9's normalization cases (Stage 3 spec: Verification (plan A), item 7).

Every non-ASCII input is built from code points here, so no editor or tool can
normalize the test itself.
"""

import pytest
from earnings_ingestion.canonical.normalize import normalize

E_ACUTE_NFD = "e" + chr(0x0301)
E_ACUTE_NFC = chr(0x00E9)


def test_nfd_input_composes_to_nfc() -> None:
    assert normalize(f"caf{E_ACUTE_NFD}") == f"caf{E_ACUTE_NFC}"


def test_a_no_break_space_becomes_a_space() -> None:
    assert normalize(f"5{chr(0x00A0)}million") == "5 million"


@pytest.mark.parametrize(
    "deleted",
    [chr(0x00AD), chr(0x200B), chr(0x2060), chr(0xFEFF), chr(0x0007), chr(0x007F)],
    ids=["soft-hyphen", "zero-width-space", "word-joiner", "bom", "c0-bell", "delete"],
)
def test_invisible_and_control_characters_are_deleted(deleted: str) -> None:
    assert normalize(f"Net{deleted}sales") == "Netsales"


@pytest.mark.parametrize(
    "kept",
    [
        chr(0x00B9),  # superscript one
        chr(0x00BD),  # vulgar fraction one half
        chr(0xFB01),  # ligature fi
        chr(0xFF11) + chr(0xFF12),  # full-width digits one and two
        chr(0x2013),  # en dash
        chr(0x2014),  # em dash
        chr(0x2212),  # minus sign
        chr(0x201C) + chr(0x201D),  # curly double quotes
        chr(0x2018) + chr(0x2019),  # curly single quotes
    ],
    ids=[
        "superscript-one",
        "one-half",
        "fi-ligature",
        "full-width-digits",
        "en-dash",
        "em-dash",
        "minus-sign",
        "double-quotes",
        "single-quotes",
    ],
)
def test_compatibility_forms_dashes_and_quotes_are_preserved(kept: str) -> None:
    assert normalize(f"a {kept} b") == f"a {kept} b"


def test_the_replacement_character_is_preserved() -> None:
    assert normalize(f"caf{chr(0xFFFD)}") == f"caf{chr(0xFFFD)}"


def test_whitespace_collapses_after_deletion() -> None:
    assert normalize(f" Net \t{chr(0x200B)} \n sales{chr(0x2003)} ") == "Net sales"


def test_a_unit_left_empty_normalizes_to_the_empty_string() -> None:
    assert normalize(f"{chr(0x00AD)} {chr(0x200B)}\t") == ""


def test_whitespace_controls_collapse_rather_than_vanish() -> None:
    assert normalize("Net\x1csales") == "Net sales"
