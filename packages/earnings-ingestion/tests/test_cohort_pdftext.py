"""pdftext-1, the citation text of a saved PDF (plan 6, P6-24).

The invented notice's text and its golden hash are the drift alarm, as walker-1's
golden test is. If pypdf's output changes, the remedy is pdftext-2 and new citations,
never an edited hash.
"""

import io
import logging

import pytest
from earnings_core import hash_canonical_text
from earnings_ingestion.cohort.pdftext import PDFTEXT_VERSION, PdfTextError, pdf_text
from pypdf import PdfReader, PdfWriter

TM = chr(0x2122)  # the trade mark sign: NFC keeps it, NFKC would spell it out
NOTICE = [
    [
        (72, 740, "Synthetic Index Services"),
        (72, 722, "Corvid Systems Set to Join the Synthetic Industrial Average"),
        (72, 692, "NEW YORK, Nov. 1, 2024: Corvid Systems will replace Borealis Air"),
        (72, 677, f"in the Synthetic Industrial Average{TM} prior to the open of"),
        (72, 662, "trading on Friday, November 8, 2024."),
        (72, 632, "Effective Date"),
        (170, 632, "Action"),
        (240, 632, "Company"),
        (400, 632, "Ticker"),
        (72, 614, "Nov 8, 2024"),
        (170, 614, "Adding"),
        (240, 614, "Corvid Systems"),
        (400, 614, "CRVD"),
        (170, 596, "Dropping"),
        (240, 596, "Borealis Air"),
        (400, 596, "BORA"),
        (72, 566, "   "),
        (72, 548, "  For more information,   contact the index team. "),
    ],
    [
        (72, 740, "About Synthetic Index Services"),
        (72, 722, "This notice is synthetic test data, invented for this repository."),
    ],
]
TEXT = "\n".join(
    [
        "Synthetic Index Services",
        "Corvid Systems Set to Join the Synthetic Industrial Average",
        "NEW YORK, Nov. 1, 2024: Corvid Systems will replace Borealis Air",
        f"in the Synthetic Industrial Average{TM} prior to the open of",
        "trading on Friday, November 8, 2024.",
        "Effective Date Action Company Ticker",
        "Nov 8, 2024 Adding Corvid Systems CRVD",
        "Dropping Borealis Air BORA",
        "For more information, contact the index team.",
        "About Synthetic Index Services",
        "This notice is synthetic test data, invented for this repository.",
    ]
)
GOLDEN = "4fe6134c599aec03e11250e8ff4e6f3010876d7cf6b061ac3248a4a152f3fd08"


def test_the_notice_extracts_to_its_golden_text(make_pdf) -> None:
    """Runs on one baseline join with single spaces, whitespace collapses, blank
    lines drop, pages join with a newline, and NFC keeps the trade mark sign."""
    text = pdf_text(make_pdf(*NOTICE))
    assert (PDFTEXT_VERSION, text) == ("pdftext-1", TEXT)
    assert hash_canonical_text(text) == GOLDEN


def test_a_rerun_is_identical(make_pdf) -> None:
    body = make_pdf(*NOTICE)
    assert pdf_text(body) == pdf_text(body)


def test_decomposed_text_is_normalized_to_nfc(make_pdf) -> None:
    body = make_pdf([(72, 720, "Cafe" + chr(0x301) + " au lait")])
    assert chr(0x301) in PdfReader(io.BytesIO(body)).pages[0].extract_text()
    assert pdf_text(body) == "Caf" + chr(0xE9) + " au lait"


@pytest.mark.parametrize("damage", ["garbage", "truncated", "empty"])
def test_bytes_pypdf_cannot_read_are_refused(make_pdf, damage) -> None:
    whole = make_pdf(*NOTICE)
    body = {
        "garbage": b"not a pdf at all",
        "truncated": whole[: len(whole) // 2],
        "empty": b"",
    }[damage]
    with pytest.raises(PdfTextError, match="pdftext-1 cannot read it"):
        pdf_text(body)


@pytest.mark.parametrize("user_password", ["", "secret"])
def test_an_encrypted_pdf_is_refused_even_one_that_opens(
    make_pdf, user_password
) -> None:
    """RC4, which pypdf writes with no extra dependency; an empty user password
    opens the file, and it is still refused."""
    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(make_pdf(*NOTICE))))
    writer.encrypt(
        user_password=user_password, owner_password="owner", algorithm="RC4-128"
    )
    out = io.BytesIO()
    writer.write(out)
    with pytest.raises(PdfTextError, match="pdftext-1 refuses an encrypted PDF"):
        pdf_text(out.getvalue())


def test_a_pdf_without_a_text_layer_is_refused(make_pdf) -> None:
    with pytest.raises(PdfTextError, match="pdftext-1 found no text layer"):
        pdf_text(make_pdf([]))


def test_recovery_warnings_are_silenced_and_the_logger_restored(
    make_pdf, caplog
) -> None:
    whole = make_pdf(*NOTICE)
    # Object 1 starts at byte 9; point its entry at byte 17, inside the object.
    damaged = whole.replace(b"0000000009 00000 n \n", b"0000000017 00000 n \n")
    caplog.set_level(logging.DEBUG, logger="pypdf")
    PdfReader(io.BytesIO(damaged))
    assert "Ignoring wrong pointing object 1 0" in caplog.text
    caplog.clear()
    assert pdf_text(damaged) == TEXT
    assert caplog.records == []
    assert logging.getLogger("pypdf").level == logging.DEBUG
    with pytest.raises(PdfTextError):
        pdf_text(b"not a pdf at all")
    assert logging.getLogger("pypdf").level == logging.DEBUG
