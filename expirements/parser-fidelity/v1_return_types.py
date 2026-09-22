# /// script
# requires-python = ">=3.14"
# dependencies = ["edgartools==5.58.0"]
# ///
"""V1: declared and observed return types of edgartools 5.58.0's acquisition paths (live, opt-in).

    uv run --locked --script expirements/parser-fidelity/v1_return_types.py --live

Paths were enumerated from the installed 5.58.0 source (see PATHS). For each fixture
filing in the manifest, every path is called and its declared return annotation (read
with ``annotationlib.Format.STRING``) and observed runtime type are recorded, with
element types for containers and a foreign-dataframe flag (pandas or pyarrow).

Rate limit: edgartools 5.58.0 reads EDGAR_RATE_LIMIT_PER_SEC at import (httpclient.py,
default 9) into a per-process pyrate-limiter bucket, which allows two back-to-back
requests and counts nothing. This script sets it to 2 and also routes every httpx
transport request through the fetcher's throttle (0.5 s spacing, request cap, count).
A fresh EDGAR_LOCAL_DATA_DIR per run keeps edgartools' HTTP cache from hiding requests.
"""

from __future__ import annotations

import argparse
import functools
import inspect
import json
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import annotationlib
import tomllib
from pf_fetch import (
    DEFAULT_MAX_REQUESTS,
    LiveLock,
    LivePolicyStop,
    Throttle,
    require_identity,
)
from pf_paths import EDGAR_HOME, LIVE_LOCK, MANIFEST, RUNS

FOREIGN_PREFIXES = ("pandas.", "pyarrow.")


@dataclass(frozen=True)
class PathSpec:
    family: str  # a: list filings; b: filing -> attachments -> exhibit; c: tables
    call: str
    owner: str  # dotted path of the class that declares the member
    member: str
    run: Callable[[dict], object]


def qualname(obj: object) -> str:
    kind = type(obj)
    return f"{kind.__module__}.{kind.__qualname__}"


def describe(obj: object) -> dict:
    observed = qualname(obj)
    elements: list[str] = []
    if isinstance(obj, (list, tuple, set, frozenset)):
        elements = sorted({qualname(item) for item in obj})
    elif isinstance(obj, dict):
        elements = sorted({qualname(value) for value in obj.values()})
    foreign = [t for t in [observed, *elements] if t.startswith(FOREIGN_PREFIXES)]
    return {
        "observed": observed,
        "elements": elements,
        "foreign_dataframe": bool(foreign),
    }


def declared(owner: type, member: str) -> str:
    """The return annotation as written in the source, or '(none)'."""
    attribute = inspect.getattr_static(owner, member, None)
    if (
        attribute is None
    ):  # an instance attribute: a class-level annotation, else the __init__ parameter
        for klass in owner.__mro__:
            annotations = annotationlib.get_annotations(
                klass, format=annotationlib.Format.STRING
            )
            if member in annotations:
                return f"attribute: {annotations[member]}"
        parameter = inspect.signature(
            owner.__init__, annotation_format=annotationlib.Format.STRING
        ).parameters.get(member)
        if parameter is None or parameter.annotation is inspect.Parameter.empty:
            return "(none)"
        return f"__init__ parameter: {parameter.annotation}"
    if isinstance(attribute, property):
        function = attribute.fget
    elif isinstance(attribute, functools.cached_property):
        function = attribute.func
    elif isinstance(attribute, (staticmethod, classmethod)):
        function = attribute.__func__
    else:
        function = attribute
    function = inspect.unwrap(function)
    annotation = inspect.signature(
        function, annotation_format=annotationlib.Format.STRING
    ).return_annotation
    return "(none)" if annotation is inspect.Signature.empty else str(annotation)


def _owner(dotted: str) -> type:
    module, _, name = dotted.rpartition(".")
    return getattr(__import__(module, fromlist=[name]), name)


def _filing(ctx: dict) -> object:
    if "filing" not in ctx:
        ctx["filing"] = next(
            iter(
                ctx["company"].get_filings(
                    form="8-K", accession_number=ctx["accession"]
                )
            )
        )
    return ctx["filing"]


def _exhibit(ctx: dict) -> object:
    return next(
        a for a in _filing(ctx).attachments if a.document == ctx["exhibit_filename"]
    )


def _html(ctx: dict) -> str:
    content = _exhibit(ctx).content
    return (
        content.decode("utf-8", errors="replace")
        if isinstance(content, bytes)
        else content
    )


PATHS = [
    PathSpec("a", "Company(cik).get_filings(form='8-K', accession_number=...)", "edgar.entity.core.Entity", "get_filings",
             lambda c: c["company"].get_filings(form="8-K", accession_number=c["accession"])),
    PathSpec("a", "EntityFilings.data", "edgar.entity.filings.EntityFilings", "data",
             lambda c: c["company"].get_filings(form="8-K", accession_number=c["accession"]).data),
    PathSpec("a", "EntityFilings.to_pandas()", "edgar.entity.filings.EntityFilings", "to_pandas",
             lambda c: c["company"].get_filings(form="8-K", accession_number=c["accession"]).to_pandas()),
    PathSpec("a", "iterating EntityFilings", "edgar.entity.filings.EntityFilings", "__iter__", _filing),
    PathSpec("b", "Filing.attachments", "edgar._filings.Filing", "attachments", lambda c: _filing(c).attachments),
    PathSpec("b", "Attachments.exhibits", "edgar.attachments.Attachments", "exhibits", lambda c: _filing(c).attachments.exhibits),
    PathSpec("b", "iterating Attachments", "edgar.attachments.Attachments", "__iter__", _exhibit),
    PathSpec("b", "Attachment.content", "edgar.attachments.Attachment", "content", lambda c: _exhibit(c).content),
    PathSpec("b", "Attachment.download()", "edgar.attachments.Attachment", "download", lambda c: _exhibit(c).download()),
    PathSpec("b", "Attachment.text()", "edgar.attachments.Attachment", "text", lambda c: _exhibit(c).text()),
    PathSpec("b", "Attachment.markdown()", "edgar.attachments.Attachment", "markdown", lambda c: _exhibit(c).markdown()),
    PathSpec("b", "Filing.html()", "edgar._filings.Filing", "html", lambda c: _filing(c).html()),
    PathSpec("b", "Filing.obj()", "edgar._filings.Filing", "obj", lambda c: _filing(c).obj()),
    PathSpec("b", "EightK.press_releases", "edgar.company_reports.current_report.CurrentReport", "press_releases",
             lambda c: _filing(c).obj().press_releases),
    PathSpec("b", "PressRelease.html()", "edgar.company_reports.press_release.PressRelease", "html",
             lambda c: _filing(c).obj().press_releases[0].html()),
    PathSpec("b", "PressRelease.text()", "edgar.company_reports.press_release.PressRelease", "text",
             lambda c: _filing(c).obj().press_releases[0].text()),
    PathSpec("b", "EightK.earnings", "edgar.company_reports.current_report.CurrentReport", "earnings",
             lambda c: _filing(c).obj().earnings),
    PathSpec("b", "Filing.text()", "edgar._filings.Filing", "text", lambda c: _filing(c).text()),
    PathSpec("b", "Filing.markdown()", "edgar._filings.Filing", "markdown", lambda c: _filing(c).markdown()),
    PathSpec("b", "Attachments.markdown()", "edgar.attachments.Attachments", "markdown",
             lambda c: _filing(c).attachments.markdown()),
    PathSpec("b", "EightK.get_exhibits()", "edgar.company_reports.current_report.CurrentReport", "get_exhibits",
             lambda c: _filing(c).obj().get_exhibits()),
    PathSpec("b", "EightK.text()", "edgar.company_reports.current_report.CurrentReport", "text",
             lambda c: _filing(c).obj().text()),
    PathSpec("b", "EarningsRelease.from_filing(filing)", "edgar.earnings.EarningsRelease", "from_filing",
             lambda c: _owner("edgar.earnings.EarningsRelease").from_filing(_filing(c))),
    PathSpec("c", "parse_html(html).tables", "edgar.documents.document.Document", "tables",
             lambda c: __import__("edgar.documents", fromlist=["parse_html"]).parse_html(_html(c)).tables),
    PathSpec("c", "TableNode.to_dataframe()", "edgar.documents.table_nodes.TableNode", "to_dataframe",
             lambda c: __import__("edgar.documents", fromlist=["parse_html"]).parse_html(_html(c)).tables[0].to_dataframe()),
    PathSpec("c", "EarningsRelease.tables", "edgar.earnings.EarningsRelease", "tables",
             lambda c: _filing(c).obj().earnings.tables),
    PathSpec("c", "FinancialTable.dataframe", "edgar.earnings.FinancialTable", "dataframe",
             lambda c: _filing(c).obj().earnings.tables[0].dataframe),
    PathSpec("c", "EarningsRelease.to_facts_dataframe()", "edgar.earnings.EarningsRelease", "to_facts_dataframe",
             lambda c: _filing(c).obj().earnings.to_facts_dataframe()),
    PathSpec("c", "Document.to_dataframe()", "edgar.documents.document.Document", "to_dataframe",
             lambda c: __import__("edgar.documents", fromlist=["parse_html"]).parse_html(_html(c)).to_dataframe()),
    PathSpec("c", "FinancialTable.per_share_rows", "edgar.earnings.FinancialTable", "per_share_rows",
             lambda c: _filing(c).obj().earnings.tables[0].per_share_rows),
    PathSpec("c", "FinancialTable.scaled_dataframe", "edgar.earnings.FinancialTable", "scaled_dataframe",
             lambda c: _filing(c).obj().earnings.tables[0].scaled_dataframe),
    PathSpec("c", "EightK.get_income_statement()", "edgar.company_reports.current_report.CurrentReport",
             "get_income_statement", lambda c: _filing(c).obj().get_income_statement()),
    PathSpec("c", "EightK.get_balance_sheet()", "edgar.company_reports.current_report.CurrentReport",
             "get_balance_sheet", lambda c: _filing(c).obj().get_balance_sheet()),
    PathSpec("c", "EightK.get_cash_flow_statement()", "edgar.company_reports.current_report.CurrentReport",
             "get_cash_flow_statement", lambda c: _filing(c).obj().get_cash_flow_statement()),
    PathSpec("c", "EightK.income_statement", "edgar.company_reports.current_report.CurrentReport",
             "income_statement", lambda c: _filing(c).obj().income_statement),
    PathSpec("c", "EightK.balance_sheet", "edgar.company_reports.current_report.CurrentReport",
             "balance_sheet", lambda c: _filing(c).obj().balance_sheet),
    PathSpec("c", "EightK.cash_flow_statement", "edgar.company_reports.current_report.CurrentReport",
             "cash_flow_statement", lambda c: _filing(c).obj().cash_flow_statement),
    PathSpec("c", "EarningsRelease.income_statement", "edgar.earnings.EarningsRelease", "income_statement",
             lambda c: _filing(c).obj().earnings.income_statement),
    PathSpec("c", "EarningsRelease.balance_sheet", "edgar.earnings.EarningsRelease", "balance_sheet",
             lambda c: _filing(c).obj().earnings.balance_sheet),
    PathSpec("c", "EarningsRelease.cash_flow_statement", "edgar.earnings.EarningsRelease", "cash_flow_statement",
             lambda c: _filing(c).obj().earnings.cash_flow_statement),
    PathSpec("c", "EarningsRelease.segment_data", "edgar.earnings.EarningsRelease", "segment_data",
             lambda c: _filing(c).obj().earnings.segment_data),
    PathSpec("c", "EarningsRelease.eps_reconciliation", "edgar.earnings.EarningsRelease", "eps_reconciliation",
             lambda c: _filing(c).obj().earnings.eps_reconciliation),
    PathSpec("c", "EarningsRelease.guidance", "edgar.earnings.EarningsRelease", "guidance",
             lambda c: _filing(c).obj().earnings.guidance),
]  # fmt: skip


def install_transport_throttle(throttle: Throttle) -> None:
    """Route every sync and async httpx transport request through the fetcher's throttle."""
    import httpx

    sync_send = httpx.HTTPTransport.handle_request
    async_send = httpx.AsyncHTTPTransport.handle_async_request

    def handle_request(
        self: httpx.HTTPTransport, request: httpx.Request
    ) -> httpx.Response:
        throttle.acquire()
        return sync_send(self, request)

    async def handle_async_request(
        self: httpx.AsyncHTTPTransport, request: httpx.Request
    ) -> httpx.Response:
        throttle.acquire()
        return await async_send(self, request)

    httpx.HTTPTransport.handle_request = handle_request
    httpx.AsyncHTTPTransport.handle_async_request = handle_async_request


def run_paths(fixtures: list[dict]) -> list[dict]:
    import edgar

    records = []
    for fixture in fixtures:
        ctx = {
            "company": edgar.Company(int(fixture["cik"])),
            "accession": fixture["accession"],
            "exhibit_filename": fixture["exhibit_filename"],
        }
        for spec in PATHS:
            record = {
                "fixture_id": fixture["fixture_id"],
                "family": spec.family,
                "call": spec.call,
            }
            record["declared"] = declared(_owner(spec.owner), spec.member)
            try:
                value = spec.run(ctx)
                record.update(
                    describe(value)
                    if value is not None
                    else {
                        "observed": "NoneType",
                        "elements": [],
                        "foreign_dataframe": False,
                    }
                )
            except LivePolicyStop:
                raise
            except Exception as exc:  # noqa: BLE001 - a failing path is a V1 finding
                record.update(
                    observed=f"raised {type(exc).__name__}: {exc}",
                    elements=[],
                    foreign_dataframe=False,
                )
            records.append(record)
    return records


def conclusion(records: list[dict]) -> str:
    foreign = sorted({r["call"] for r in records if r["foreign_dataframe"]})
    if foreign:
        return "R14.5 cast required for: " + "; ".join(foreign)
    return "R14.5 vacuous: no path returns a foreign dataframe."


def render(records: list[dict], requests: int) -> str:
    lines = [
        "| family | call | declared | observed | elements | foreign |",
        "|---|---|---|---|---|---|",
    ]
    seen = set()
    for r in records:
        key = (r["call"], r["observed"], tuple(r["elements"]))
        if key in seen:
            continue
        seen.add(key)
        lines.append(
            f"| {r['family']} | `{r['call']}` | `{r['declared']}` | `{r['observed']}` "
            f"| {', '.join(f'`{e}`' for e in r['elements']) or '-'} | {'yes' if r['foreign_dataframe'] else 'no'} |"
        )
    return "\n".join(
        lines + ["", conclusion(records), "", f"Live requests made: {requests}."]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="required: confirms a live, rate-limited run",
    )
    parser.add_argument("--max-requests", type=int, default=DEFAULT_MAX_REQUESTS)
    parser.add_argument(
        "--list-paths",
        action="store_true",
        help="offline: print the edgartools source directory and each path's declared annotation",
    )
    args = parser.parse_args(argv)
    if args.list_paths:
        os.environ.setdefault("EDGAR_LOCAL_DATA_DIR", str(EDGAR_HOME))
        import edgar

        print(f"edgartools source: {os.path.dirname(edgar.__file__)}")
        for spec in PATHS:
            print(
                f"{spec.family} {spec.call}: {declared(_owner(spec.owner), spec.member)}"
            )
        return 0
    if not args.live:
        parser.error("V1 makes live requests; pass --live to confirm")
    require_identity()  # edgartools reads the same EDGAR_IDENTITY variable
    fixtures = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))["fixtures"]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    os.environ["EDGAR_RATE_LIMIT_PER_SEC"] = "2"
    os.environ["EDGAR_LOCAL_DATA_DIR"] = str(RUNS / f"edgar-home-v1-{stamp}")
    throttle = Throttle(max_requests=args.max_requests)
    out = RUNS / "v1"
    try:
        with LiveLock(LIVE_LOCK):
            install_transport_throttle(throttle)
            records = run_paths(fixtures)
    except LivePolicyStop as exc:
        print(f"STOPPED: {exc}; requests made: {throttle.count}", file=sys.stderr)
        return 1
    if throttle.count == 0:
        print(
            "no request passed through the transport throttle; the wrapper missed edgartools' client",
            file=sys.stderr,
        )
        return 1
    out.mkdir(parents=True, exist_ok=True)
    (out / "v1-results.json").write_text(
        json.dumps(records, indent=2) + "\n", encoding="utf-8"
    )
    (out / "v1-results.md").write_text(
        render(records, throttle.count) + "\n", encoding="utf-8"
    )
    print(render(records, throttle.count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
