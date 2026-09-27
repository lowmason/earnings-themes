"""A filing's EDGAR index page: form, acceptance, items, and documents (Stage 5)."""

from datetime import date

import pytest
from earnings_ingestion.sec.data import SecDataError
from earnings_ingestion.sec.filing_index import IndexDocument, read_filing_index

ROW = (
    '<tr><td scope="row">{seq}</td><td scope="row">{description}</td>'
    '<td scope="row"><a href="{href}">{name}</a></td>'
    '<td scope="row">{kind}</td><td scope="row">1000</td></tr>'
)


def page(
    *,
    form: str = "8-K",
    accession: str = "0009990001-24-000012",
    accepted: str = "2024-10-24 16:05:12",
    period: str | None = "2024-10-24",
    items: str | None = (
        "Item 2.02: Results of Operations and Financial Condition<br />"
        "Item 9.01: Financial Statements and Exhibits<br />"
    ),
) -> bytes:
    """An index page shaped as EDGAR writes them: a header of info pairs, then the
    Document Format Files table, then a Data Files table."""
    folder = "/Archives/edgar/data/9990001/000999000124000012"
    groups = [
        (
            '<div class="formGrouping"><div class="infoHead">Filing Date</div>'
            '<div class="info">2024-10-24</div><div class="infoHead">Accepted</div>'
            f'<div class="info">{accepted}</div><div class="infoHead">Documents</div>'
            '<div class="info">3</div></div>'
        )
    ]
    if period is not None:
        groups.append(
            '<div class="formGrouping"><div class="infoHead">Period of Report</div>'
            f'<div class="info">{period}</div></div>'
        )
    if items is not None:
        groups.append(
            '<div class="formGrouping"><div class="infoHead">Items</div>'
            f'<div class="info">{items}</div></div>'
        )
    rows = [
        ROW.format(
            seq=1,
            description="8-K",
            href=f"/ix?doc={folder}/acme-20241024.htm",
            name="acme-20241024.htm",
            kind=form,
        ),
        ROW.format(
            seq=2,
            description="PRESS RELEASE",
            href=f"{folder}/acme-ex991.htm",
            name="acme-ex991.htm",
            kind="EX-99.1",
        ),
        ROW.format(
            seq="&nbsp;",
            description="Complete submission text file",
            href=f"{folder}/{accession}.txt",
            name=f"{accession}.txt",
            kind="&nbsp;",
        ),
    ]
    data = ROW.format(
        seq=3,
        description="XBRL TAXONOMY EXTENSION SCHEMA DOCUMENT",
        href=f"{folder}/acme-20241024.xsd",
        name="acme-20241024.xsd",
        kind="EX-101.SCH",
    )
    return (
        "<html><head><title>EDGAR Filing Documents</title></head><body>"
        '<div class="formDiv"><div id="formHeader"><div id="formName">'
        f"<strong>Form {form}</strong> - Current report:</div>"
        '<div id="secNum"><strong>SEC Accession No.</strong> '
        f"{accession}</div></div>"
        f'<div class="formContent">{"".join(groups)}</div></div>'
        '<table class="tableFile" summary="Document Format Files">'
        "<tr><th>Seq</th><th>Description</th><th>Document</th><th>Type</th>"
        f"<th>Size</th></tr>{''.join(rows)}</table>"
        '<table class="tableFile" summary="Data Files">'
        "<tr><th>Seq</th><th>Description</th><th>Document</th><th>Type</th>"
        f"<th>Size</th></tr>{data}</table></body></html>"
    ).encode()


def test_the_header_and_the_documents_are_read() -> None:
    index = read_filing_index(page())
    assert index.accession == "0009990001-24-000012"
    assert index.form == "8-K"
    assert index.filing_date == date(2024, 10, 24)
    assert index.accepted == "2024-10-24 16:05:12"
    assert index.period_of_report == date(2024, 10, 24)
    assert index.items == ("2.02", "9.01")
    assert index.documents == (
        IndexDocument(1, "8-K", "acme-20241024.htm", "8-K"),
        IndexDocument(2, "PRESS RELEASE", "acme-ex991.htm", "EX-99.1"),
        IndexDocument(
            None,
            "Complete submission text file",
            "0009990001-24-000012.txt",
            "",
        ),
    )


@pytest.mark.parametrize(
    ("kind", "is_exhibit"),
    [
        ("EX-99", True),
        ("EX-99.1", True),
        ("EX-99.01", True),
        ("ex-99.2", True),
        ("EX-10.1", False),
        ("EX-101.INS", False),
    ],
)
def test_every_ex_99_numbering_is_an_exhibit_99(kind, is_exhibit) -> None:
    """The spec's ``EX-99*``: EX-99 with any numbering, as Stage 1 matched it."""
    body = page().replace(b">EX-99.1<", f">{kind}<".encode())
    assert bool(read_filing_index(body).exhibits_99()) is is_exhibit


def test_a_page_without_items_or_a_period_reads_empty() -> None:
    index = read_filing_index(page(form="10-Q", items=None, period=None))
    assert (index.items, index.period_of_report) == ((), None)


@pytest.mark.parametrize(
    "body",
    [
        b"<html><body>Request Rate Threshold Exceeded</body></html>",
        page(accepted="2024-10-24T16:05:12"),
        page(accepted="2024-10-24 4:05:12"),
        page(accepted="2024-02-30 16:05:12"),
        page(accepted="2024-10-24 24:05:12"),
        page().replace(b"Accepted", b"Received"),
        page(items="Results of Operations and Financial Condition<br />"),
        page().replace(b'summary="Document Format Files"', b'summary="Files"'),
        page(accession="not an accession"),
        b"",
    ],
    ids=[
        "block-page",
        "accepted-not-a-time",
        "accepted-not-padded",
        "accepted-no-such-day",
        "accepted-no-such-hour",
        "no-accepted",
        "items-without-numbers",
        "no-document-table",
        "no-accession",
        "empty",
    ],
)
def test_a_page_of_another_shape_is_refused(body) -> None:
    with pytest.raises(SecDataError):
        read_filing_index(body)
