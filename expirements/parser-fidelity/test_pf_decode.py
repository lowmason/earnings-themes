import codecs

import pytest
from pf_decode import decode_html_bytes
from pf_paths import fixture_id


def test_utf8_bom_wins_and_is_stripped():
    decoded = decode_html_bytes(codecs.BOM_UTF8 + "<p>caf\xe9</p>".encode())
    assert (decoded.text, decoded.encoding, decoded.basis) == (
        "<p>caf\xe9</p>",
        "UTF-8",
        "bom",
    )


def test_meta_latin1_label_means_windows_1252():
    raw = b'<html><head><meta charset="iso-8859-1"></head><body>\x93quoted\x94 \x92</body></html>'
    decoded = decode_html_bytes(raw)
    assert decoded.encoding == "windows-1252"
    assert decoded.basis == "meta"
    assert "\u201cquoted\u201d \u2019" in decoded.text


def test_meta_http_equiv_utf8():
    raw = '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><p>\u2014</p>'.encode()
    decoded = decode_html_bytes(raw)
    assert (decoded.encoding, decoded.basis) == ("UTF-8", "meta")
    assert "\u2014" in decoded.text


def test_meta_beyond_prescan_window_is_ignored():
    raw = b"<!--" + b" " * 1100 + b'--><meta charset="iso-8859-1"><p>\xc3\xa9</p>'
    decoded = decode_html_bytes(raw)
    assert (decoded.encoding, decoded.basis) == ("UTF-8", "valid-utf-8")
    assert "\xe9" in decoded.text


def test_unlabeled_invalid_utf8_falls_back_to_windows_1252():
    decoded = decode_html_bytes(b"<p>\x93Hi\x94 \x81</p>")
    assert (decoded.encoding, decoded.basis) == ("windows-1252", "default")
    assert decoded.text == "<p>\u201cHi\u201d \x81</p>"


def test_unknown_label_is_ignored():
    decoded = decode_html_bytes(b'<meta charset="no-such-charset"><p>plain</p>')
    assert decoded.basis == "valid-utf-8"
    assert decoded.ascii_only is True


def test_fixture_id_lowercases_and_replaces_dots():
    assert (
        fixture_id("0001234567-25-000123", "EX-99.1") == "0001234567-25-000123_ex-99-1"
    )


@pytest.mark.parametrize(
    ("accession", "exhibit"),
    [("123-25-1", "EX-99.1"), ("0001234567-25-000123", "EX 99(a)")],
)
def test_fixture_id_rejects_bad_input(accession, exhibit):
    with pytest.raises(ValueError):
        fixture_id(accession, exhibit)
