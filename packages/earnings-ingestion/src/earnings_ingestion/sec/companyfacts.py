"""SEC's companyfacts: the fiscal labels each periodic report states (Stage 5, EV6).

``companyfacts`` holds every XBRL fact a registrant filed, each with the accession
that filed it and that filing's fiscal year (``fy``) and period (``fp``). Stage 5
takes a slot's fiscal labels from the facts of its periodic report, as the source
writes them: a 10-K's ``FY`` is never renamed ``Q4``.

``read_companyfacts`` is a pure function of the saved bytes. It checks the shape it
relies on and raises ``SecDataError`` on any other (A §407). An accession whose facts
disagree, or leave a label out, has no labels: only non-periodic filings such as
8-Ks and S-8s did so in the files plan 7 read.
"""

from dataclasses import dataclass

from earnings_ingestion.sec.data import SecDataError, json_pointer_token, load_json
from earnings_ingestion.sec.identifiers import pad_cik


@dataclass(frozen=True)
class FiscalLabels:
    fiscal_year: int
    fiscal_period: str
    """``Q1``, ``Q2``, ``Q3``, or ``FY``, as the source writes it."""
    pointer: str
    """The JSON pointer of the first fact stating them."""


@dataclass(frozen=True)
class CompanyFacts:
    cik: str
    labels: dict[str, FiscalLabels | None]
    """By accession: the labels its facts state, or ``None`` if they disagree or
    leave one out."""


def _statement(fact: object, pointer: str) -> tuple[str, int | None, str | None]:
    """A fact's accession, ``fy``, and ``fp``."""
    if not isinstance(fact, dict) or not isinstance(fact.get("accn"), str):
        raise SecDataError(f"{pointer} is not a fact with an accession")
    year, period = fact.get("fy"), fact.get("fp")
    if year is not None and (isinstance(year, bool) or not isinstance(year, int)):
        raise SecDataError(f"{pointer}/fy is not a year")
    if period is not None and not isinstance(period, str):
        raise SecDataError(f"{pointer}/fp is not text")
    return fact["accn"], year, period


def read_companyfacts(body: bytes) -> CompanyFacts:
    data = load_json(body, "the companyfacts file")
    if not isinstance(data, dict) or not isinstance(data.get("facts"), dict):
        raise SecDataError("the companyfacts file has no facts object")
    if "cik" not in data:
        raise SecDataError("the companyfacts file has no cik")
    stated: dict[str, list[tuple[int | None, str | None, str]]] = {}
    for taxonomy, concepts in data["facts"].items():
        if not isinstance(concepts, dict):
            raise SecDataError(
                f"/facts/{json_pointer_token(taxonomy)} is not an object"
            )
        for concept, entry in concepts.items():
            where = (
                f"/facts/{json_pointer_token(taxonomy)}/{json_pointer_token(concept)}"
            )
            if not isinstance(entry, dict) or not isinstance(entry.get("units"), dict):
                raise SecDataError(f"{where} has no units object")
            for unit, facts in entry["units"].items():
                pointer = f"{where}/units/{json_pointer_token(unit)}"
                if not isinstance(facts, list):
                    raise SecDataError(f"{pointer} is not a list")
                for index, fact in enumerate(facts):
                    accession, year, period = _statement(fact, f"{pointer}/{index}")
                    stated.setdefault(accession, []).append(
                        (year, period, f"{pointer}/{index}")
                    )
    labels: dict[str, FiscalLabels | None] = {}
    for accession, statements in stated.items():
        year, period, pointer = statements[0]
        agreed = all((y, p) == (year, period) for y, p, _ in statements)
        if agreed and year is not None and period is not None:
            labels[accession] = FiscalLabels(year, period, pointer)
        else:
            labels[accession] = None
    return CompanyFacts(cik=pad_cik(data["cik"]), labels=labels)
