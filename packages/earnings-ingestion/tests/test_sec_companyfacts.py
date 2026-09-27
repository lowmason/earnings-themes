"""SEC's companyfacts: the fiscal labels each periodic report states (Stage 5, EV6)."""

import json

import pytest
from earnings_ingestion.sec.companyfacts import FiscalLabels, read_companyfacts
from earnings_ingestion.sec.data import SecDataError


def fact(accn: str, fy: object, fp: object, **extra: object) -> dict:
    return {"end": "2024-08-31", "val": 1, "accn": accn, "fy": fy, "fp": fp} | extra


def facts(*entries: dict, concept: str = "Revenues") -> bytes:
    data = {
        "cik": 9990001,
        "entityName": "Acme Industrial Corp",
        "facts": {
            "us-gaap": {
                concept: {
                    "label": "Revenues",
                    "description": "Revenues.",
                    "units": {"USD": list(entries)},
                }
            }
        },
    }
    return json.dumps(data).encode()


def test_each_accession_takes_the_labels_its_facts_state() -> None:
    body = facts(
        fact("0009990001-24-000030", 2025, "Q1", form="10-Q"),
        fact("0009990001-24-000030", 2025, "Q1", start="2024-06-01"),
        fact("0009990001-24-000020", 2024, "FY", form="10-K"),
    )
    read = read_companyfacts(body)
    assert read.cik == "0009990001"
    assert read.labels["0009990001-24-000030"] == FiscalLabels(
        fiscal_year=2025,
        fiscal_period="Q1",
        pointer="/facts/us-gaap/Revenues/units/USD/0",
    )
    assert read.labels["0009990001-24-000020"].fiscal_period == "FY"


@pytest.mark.parametrize(
    "entries",
    [
        [fact("a", 2025, "Q1"), fact("a", 2025, "Q2")],
        [fact("a", 2025, "Q1"), fact("a", 2024, "Q1")],
        [fact("a", None, "Q1")],
        [fact("a", 2025, None)],
    ],
    ids=["periods-disagree", "years-disagree", "no-year", "no-period"],
)
def test_disagreeing_or_missing_labels_are_no_labels(entries) -> None:
    assert read_companyfacts(facts(*entries)).labels == {"a": None}


def test_a_concept_name_is_escaped_in_its_pointer() -> None:
    read = read_companyfacts(facts(fact("a", 2025, "Q3"), concept="Odd/Name~1"))
    assert read.labels["a"].pointer == "/facts/us-gaap/Odd~1Name~01/units/USD/0"


@pytest.mark.parametrize(
    "body",
    [
        b"<html>Undeclared Automated Tool</html>",
        b'{"cik": 9990001}',
        json.dumps({"cik": 9990001, "facts": {"us-gaap": {"R": {}}}}).encode(),
        facts({"end": "2024-08-31", "fy": 2025, "fp": "Q1"}),
        facts(fact("a", "2025", "Q1")),
        facts(fact("a", True, "Q1")),
        facts(fact("a", 2025, 1)),
    ],
    ids=[
        "html",
        "no-facts",
        "no-units",
        "no-accession",
        "year-not-a-number",
        "year-a-boolean",
        "period-not-text",
    ],
)
def test_facts_of_another_shape_are_refused(body) -> None:
    with pytest.raises(SecDataError):
        read_companyfacts(body)
