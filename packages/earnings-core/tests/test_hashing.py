import hashlib

import pytest
from earnings_core.hashing import hash_canonical_text, sha256_hex


def test_sha256_hex_matches_the_published_test_vector() -> None:
    # FIPS 180-2, appendix B.1: SHA-256("abc").
    assert (
        sha256_hex(b"abc")
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_canonical_hash_is_sha256_of_the_utf8_bytes() -> None:
    text = "Revenue rose 5% to \u20ac2.1 billion \U0001f4c8 at the caf\u00e9."
    assert hash_canonical_text(text) == hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_canonical_hash_differs_for_composed_and_decomposed_accents() -> None:
    composed = "caf\u00e9"
    decomposed = "cafe\u0301"
    assert hash_canonical_text(composed) != hash_canonical_text(decomposed)


def test_a_lone_surrogate_cannot_be_hashed() -> None:
    with pytest.raises(UnicodeEncodeError):
        hash_canonical_text("broken \ud800 text")
