"""What a fetch returns, or how it refuses a response (plan 8, P8-12).

These hold no client and load no network library, so a package function that takes
a fetch callable, such as discovery or acquisition, never loads the client that the
CLI opens (P6-22). ``fetch.client`` raises and returns them.
"""

from dataclasses import dataclass

from earnings_ingestion.fetch.records import Retrieval


class UnexpectedResponse(RuntimeError):
    """A response that must not be kept; the caller may skip the item and go on."""


@dataclass(frozen=True)
class Fetched:
    """A validated response body and the record of its retrieval."""

    body: bytes
    retrieval: Retrieval
