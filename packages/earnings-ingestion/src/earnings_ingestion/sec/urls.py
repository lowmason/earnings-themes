"""SEC hosts and URLs, with no network client: parsers and builders import these.

A module that reads saved SEC bytes needs the URLs they came from, to find them in
the artifact store and to cite them, but must never import the client that fetches
them (A §410); ``sec.client`` imports this module, never the reverse.
"""

from earnings_ingestion.sec.identifiers import pad_cik, unpad_cik

SEC_HOSTS = frozenset({"www.sec.gov", "data.sec.gov"})
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


def is_sec_host(host: str) -> bool:
    """True for sec.gov and every host under it: only the SEC client may reach them.

    DNS's trailing root dot is ignored, so ``www.sec.gov.`` is an SEC host too and
    goes to the SEC client, whose exact match on ``SEC_HOSTS`` then refuses it.
    """
    host = host.lower().rstrip(".")
    return host == "sec.gov" or host.endswith(".sec.gov")


def submissions_url(cik: str | int) -> str:
    return f"https://data.sec.gov/submissions/CIK{pad_cik(cik)}.json"


def submissions_page_url(name: str) -> str:
    """An older filings page named in a submissions file's ``filings.files``."""
    return f"https://data.sec.gov/submissions/{name}"


def archive_url(cik: str | int, accession: str, filename: str) -> str:
    """A filed document under EDGAR's archive, which uses the unpadded CIK."""
    folder = accession.replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{unpad_cik(cik)}/{folder}/{filename}"
    )
