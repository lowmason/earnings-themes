"""Locators cite saved evidence by position and hash, and catch any change."""

import json

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.cohort.locators import (
    ArtifactText,
    LocatorError,
    resolve_json_pointer,
)
from earnings_ingestion.cohort.records import LocatorKind

PAGE = (
    b"<html><body><h1>Synthetic roster</h1><table>"
    b"<tr><th>Company</th><th>Symbol</th></tr>"
    b"<tr><td>Acme Industrial</td><td>ACME</td></tr>"
    b"<tr><td>Borealis Air</td><td>BORA</td></tr>"
    b"</table></body></html>"
)
DATA = json.dumps({"0": {"ticker": "ACME", "cik_str": 9990001}, "a/b": [1, 2]}).encode()


def test_a_found_span_cites_its_text_by_hash() -> None:
    page = ArtifactText(PAGE, "text/html; charset=utf-8")
    locator = page.find("Acme Industrial")
    assert locator.kind is LocatorKind.TEXT_SPAN
    assert locator.canonicalization_version == "walker-1"
    assert locator.cited_sha256 == sha256_hex(b"Acme Industrial")
    assert page.cited(locator) == "Acme Industrial"


def test_a_table_row_is_one_tab_separated_line() -> None:
    page = ArtifactText(PAGE, "text/html")
    row = page.find("Borealis Air\tBORA")
    assert page.cited(row) == "Borealis Air\tBORA"


def test_a_line_cites_the_whole_row_holding_the_text() -> None:
    page = ArtifactText(PAGE, "text/html")
    row = page.line("BORA")
    assert page.cited(row) == "Borealis Air\tBORA"
    assert page.cited(page.line("Synthetic")) == "Synthetic roster"
    with pytest.raises(LocatorError, match="does not occur"):
        page.line("CRVD")


def test_the_nth_occurrence_is_found() -> None:
    page = ArtifactText(
        PAGE.replace(b"</body>", b"<p>ACME again</p></body>"), "text/html"
    )
    first, second = page.find("ACME"), page.find("ACME", occurrence=2)
    assert first.start < second.start
    with pytest.raises(LocatorError, match="does not occur 3 times"):
        page.find("ACME", occurrence=3)


def test_changed_bytes_or_a_changed_hash_fail_verification() -> None:
    locator = ArtifactText(PAGE, "text/html").find("Acme Industrial")
    edited = ArtifactText(
        PAGE.replace(b"Acme Industrial", b"Acme Industries"), "text/html"
    )
    with pytest.raises(LocatorError, match="canonical text is not the one cited"):
        edited.verify(locator)
    forged = locator.model_copy(update={"cited_sha256": "0" * 64})
    with pytest.raises(LocatorError, match="no longer hashes"):
        ArtifactText(PAGE, "text/html").verify(forged)


def test_a_span_outside_the_text_is_refused() -> None:
    page = ArtifactText(PAGE, "text/html")
    with pytest.raises(LocatorError, match="outside"):
        page.span(0, 10_000)


def test_a_pointer_cites_the_canonical_json_of_its_value() -> None:
    data = ArtifactText(DATA, "application/json")
    locator = data.pointer("/0")
    assert data.cited(locator) == '{"cik_str":9990001,"ticker":"ACME"}'
    assert data.cited(data.pointer("/a~1b/1")) == "2"


@pytest.mark.parametrize("pointer", ["/1", "/a~1b/2", "/a~1b/01", "0"])
def test_a_pointer_to_nothing_is_refused(pointer) -> None:
    with pytest.raises(LocatorError):
        resolve_json_pointer(json.loads(DATA), pointer)


def test_each_kind_needs_its_media_type() -> None:
    with pytest.raises(LocatorError, match="needs HTML"):
        ArtifactText(DATA, "application/json").find("ACME")
    with pytest.raises(LocatorError, match="needs JSON"):
        ArtifactText(PAGE, "text/html").pointer("/0")
