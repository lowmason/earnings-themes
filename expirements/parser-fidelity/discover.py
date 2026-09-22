# /// script
# requires-python = ">=3.14"
# dependencies = ["httpx==0.28.1", "lxml==6.1.3"]
# ///
"""Discover Item 2.02 press-release exhibits for the Stage 1 fixture shortlist.

Sources: EDGAR's quarterly filing index (``master.idx``) is the sampling frame across
years and filer agents; the submissions data supplies each filing's Item list; the
filing index page supplies the exhibit type and description. Every response is saved
under ``data/raw/discovery/`` and reused on rerun, so no exhibit is fetched twice.

Usage (live, opt-in; ``EDGAR_IDENTITY`` must be set outside Git):
    uv run --locked --script expirements/parser-fidelity/discover.py run --live
    uv run --locked --script expirements/parser-fidelity/discover.py shortlist
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import lxml.html
from pf_classes import run_class_tests
from pf_fetch import (
    DEFAULT_MAX_REQUESTS,
    EdgarFetcher,
    LiveLock,
    LivePolicyStop,
    Throttle,
    UnexpectedResponse,
    read_meta,
    require_identity,
)
from pf_paths import DISCOVERY, LIVE_LOCK, MAX_FIXTURE_BYTES, fixture_id

FIRST_SAMPLED_YEAR = (
    2005  # Item 2.02 dates from August 2004; 2005 is its first full year
)
DEFAULT_YEARS = (2005, 2008, 2011, 2014, 2017, 2020, 2023, 2025)
DEFAULT_PER_YEAR = 8
DEFAULT_SEED = 20260922
CANDIDATES_FILE = DISCOVERY / "candidates.jsonl"
SHORTLIST_FILE = DISCOVERY / "shortlist.md"
PRESS_RELEASE_WORDS = re.compile(
    r"press release|news release|earnings|results", re.IGNORECASE
)
HTML_SUFFIXES = (".htm", ".html")
CLASSES = ("narrative_only", "malformed_layout", "table_heavy", "clean_html")
# Image-only exhibits need OCR (R4.3) and are excluded; a release with native text has
# thousands of visible characters. This only sorts candidates; it is not a quality threshold.
MIN_NATIVE_TEXT_CHARS = 500


@dataclass(frozen=True)
class IndexRow:
    cik: str  # zero-padded, 10 characters (A §264)
    company: str
    form: str
    filed: str
    accession: str

    @property
    def agent(self) -> str:
        """The accession prefix: the CIK of whoever submitted the filing."""
        return self.accession[:10]


@dataclass(frozen=True)
class SubmissionFiling:
    accession: str
    form: str
    filing_date: str
    items: str


@dataclass(frozen=True)
class IndexDocument:
    seq: str
    description: str
    filename: str
    doc_type: str


def master_index_url(year: int, quarter: int) -> str:
    return (
        f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/master.idx"
    )


def submissions_url(cik: str) -> str:
    return f"https://data.sec.gov/submissions/CIK{cik}.json"


def submissions_page_url(name: str) -> str:
    return f"https://data.sec.gov/submissions/{name}"


def filing_folder(cik: str, accession: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}"


def filing_index_url(cik: str, accession: str) -> str:
    return f"{filing_folder(cik, accession)}/{accession}-index.htm"


def quarter_of(day: str) -> tuple[int, int]:
    parsed = date.fromisoformat(day)
    return parsed.year, (parsed.month - 1) // 3 + 1


def quarter_bounds(year: int, quarter: int) -> tuple[str, str]:
    first = date(year, 3 * quarter - 2, 1)
    after = date(year + 1, 1, 1) if quarter == 4 else date(year, 3 * quarter + 1, 1)
    return first.isoformat(), (after - timedelta(days=1)).isoformat()


def parse_master_index(text: str) -> list[IndexRow]:
    """Rows of a ``master.idx`` file: ``CIK|Company Name|Form Type|Date Filed|Filename``."""
    rows = []
    for line in text.splitlines():
        parts = line.split("|")
        if len(parts) != 5 or not parts[0].strip().isdigit():
            continue
        cik, company, form, filed, filename = (part.strip() for part in parts)
        accession = filename.rsplit("/", 1)[-1].removesuffix(".txt")
        rows.append(IndexRow(cik.zfill(10), company, form, filed, accession))
    return rows


def sample_ciks(
    rows: list[IndexRow], *, count: int, rng: random.Random
) -> list[IndexRow]:
    """One 8-K per CIK, spread across filer agents: shuffle agents, then take round-robin."""
    by_agent: dict[str, list[IndexRow]] = defaultdict(list)
    for row in sorted(rows, key=lambda r: (r.agent, r.cik, r.accession)):
        if row.form == "8-K":
            by_agent[row.agent].append(row)
    agents = sorted(by_agent)
    rng.shuffle(agents)
    for agent in agents:
        rng.shuffle(by_agent[agent])
    picked: list[IndexRow] = []
    seen: set[str] = set()
    while len(picked) < count and any(by_agent[agent] for agent in agents):
        for agent in agents:
            while by_agent[agent]:
                row = by_agent[agent].pop()
                if row.cik not in seen:
                    seen.add(row.cik)
                    picked.append(row)
                    break
            if len(picked) == count:
                break
    return picked


def parse_submission_filings(block: dict) -> list[SubmissionFiling]:
    """Rows of a submissions ``filings.recent`` block or an older submissions page."""
    accessions = block["accessionNumber"]
    items = block.get("items") or [""] * len(accessions)
    return [
        SubmissionFiling(accession, form, filing_date, item or "")
        for accession, form, filing_date, item in zip(
            accessions, block["form"], block["filingDate"], items, strict=True
        )
    ]


def older_pages_covering(document: dict, year: int, quarter: int) -> list[str]:
    start, end = quarter_bounds(year, quarter)
    return [
        page["name"]
        for page in document.get("filings", {}).get("files", [])
        if page["filingFrom"] <= end and page["filingTo"] >= start
    ]


def pick_earnings_filing(
    filings: list[SubmissionFiling], year: int, quarter: int
) -> SubmissionFiling | None:
    """The quarter's earliest 8-K whose Items include 2.02."""
    matches = [
        filing
        for filing in filings
        if filing.form == "8-K"
        and "2.02" in [item.strip() for item in filing.items.split(",")]
        and quarter_of(filing.filing_date) == (year, quarter)
    ]
    return min(matches, key=lambda f: (f.filing_date, f.accession), default=None)


def parse_filing_index(html: str) -> list[IndexDocument]:
    """The 'Document Format Files' table of a filing index page."""
    root = lxml.html.document_fromstring(
        html.encode("utf-8"), parser=lxml.html.HTMLParser(encoding="utf-8")
    )
    tables = [
        t
        for t in root.iter("table")
        if "document format files" in (t.get("summary") or "").lower()
    ]
    if not tables:
        tables = [
            t
            for t in root.iter("table")
            if "tablefile" in (t.get("class") or "").lower()
        ]
    documents = []
    for row in tables[0].iter("tr") if tables else []:
        cells = row.findall("td")
        if len(cells) < 4:
            continue
        link = cells[2].find(".//a")
        href = link.get("href", "") if link is not None else ""
        documents.append(
            IndexDocument(
                seq=cells[0].text_content().strip(),
                description=cells[1].text_content().strip(),
                filename=_filename_from_href(href)
                or cells[2].text_content().split()[0],
                doc_type=cells[3].text_content().strip(),
            )
        )
    return documents


def _filename_from_href(href: str) -> str:
    parsed = urlparse(href)
    target = parse_qs(parsed.query).get("doc", [parsed.path])[0]
    return target.rsplit("/", 1)[-1]


def pick_press_release(
    documents: list[IndexDocument],
) -> tuple[IndexDocument | None, str]:
    """Choose the press-release exhibit by exhibit type and description."""
    exhibits = [d for d in documents if d.doc_type.upper().startswith("EX-99")]
    if not exhibits:
        return None, "no EX-99 exhibit"
    described = [d for d in exhibits if PRESS_RELEASE_WORDS.search(d.description)]
    chosen = (
        described[0] if described else (exhibits[0] if len(exhibits) == 1 else None)
    )
    if chosen is None:
        return None, "several EX-99 exhibits and none described as a release"
    if not chosen.filename.lower().endswith(HTML_SUFFIXES):
        return None, f"exhibit is not HTML ({chosen.filename})"
    return chosen, "ok"


@dataclass
class Candidate:
    fixture_id: str
    cik: str
    issuer_name: str
    accession: str
    agent: str
    form: str
    items: str
    filing_date: str
    exhibit_type: str
    exhibit_filename: str
    exhibit_description: str
    url: str
    year: int
    quarter: int
    within_size_cap: bool
    class_tests: dict


class Discovery:
    def __init__(self, fetcher: EdgarFetcher, root: Path = DISCOVERY) -> None:
        self.fetcher = fetcher
        self.root = root
        self.candidates_file = root / "candidates.jsonl"

    def _cached(self, url: str, dest: Path, expected: set[str]) -> bytes:
        if not dest.exists():
            self.fetcher.fetch_and_save(url, dest, expected)
        return dest.read_bytes()

    def known_accessions(self) -> set[str]:
        if not self.candidates_file.exists():
            return set()
        lines = self.candidates_file.read_text(encoding="utf-8").splitlines()
        return {json.loads(line)["accession"] for line in lines if line.strip()}

    def run_year(
        self, year: int, quarter: int, per_year: int, rng: random.Random
    ) -> list[str]:
        """Collect up to ``per_year`` candidates from one quarter; returns skip reasons."""
        index_text = self._cached(
            master_index_url(year, quarter),
            self.root / "index" / f"{year}-QTR{quarter}-master.idx",
            {"text/plain", "application/octet-stream"},
        ).decode("latin-1")
        rows = parse_master_index(index_text)
        known = self.known_accessions()
        skips: list[str] = []
        found = 0
        for row in sample_ciks(rows, count=per_year * 4, rng=rng):
            if found == per_year:
                break
            try:
                reason = self._try_issuer(row, year, quarter, known)
            except UnexpectedResponse as exc:
                reason = f"skipped: {exc}"
            if reason in ("ok", "already recorded"):
                found += 1
            else:
                skips.append(f"{row.cik} {year}Q{quarter}: {reason}")
        return skips

    def _try_issuer(
        self, row: IndexRow, year: int, quarter: int, known: set[str]
    ) -> str:
        sub_dir = self.root / "submissions"
        document = json.loads(
            self._cached(
                submissions_url(row.cik),
                sub_dir / f"CIK{row.cik}.json",
                {"application/json"},
            )
        )
        filings = parse_submission_filings(document["filings"]["recent"])
        filing = pick_earnings_filing(filings, year, quarter)
        if filing is None:
            for name in older_pages_covering(document, year, quarter):
                page = json.loads(
                    self._cached(
                        submissions_page_url(name), sub_dir / name, {"application/json"}
                    )
                )
                filing = pick_earnings_filing(
                    parse_submission_filings(page), year, quarter
                )
                if filing is not None:
                    break
        if filing is None:
            return "no 8-K reporting Item 2.02 in the quarter"
        if filing.accession in known:
            return "already recorded"
        index_dest = self.root / "filings" / filing.accession / "index.htm"
        index_html = self._cached(
            filing_index_url(row.cik, filing.accession), index_dest, {"text/html"}
        )
        exhibit, reason = pick_press_release(
            parse_filing_index(index_html.decode("utf-8", errors="replace"))
        )
        if exhibit is None:
            return reason
        try:
            fid = fixture_id(filing.accession, exhibit.doc_type)
        except ValueError:
            return f"exhibit type {exhibit.doc_type!r} gives no valid fixture id"
        dest = self.root / fid / "source.html"
        url = f"{filing_folder(row.cik, filing.accession)}/{exhibit.filename}"
        raw = self._cached(url, dest, {"text/html"})
        candidate = Candidate(
            fixture_id=fid,
            cik=row.cik,
            issuer_name=row.company,
            accession=filing.accession,
            agent=filing.accession[:10],
            form=filing.form,
            items=filing.items,
            filing_date=filing.filing_date,
            exhibit_type=exhibit.doc_type,
            exhibit_filename=exhibit.filename,
            exhibit_description=exhibit.description,
            url=read_meta(dest).url,
            year=year,
            quarter=quarter,
            within_size_cap=len(raw) <= MAX_FIXTURE_BYTES,
            class_tests=run_class_tests(raw).as_dict(),
        )
        with self.candidates_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(candidate), sort_keys=True) + "\n")
        known.add(filing.accession)
        return "ok"


def load_candidates(path: Path = CANDIDATES_FILE) -> list[Candidate]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [Candidate(**json.loads(line)) for line in lines if line.strip()]


def eligible_for_shortlist(candidate: Candidate) -> bool:
    """Within the 1 MiB cap and carrying native text (not an image-only exhibit)."""
    return (
        candidate.within_size_cap
        and candidate.class_tests["visible_chars"] >= MIN_NATIVE_TEXT_CHARS
    )


def suggest(
    candidates: list[Candidate], per_class: int = 3
) -> dict[str, list[Candidate]]:
    """About three per class: mixed agents and years, at most two per issuer, scarcest class first.

    Table-heavy and narrative-only suggestions prefer exhibits that trip no malformed test.
    """
    eligible = [c for c in candidates if eligible_for_shortlist(c)]
    per_issuer: Counter[str] = Counter()
    used: set[str] = set()
    agents: Counter[str] = Counter()
    years: Counter[int] = Counter()
    chosen: dict[str, list[Candidate]] = {}
    for cls in CLASSES:
        pool = [c for c in eligible if c.class_tests[cls] and c.fixture_id not in used]
        picks: list[Candidate] = []
        while len(picks) < per_class:
            options = [c for c in pool if c not in picks and per_issuer[c.cik] < 2]
            if not options:
                break
            prefer_clean = cls in ("table_heavy", "narrative_only")
            best = min(
                options,
                key=lambda c: (
                    prefer_clean and c.class_tests["malformed_layout"],
                    agents[c.agent],
                    years[c.year],
                    c.fixture_id,
                ),
            )
            picks.append(best)
            used.add(best.fixture_id)
            per_issuer[best.cik] += 1
            agents[best.agent] += 1
            years[best.year] += 1
        chosen[cls] = picks
    return chosen


def render_shortlist(candidates: list[Candidate]) -> str:
    suggested = suggest(candidates)
    lines = [
        "# Stage 1 fixture shortlist",
        "",
        (
            f"{len(candidates)} candidates discovered; "
            f"{sum(not c.within_size_cap for c in candidates)} exceed the 1 MiB cap and "
            f"{sum(c.within_size_cap and not eligible_for_shortlist(c) for c in candidates)} "
            f"have under {MIN_NATIVE_TEXT_CHARS} characters of native text; both are excluded."
        ),
        "",
        "Approve eight fixtures (two per class) and two or three development releases in",
        "`expirements/parser-fidelity/approval.toml`. Suggested picks are marked **S**.",
        "",
    ]
    for cls in CLASSES:
        pool = sorted(
            (c for c in candidates if c.class_tests[cls] and eligible_for_shortlist(c)),
            key=lambda c: c.fixture_id,
        )
        lines += [f"## {cls} ({len(pool)} eligible)", ""]
        lines.append(
            "| | fixture_id | issuer | year | agent | exhibit | data share | malformed | stage 4 |"
        )
        lines.append("|---|---|---|---|---|---|---|---|---|")
        picks = {c.fixture_id for c in suggested[cls]}
        for c in pool:
            flags = []
            if c.class_tests["narrative_only"]:
                flags.append("narrative-only")
            if c.exhibit_type.upper() != "EX-99.1":
                flags.append("alt numbering")
            lines.append(
                f"| {'**S**' if c.fixture_id in picks else ''} | `{c.fixture_id}` | {c.issuer_name} | {c.year} "
                f"| {c.agent} | {c.exhibit_type} | {c.class_tests['data_table_share']:.2f} "
                f"| {'yes' if c.class_tests['malformed_layout'] else 'no'} | {', '.join(flags)} |"
            )
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="live discovery (opt-in)")
    run.add_argument(
        "--live",
        action="store_true",
        help="required: confirms a live, rate-limited run",
    )
    run.add_argument("--years", type=int, nargs="+", default=list(DEFAULT_YEARS))
    run.add_argument("--per-year", type=int, default=DEFAULT_PER_YEAR)
    run.add_argument("--seed", type=int, default=DEFAULT_SEED)
    run.add_argument("--max-requests", type=int, default=DEFAULT_MAX_REQUESTS)
    sub.add_parser(
        "shortlist", help="write data/raw/discovery/shortlist.md from saved candidates"
    )
    args = parser.parse_args(argv)

    if args.command == "shortlist":
        SHORTLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
        SHORTLIST_FILE.write_text(
            render_shortlist(load_candidates()) + "\n", encoding="utf-8"
        )
        print(f"wrote {SHORTLIST_FILE}")
        return 0

    if not args.live:
        parser.error("discovery makes live requests; pass --live to confirm")
    if min(args.years) < FIRST_SAMPLED_YEAR:
        parser.error(
            f"Item 2.02 dates from August 2004; sample {FIRST_SAMPLED_YEAR} or later"
        )
    identity = require_identity()
    throttle = Throttle(max_requests=args.max_requests)
    fetcher = EdgarFetcher(identity, throttle=throttle)
    rng = random.Random(args.seed)
    status = 0
    try:
        with LiveLock(LIVE_LOCK):
            discovery = Discovery(fetcher)
            for year in args.years:
                quarter = 1 + (args.seed + year) % 4
                for skip in discovery.run_year(year, quarter, args.per_year, rng):
                    print(skip)
    except LivePolicyStop as exc:
        print(f"STOPPED: {exc}", file=sys.stderr)
        status = 1
    finally:
        fetcher.close()
        print(f"requests made: {throttle.count}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
