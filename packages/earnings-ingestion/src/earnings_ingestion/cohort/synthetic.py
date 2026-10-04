"""A synthetic, redistributable cohort (P §Verification): every company, page,
record, and filing here is invented, so all of it may be committed.

``write_synthetic_cohort(repo, directory)`` writes under ``repo / directory``:

- ``membership-source-register.toml`` and ``source-register.toml``: the registers;
- ``raw/``: an artifact store holding the roster revisions, the index notices, SEC's
  ticker list and submissions, and the fund's N-PORT filings;
- ``universe.toml`` and ``evidence.toml``: the curated files;
- ``overrides.toml``: the decisions a reviewer makes against the build's findings;
- ``manifests/``: the frozen manifest, which Stage 5's offline tests consume.

The scenario exercises P-VF's Stage 4 cases: an anchor with additions and removals,
a date conflict settled by review, a change published after the cutoff, a ticker
change, a former name, two share classes of one issuer, an identity override, an
amended fund filing, a lagging secondary snapshot, and an uncorroborated quarter.
"""

import json
from datetime import UTC, date, datetime
from pathlib import Path

from earnings_core import RightsStatus, canonical_json, sha256_hex

from earnings_ingestion.cohort.build import build
from earnings_ingestion.cohort.freeze import freeze
from earnings_ingestion.cohort.locators import ArtifactText
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.identifiers import pad_cik
from earnings_ingestion.sec.urls import (
    COMPANY_TICKERS_URL,
    archive_url,
    submissions_url,
)

FIXTURE_DIR = Path("tests") / "fixtures" / "cohort"
UNIVERSE_ID = "djia-synthetic"
CUTOFF = date(2026, 9, 22)
RETRIEVED = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)
FROZEN_AT = datetime(2026, 9, 28, 0, 0, tzinfo=UTC)
REVIEWER = "Synthetic Reviewer"
FUND_CIK = pad_cik(9990900)
NPORT_DOCUMENT = "xslFormNPORT-P_X01/primary_doc.xml"
RIGHTS = {
    "rights_status": RightsStatus.REDISTRIBUTABLE,
    "rights_basis": "synthetic test data, invented for this repository",
}

COMPANIES = {
    # cik: (SEC name, tickers, former names)
    9990001: ("Acme Industrial Corp", ["ACME"], []),
    9990002: ("Borealis Air Inc", ["BORA"], ["Northern Airways Inc"]),
    9990003: ("Corvid Systems Inc", ["CRVD"], []),
    9990005: ("Dynamo Motors Co", ["DYNA", "DYNB"], []),
    9990006: ("Eastfield Bank Corp", ["EFB"], []),
    9990007: ("Fenwick Laboratories Inc", ["FNWK"], []),
    9990900: ("Synthetic Industrial Average Fund Trust", ["SIAF"], []),
}
ROW = {
    # security_id: (name, ticker) as the rosters and notices print them
    "acme-old": ("Acme Industrial", "ACMX"),
    "acme": ("Acme Industrial", "ACME"),
    "borealis-old": ("Northern Airways", "BORA"),
    "borealis": ("Borealis Air", "BORA"),
    "corvid": ("Corvid Systems", "CRVD"),
    "dynamo-a": ("Dynamo Motors (Class A)", "DYNA"),
    "dynamo-b": ("Dynamo Motors (Class B)", "DYNB"),
    "eastfield": ("EFB Financial", "EFB"),
    "fenwick": ("Fenwick Labs", "FNWK"),
}
SECURITY = {
    "acme-old": "acme-common",
    "acme": "acme-common",
    "borealis-old": "borealis-common",
    "borealis": "borealis-common",
    "corvid": "corvid-common",
    "dynamo-a": "dynamo-class-a",
    "dynamo-b": "dynamo-class-b",
    "eastfield": "eastfield-common",
    "fenwick": "fenwick-common",
}
ROSTERS = [
    # evidence_id, revision, role, as_of, published_on, rows
    (
        "roster-2024-06-28",
        1001,
        "anchor",
        date(2024, 6, 28),
        date(2024, 6, 20),
        ["acme-old", "borealis-old", "dynamo-a", "eastfield"],
    ),
    (
        "roster-2024-11-08",
        1002,
        "corroboration",
        date(2024, 11, 8),
        date(2024, 11, 8),
        ["acme-old", "borealis", "dynamo-a", "eastfield"],
    ),
    (
        "roster-2025-06-30",
        1003,
        "corroboration",
        date(2025, 6, 30),
        date(2025, 6, 30),
        ["acme", "corvid", "dynamo-a", "eastfield"],
    ),
]
NOTICES = [
    # evidence_id, announced, published_at, effective, date phrase, added, removed
    (
        "index-2024-10-31",
        date(2024, 10, 31),
        datetime(2024, 10, 31, 21, 0, tzinfo=UTC),
        date(2024, 11, 7),
        "prior to the open of trading on Thursday, November 7, 2024",
        ["corvid"],
        [],
    ),
    (
        "index-2024-11-01",
        date(2024, 11, 1),
        datetime(2024, 11, 1, 21, 15, tzinfo=UTC),
        date(2024, 11, 8),
        "prior to the open of trading on Friday, November 8, 2024",
        ["corvid"],
        ["borealis"],
    ),
    (
        "index-2026-06-16",
        date(2026, 6, 16),
        datetime(2026, 6, 16, 21, 0, tzinfo=UTC),
        date(2026, 6, 22),
        "prior to the open of trading on Monday, June 22, 2026",
        ["dynamo-b"],
        ["eastfield"],
    ),
    (
        "index-2026-09-25",
        date(2026, 9, 25),
        datetime(2026, 9, 25, 21, 0, tzinfo=UTC),
        date(2026, 10, 5),
        "prior to the open of trading on Monday, October 5, 2026",
        ["fenwick"],
        ["acme"],
    ),
]
BEFORE = ["Acme Industrial Corp", "Borealis Air Inc", "Dynamo Motors Co Class A"]
MIDDLE = ["Acme Industrial Corp", "Corvid Systems Inc", "Dynamo Motors Co Class A"]
AFTER = [*MIDDLE, "Dynamo Motors Co Class B"]
FILINGS = [
    # accession suffix, form, filed, report date, holdings
    (
        "24-000001",
        "NPORT-P",
        date(2024, 11, 26),
        date(2024, 9, 30),
        [*BEFORE, "Eastfield Bank Corp"],
    ),
    (
        "25-000001",
        "NPORT-P",
        date(2025, 2, 26),
        date(2024, 12, 31),
        [*MIDDLE, "Eastfield Bank Corp"],
    ),
    (
        "25-000002",
        "NPORT-P",
        date(2025, 5, 28),
        date(2025, 3, 31),
        [*BEFORE, "Eastfield Bank Corp"],
    ),
    (
        "25-000003",
        "NPORT-P/A",
        date(2025, 6, 10),
        date(2025, 3, 31),
        [*MIDDLE, "Eastfield Bank Corp"],
    ),
    (
        "25-000004",
        "NPORT-P",
        date(2025, 8, 27),
        date(2025, 6, 30),
        [*MIDDLE, "Eastfield Bank Corp"],
    ),
    (
        "25-000005",
        "NPORT-P",
        date(2025, 11, 25),
        date(2025, 9, 30),
        [*MIDDLE, "Eastfield Bank Corp"],
    ),
    (
        "26-000001",
        "NPORT-P",
        date(2026, 2, 25),
        date(2025, 12, 31),
        [*MIDDLE, "Eastfield Bank Corp"],
    ),
    (
        "26-000002",
        "NPORT-P",
        date(2026, 5, 27),
        date(2026, 3, 31),
        [*MIDDLE, "Eastfield Bank Corp"],
    ),
    ("26-000003", "NPORT-P", date(2026, 8, 26), date(2026, 6, 30), AFTER),
    ("26-000004", "NPORT-P/A", date(2026, 9, 24), date(2026, 6, 30), AFTER),
]
USER_LIST = ["acme", "corvid", "dynamo-a", "dynamo-b", "fenwick"]


def _toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, date)):
        return value.isoformat() if isinstance(value, date) else str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    raise TypeError(f"no TOML form for {type(value).__name__}")


def _toml(data: dict, prefix: str = "") -> list[str]:
    """TOML for ``data``: scalars, tables, and arrays of tables, in key order."""
    lines = []
    for key, value in data.items():
        if isinstance(value, dict) or (
            isinstance(value, list) and value and isinstance(value[0], dict)
        ):
            continue
        if value is not None:
            lines.append(f"{key} = {_toml_value(value)}")
    for key, value in data.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            lines += ["", f"[{name}]", *_toml(value, f"{name}.")]
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            for entry in value:
                lines += ["", f"[[{name}]]", *_toml(entry, f"{name}.")]
    return lines


def _write_toml(path: Path, header: str, data: dict) -> None:
    body = "\n".join(_toml(data)).strip("\n")
    path.write_text(f"# {header}\n{body}\n", encoding="utf-8")


def _save(
    store: ArtifactStore, source_id: str, url: str, body: bytes, media: str
) -> str:
    retrieval = Retrieval(
        request_url=url,
        final_url=url,
        retrieved_at=RETRIEVED,
        retrieval_method=RetrievalMethod.HTTP,
        http_status=200,
        media_type=media,
        content_type=media,
        byte_count=len(body),
        sha256=sha256_hex(body),
    )
    return store.put(source_id, body, retrieval, **RIGHTS).content_sha256


def _roster_page(revision: int, as_of: date, rows: list[str]) -> bytes:
    cells = "".join(
        f"<tr><td>{ROW[key][0]}</td><td>{ROW[key][1]}</td><td>Industrials</td></tr>"
        for key in rows
    )
    return (
        "<html><head><title>Synthetic Industrial Average</title></head><body>"
        "<h1>Synthetic Industrial Average</h1>"
        f"<p>Revision {revision}. Components as of {as_of:%B} {as_of.day}, {as_of.year}:</p>"
        "<table><tr><th>Company</th><th>Symbol</th><th>Sector</th></tr>"
        f"{cells}</table></body></html>"
    ).encode()


def _named(key: str) -> str:
    name, ticker = ROW[key]
    return f"{name} ({ticker})"


def _notice_page(phrase: str, added: list[str], removed: list[str]) -> bytes:
    joined = " and ".join(_named(key) for key in added)
    if removed:
        replaced = " and ".join(_named(key) for key in removed)
        sentence = f"{joined} will replace {replaced} in the Synthetic Industrial Average {phrase}."
    else:
        sentence = f"{joined} will join the Synthetic Industrial Average {phrase}."
    return (
        "<html><head><title>Synthetic Index Notice</title></head><body>"
        "<h1>Synthetic Index Services announces a change</h1>"
        f"<p>{sentence}</p><p>This notice is synthetic test data.</p></body></html>"
    ).encode()


def _submissions(cik: int, filings: list[tuple] = ()) -> bytes:
    name, tickers, former = COMPANIES[cik]
    columns = {
        "accessionNumber": [],
        "filingDate": [],
        "reportDate": [],
        "acceptanceDateTime": [],
        "form": [],
        "primaryDocument": [],
    }
    for suffix, form, filed, report, _ in sorted(
        filings, reverse=True, key=lambda f: f[2]
    ):
        columns["accessionNumber"].append(f"{FUND_CIK}-{suffix}")
        columns["filingDate"].append(filed.isoformat())
        columns["reportDate"].append(report.isoformat())
        columns["acceptanceDateTime"].append(f"{filed.isoformat()}T16:05:00.000Z")
        columns["form"].append(form)
        columns["primaryDocument"].append(NPORT_DOCUMENT)
    data = {
        "cik": str(cik),
        "name": name,
        "tickers": tickers,
        "formerNames": [
            {
                "name": n,
                "from": "2001-01-01T00:00:00.000Z",
                "to": "2019-12-31T00:00:00.000Z",
            }
            for n in former
        ],
        "filings": {"recent": columns, "files": []},
    }
    return canonical_json(data)


def _nport(report: date, holdings: list[str]) -> bytes:
    positions = "".join(
        f"<invstOrSec><name>{name}</name><title>{name}</title>"
        "<assetCat>EC</assetCat></invstOrSec>"
        for name in holdings
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<edgarSubmission xmlns="http://www.sec.gov/edgar/nport">'
        "<formData><genInfo>"
        f"<repPdDate>{report.isoformat()}</repPdDate></genInfo><invstOrSecs>"
        f"{positions}<invstOrSec><name>Synthetic Treasury Money Fund</name>"
        "<assetCat>STIV</assetCat></invstOrSec></invstOrSecs></formData>"
        "</edgarSubmission>"
    ).encode()


def _cite(text: ArtifactText, needle: str) -> dict:
    locator = text.find(needle)
    return {"span": [locator.start, locator.end], "cited_sha256": locator.cited_sha256}


def _registers(root: Path) -> None:
    common = {
        "cost": "Free; synthetic.",
        "license_terms": "Invented for this repository's tests.",
        "redistribution_status": "Synthetic; committed as test data.",
        "expected_update_pattern": "Never updated.",
        "known_limitations": ["Synthetic: it describes no real index."],
        "last_verified": date(2026, 9, 27),
        "rights_status": "redistributable",
        "rights_basis": "synthetic test data, invented for this repository",
        "terms_sha256": sha256_hex(b"synthetic terms"),
    }
    sources = {
        "synthetic-roster": {
            "owner": "Synthetic Encyclopedia",
            "url": "https://roster.example/index",
            "access_method": "Fixed revisions through the cohort web client.",
            "terms_url": "https://roster.example/terms",
            "coverage": "Dated revisions of the roster.",
            "evidence_class": "secondary",
            "roles": ["anchor", "corroboration"],
        },
        "synthetic-index": {
            "owner": "Synthetic Index Services",
            "url": "https://index.example/notices",
            "access_method": "Notices through the cohort web client.",
            "terms_url": "https://index.example/terms",
            "coverage": "Every addition and removal.",
            "evidence_class": "official",
            "roles": ["change"],
        },
        "synthetic-fund": {
            "owner": "Synthetic Industrial Average Fund Trust",
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?CIK=0009990900",
            "access_method": "N-PORT filings through the shared SEC client.",
            "terms_url": "https://www.sec.gov/privacy",
            "coverage": "Quarterly holdings.",
            "evidence_class": "etf_proxy",
            "roles": ["corroboration"],
        },
        "user-list": {
            "owner": "The user",
            "url": "https://user.example/list",
            "access_method": "Supplied in conversation.",
            "terms_url": "https://user.example/terms",
            "coverage": "One list, as of the cutoff.",
            "evidence_class": "user_supplied",
            "roles": ["check"],
        },
    }
    register = {
        "schema_version": 1,
        "sources": {key: value | common for key, value in sources.items()},
    }
    _write_toml(
        root / "membership-source-register.toml", "Synthetic register.", register
    )
    sec = {
        "sources": {
            "sec-edgar": {"owner": "Synthetic SEC", "last_verified": date(2026, 9, 27)}
        }
    }
    _write_toml(root / "source-register.toml", "Synthetic sec-edgar entry.", sec)


def _evidence(store: ArtifactStore) -> dict:
    snapshots, changes = [], []
    for evidence_id, revision, role, as_of, published, rows in ROSTERS:
        url = f"https://roster.example/index?rev={revision}"
        body = _roster_page(revision, as_of, rows)
        sha = _save(store, "synthetic-roster", url, body, "text/html")
        text = ArtifactText(body, "text/html")
        members = [
            {
                "security_id": SECURITY[key],
                "name": ROW[key][0],
                "ticker": ROW[key][1],
                **_cite(text, f"{ROW[key][0]}\t{ROW[key][1]}"),
            }
            for key in rows
        ]
        snapshots.append(
            {
                "evidence_id": evidence_id,
                "source_id": "synthetic-roster",
                "role": role,
                "url": url,
                "artifact_sha256": sha,
                "canonical_sha256": text.canonical[1],
                "as_of": as_of,
                "published_on": published,
                "members": members,
            }
        )
    for (
        evidence_id,
        announced,
        published_at,
        effective,
        phrase,
        added,
        removed,
    ) in NOTICES:
        url = f"https://index.example/notices/{evidence_id}"
        body = _notice_page(phrase, added, removed)
        sha = _save(store, "synthetic-index", url, body, "text/html")
        text = ArtifactText(body, "text/html")
        dated = _cite(text, phrase)
        entries = [
            {
                "action": action,
                "security_id": SECURITY[key],
                "name": ROW[key][0],
                "ticker": ROW[key][1],
                **_cite(text, _named(key)),
            }
            for action, keys in (("added", added), ("removed", removed))
            for key in keys
        ]
        changes.append(
            {
                "evidence_id": evidence_id,
                "source_id": "synthetic-index",
                "url": url,
                "artifact_sha256": sha,
                "canonical_sha256": text.canonical[1],
                "announced_on": announced,
                "published_on": published_at.date(),
                "published_at": published_at.isoformat().replace("+00:00", "Z"),
                "effective_on": effective,
                "timing": "before_open",
                "date_span": dated["span"],
                "date_cited_sha256": dated["cited_sha256"],
                "entries": entries,
            }
        )
    check = {
        "evidence_id": "user-list-2026-09-26",
        "source_id": "user-list",
        "as_of": CUTOFF,
        "published_on": date(2026, 9, 26),
        "members": [{"name": ROW[k][0], "ticker": ROW[k][1]} for k in USER_LIST],
    }
    return {
        "schema_version": 1,
        "snapshots": snapshots,
        "changes": changes,
        "checks": [check],
    }


def _sec(store: ArtifactStore) -> dict[str, str]:
    """Save SEC's records; return the submissions hash of each CIK."""
    tickers = {
        str(index): {"cik_str": cik, "ticker": ticker, "title": name}
        for index, (cik, ticker, name) in enumerate(
            (cik, ticker, name)
            for cik, (name, symbols, _) in COMPANIES.items()
            for ticker in symbols
        )
    }
    _save(
        store,
        "sec-edgar",
        COMPANY_TICKERS_URL,
        canonical_json(tickers),
        "application/json",
    )
    hashes = {}
    for cik in COMPANIES:
        body = _submissions(cik, FILINGS if pad_cik(cik) == FUND_CIK else [])
        hashes[pad_cik(cik)] = _save(
            store, "sec-edgar", submissions_url(cik), body, "application/json"
        )
    for suffix, _, _, report, holdings in FILINGS:
        url = archive_url(FUND_CIK, f"{FUND_CIK}-{suffix}", "primary_doc.xml")
        _save(store, "synthetic-fund", url, _nport(report, holdings), "application/xml")
    return hashes


def _override(override_id: str, kind: str, rationale: str, **fields) -> dict:
    return {
        "override_id": override_id,
        "kind": kind,
        **fields,
        "rationale": rationale,
        "reviewer": REVIEWER,
        "recorded_on": date(2026, 9, 28),
        "effective_from": date(2024, 7, 1),
    }


def build_options(directory: Path = FIXTURE_DIR) -> dict[str, Path]:
    """``build``'s keywords for a synthetic cohort written under ``directory``."""
    return {
        "config_dir": directory,
        "store_root": directory / "raw",
        "register": directory / "membership-source-register.toml",
        "sec_register": directory / "source-register.toml",
    }


def write_synthetic_cohort(repo: Path, directory: Path = FIXTURE_DIR) -> Path:
    """Write the synthetic cohort and freeze it; return the manifest's path."""
    root = repo / directory
    root.mkdir(parents=True, exist_ok=True)
    store = ArtifactStore(root / "raw", repo)
    _registers(root)
    universe = {
        "universe_id": UNIVERSE_ID,
        "universe_name": "djia",
        "period_end_start": date(2024, 7, 1),
        "period_end_stop": date(2026, 7, 1),
        "public_information_cutoff": CUTOFF,
        "membership_reference": "first_publication_time",
        "selection_policy_version": "djia-pilot/1",
        "expected_member_count": 4,
        "etf_proxy": {"source_id": "synthetic-fund", "cik": FUND_CIK},
    }
    _write_toml(root / "universe.toml", "Synthetic universe.", universe)
    _write_toml(root / "evidence.toml", "Synthetic evidence.", _evidence(store))
    hashes = _sec(store)

    fund_document = archive_url(FUND_CIK, f"{FUND_CIK}-25-000001", "primary_doc.xml")
    fund_citation = [{"source_id": "synthetic-fund", "url": fund_document}]
    submissions = submissions_url(9990006)
    submissions_text = ArtifactText(
        store.get("sec-edgar", hashes[pad_cik(9990006)], **RIGHTS).body,
        "application/json",
    )
    overrides = [
        _override(
            "reject-preliminary-date",
            "reject_assertion",
            "index-2024-11-01 sets November 8, replacing the preliminary November 7.",
            membership_assertion_id="index-2024-10-31:corvid-common:added",
            citations=[
                {
                    "source_id": "synthetic-index",
                    "url": "https://index.example/notices/index-2024-11-01",
                }
            ],
        ),
        _override(
            "eastfield-issuer",
            "set_issuer",
            "SEC's record for this CIK lists EFB; EFB Financial is its trade name.",
            security_id="eastfield-common",
            cik=pad_cik(9990006),
            citations=[
                {
                    "source_id": "sec-edgar",
                    "url": submissions,
                    "artifact_sha256": hashes[pad_cik(9990006)],
                    "locator": submissions_text.pointer("/tickers").model_dump(
                        mode="json", exclude_none=True
                    ),
                }
            ],
        ),
        _override(
            "alias-dynamo-a",
            "holding_alias",
            "The fund lists the Class A shares under this name.",
            security_id="dynamo-class-a",
            holding_name="Dynamo Motors Co Class A",
            citations=fund_citation,
        ),
        _override(
            "alias-dynamo-b",
            "holding_alias",
            "The fund lists the Class B shares under this name.",
            security_id="dynamo-class-b",
            holding_name="Dynamo Motors Co Class B",
            citations=fund_citation,
        ),
        _override(
            "alias-eastfield",
            "holding_alias",
            "The fund lists EFB Financial under its legal name.",
            security_id="eastfield-common",
            holding_name="Eastfield Bank Corp",
            citations=fund_citation,
        ),
    ]
    path = root / "overrides.toml"
    _write_toml(
        path, "Synthetic review.", {"schema_version": 1, "overrides": overrides}
    )
    options = build_options(directory)
    lagging = next(
        f
        for f in build(repo, **options).report.findings
        if f.finding_id == "difference:roster-2024-11-08"
    )
    overrides.append(
        _override(
            "ack-lagging-revision",
            "acknowledge",
            "The revision was saved on the change date, before editors updated it;"
            " the next revision agrees.",
            finding_id=lagging.finding_id,
            finding_digest=lagging.digest,
            citations=[
                {
                    "source_id": "synthetic-roster",
                    "url": "https://roster.example/index?rev=1003",
                }
            ],
        )
    )
    _write_toml(
        path, "Synthetic review.", {"schema_version": 1, "overrides": overrides}
    )
    frozen = freeze(build(repo, **options), root / "manifests", now=FROZEN_AT)
    return frozen.path
