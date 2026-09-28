"""R1.2's exhibit choice (the Stage 5 spec, §Exhibit choice; plan 8, P8-8).

The candidates are the release filing's exhibits typed ``EX-99*`` on its saved index
page, tried in this order, each group by sequence number:

1. ``named``: each whose number the Item 2.02 text names, in "Exhibit 99.1",
   "Exhibit No. 99.1", or a list such as "Exhibits 99.1 and 99.2". A number is 99
   and a sub-number read as an integer, so "99.01" names ``EX-99.1``, and
   "Exhibit 99" names ``EX-99`` alone.
2. ``described``: each whose description on the index page has the word
   "release", such as "Press release" or "Earnings release".
3. ``lowest_sequence``: the rest.

Only the Item 2.02 sections are read, never Item 9.01's list, which names every
exhibit.
"""

import re
from dataclasses import dataclass

from earnings_ingestion.events.states import ExhibitChoice
from earnings_ingestion.sec.filing_index import FilingIndex, IndexDocument

_NUMBER = r"99(?:\.\d+)?(?!\d)"
_SEPARATOR = r"(?:\s*,\s*(?:and\s+)?|\s+and\s+|\s*&\s*)"
_NAMED = re.compile(
    rf"\bexhibits?\s+(?:no\.?\s*)?(?P<list>{_NUMBER}(?:{_SEPARATOR}{_NUMBER})*)",
    re.IGNORECASE,
)
_TYPE = re.compile(rf"^EX-(?P<number>{_NUMBER})$", re.IGNORECASE)
_RELEASE = re.compile(r"\brelease\b", re.IGNORECASE)

Number = tuple[int, int | None]


def _number(written: str) -> Number:
    main, _, sub = written.partition(".")
    return int(main), int(sub) if sub else None


def named_numbers(text: str) -> set[Number]:
    """The exhibit numbers ``text`` names."""
    return {
        _number(written)
        for match in _NAMED.finditer(text)
        for written in re.findall(_NUMBER, match["list"])
    }


@dataclass(frozen=True)
class ExhibitCandidate:
    document: IndexDocument
    choice: ExhibitChoice


def _type_number(document: IndexDocument) -> Number | None:
    match = _TYPE.match(document.doc_type.strip())
    return None if match is None else _number(match["number"])


def exhibit_order(index: FilingIndex, item_text: str) -> tuple[ExhibitCandidate, ...]:
    """The filing's ``EX-99*`` exhibits in the order R1.2 tries them."""
    exhibits = sorted(index.exhibits_99(), key=lambda document: document.sequence or 0)
    named = named_numbers(item_text)
    groups: dict[ExhibitChoice, list[ExhibitCandidate]] = {
        choice: []
        for choice in (
            ExhibitChoice.NAMED,
            ExhibitChoice.DESCRIBED,
            ExhibitChoice.LOWEST_SEQUENCE,
        )
    }
    for document in exhibits:
        if _type_number(document) in named:
            choice = ExhibitChoice.NAMED
        elif _RELEASE.search(document.description):
            choice = ExhibitChoice.DESCRIBED
        else:
            choice = ExhibitChoice.LOWEST_SEQUENCE
        groups[choice].append(ExhibitCandidate(document, choice))
    return tuple(candidate for group in groups.values() for candidate in group)
