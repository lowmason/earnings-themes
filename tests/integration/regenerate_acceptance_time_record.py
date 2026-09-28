"""Regenerate docs/verification/edgar-acceptance-time.md from saved pages (EV10).

    uv run --locked --all-packages python tests/integration/regenerate_acceptance_time_record.py --repo PATH

It cross-checks SEC's submissions ``acceptanceDateTime`` against the index page's
"Accepted" value for every saved row that has both, and rewrites the record. It sends
no request. ``--repo`` is the checkout whose gitignored ``data/raw/`` holds the pages,
by default this one; the record is written in this checkout.

- Leg 1 reads Stage 1's pages, under ``data/raw/discovery/``.
- Leg 2 reads Stage 5's store, under ``data/raw/events/``, once its discovery run has
  saved submissions files and index pages there. It reads no companyfacts file or
  primary document.

pytest never collects this file.
"""

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from earnings_ingestion.events.acceptance import (
    Convention,
    FileSurvey,
    accepted_instant,
    survey,
)
from earnings_ingestion.fetch.records import Retrieval
from earnings_ingestion.sec.data import read_submissions, read_submissions_page
from earnings_ingestion.sec.filing_index import read_filing_index
from earnings_ingestion.sec.urls import submissions_page_url

REPO = Path(__file__).resolve().parents[2]
RECORD = Path("docs/verification/edgar-acceptance-time.md")
GENERATOR = "tests/integration/regenerate_acceptance_time_record.py"
STAGE_1 = Path("data/raw/discovery")
STAGE_5 = Path("data/raw/events/sec-edgar")
SUBMISSIONS = submissions_page_url("")
"""Where submissions files and older pages live: a companyfacts file's name looks
like a submissions file's, so the name alone cannot tell them apart."""
ARCHIVES = "https://www.sec.gov/Archives/"
MAIN_FILE = re.compile(r"CIK\d{10}\.json")
OLDER_PAGE = re.compile(r"CIK\d{10}-submissions-\d{3}\.json")
LABELS = {Convention.UTC: "true UTC", Convention.EASTERN_DIGITS: "Eastern digits and Z"}


@dataclass(frozen=True)
class Saved:
    name: str
    body: bytes
    retrieved: date


@dataclass(frozen=True)
class Leg:
    title: str
    source: str
    surveys: tuple[tuple[FileSurvey, bool, date | None], ...]
    """Each file's survey, whether it is an older page, and a main file's latest
    filing date."""
    index_pages: int
    retrieved: tuple[date, date]


def stage_1(repo: Path) -> tuple[list[Saved], list[Saved]]:
    """Stage 1's submissions files and index pages, each with its meta record."""

    def saved(path: Path, name: str) -> Saved:
        meta = json.loads(Path(f"{path}.meta.json").read_text(encoding="utf-8"))
        return Saved(
            name, path.read_bytes(), date.fromisoformat(meta["retrieved_at"][:10])
        )

    root = repo / STAGE_1
    files = [
        saved(path, path.name)
        for path in sorted((root / "submissions").glob("*.json"))
        if not path.name.endswith(".meta.json")
    ]
    pages = [
        saved(path, path.parent.name)
        for path in sorted((root / "filings").glob("*/index.htm"))
    ]
    return files, pages


def stage_5(repo: Path) -> tuple[list[Saved], list[Saved]]:
    """The newest retrieval of each submissions file, older page, and index page in
    Stage 5's store."""
    root = repo / STAGE_5
    newest: dict[str, Retrieval] = {}
    for path in sorted(root.glob("retrievals/*/*.json")):
        record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
        known = newest.get(record.request_url)
        if known is None or (record.retrieved_at, record.sha256) > (
            known.retrieved_at,
            known.sha256,
        ):
            newest[record.request_url] = record
    files: list[Saved] = []
    pages: list[Saved] = []
    for url, record in sorted(newest.items()):
        name = url.rsplit("/", 1)[-1]
        if url.startswith(SUBMISSIONS) and (
            MAIN_FILE.fullmatch(name) or OLDER_PAGE.fullmatch(name)
        ):
            kind = files
        elif url.startswith(ARCHIVES) and name.endswith("-index.htm"):
            kind = pages
        else:
            continue
        (body_path,) = root.glob(f"{record.sha256}.*")
        kind.append(Saved(name, body_path.read_bytes(), record.retrieved_at.date()))
    return files, pages


def leg(title: str, source: str, files: list[Saved], pages: list[Saved]) -> Leg:
    instants = {}
    for page in pages:
        index = read_filing_index(page.body)
        instants[index.accession] = accepted_instant(index.accepted)
    surveys = []
    for saved in files:
        older = OLDER_PAGE.fullmatch(saved.name) is not None
        filings = (
            read_submissions_page(saved.body)
            if older
            else read_submissions(saved.body).filings
        )
        latest = None if older else max((f.filing_date for f in filings), default=None)
        surveys.append((survey(saved.name, filings, instants), older, latest))
    dates = [saved.retrieved for saved in files + pages]
    return Leg(title, source, tuple(surveys), len(pages), (min(dates), max(dates)))


def span(dates: list[date]) -> str:
    return f"{min(dates)} to {max(dates)}" if dates else "none"


def rows(leg: Leg) -> list[tuple[str, str]]:
    checked = [s for s, _, _ in leg.surveys if s.checks]
    checks = [check for s in checked for check in s.checks]
    lines = [
        ("Retrieved", span(list(leg.retrieved))),
        ("Submissions files read", str(sum(not older for _, older, _ in leg.surveys))),
        ("Older pages read", str(sum(older for _, older, _ in leg.surveys))),
        ("Index pages read", str(leg.index_pages)),
        ("Files with a cross-checked row", str(len(checked))),
        ("Rows cross-checked", str(len(checks))),
    ]
    for convention, label in LABELS.items():
        count = sum(check.convention is convention for check in checks)
        lines.append((f"Rows in {label}", str(count)))
    lines += [
        ("Rows in neither", str(sum(check.convention is None for check in checks))),
        ("Files in both conventions", str(sum(s.mixed for s in checked))),
    ]
    for convention, label in LABELS.items():
        main = [
            latest
            for s, older, latest in leg.surveys
            if not older and s.convention is convention and latest is not None
        ]
        lines.append(
            (
                f"Submissions files in {label}",
                f"{len(main)}, latest filing {span(main)}",
            )
        )
    for convention, label in LABELS.items():
        count = sum(older and s.convention is convention for s, older, _ in leg.surveys)
        lines.append((f"Older pages in {label}", str(count)))
    return lines


def failures(leg: Leg) -> list[str]:
    found = []
    for s, _, _ in leg.surveys:
        found += [
            f"- {leg.title}: `{s.name}` row `{c.accession}` follows neither convention."
            for c in s.mismatches
        ]
        if s.mixed:
            found.append(f"- {leg.title}: `{s.name}` follows both conventions.")
    return found


def render(legs: list[Leg]) -> str:
    table = [
        "| | " + " | ".join(leg.title for leg in legs) + " |",
        "| --- |" + " --- |" * len(legs),
    ]
    columns = [rows(leg) for leg in legs]
    for position, (label, _) in enumerate(columns[0]):
        values = " | ".join(column[position][1] for column in columns)
        table.append(f"| {label} | {values} |")
    found = [line for leg in legs for line in failures(leg)]
    verdict = (
        [
            "Every cross-checked row follows one of the two conventions, and no file",
            "follows both. So Stage 5 reads the index page's Accepted value as the",
            "acceptance time, and the submissions value only cross-checks it.",
        ]
        if not found
        else ["These rows or files break the rule:", "", *found]
    )
    pending = (
        []
        if len(legs) == 2
        else [
            "",
            "Leg 2 reads Stage 5's own pages, which cover the window's filings. It is",
            "added when Stage 5's discovery run has saved them.",
        ]
    )
    sources = [f"- **{leg.title}** reads {leg.source}." for leg in legs]
    return "\n".join(
        [
            "# EDGAR acceptance time",
            "",
            f"<!-- Generated by {GENERATOR} from saved pages; do not edit. -->",
            "",
            "Stage 5 takes a filing's acceptance time from its EDGAR index page's",
            '"Accepted" value, read as America/New_York wall time (EV10 of',
            "`specs/completed/event-discovery-eligibility-and-acquisition.md`). SEC's submissions",
            "`acceptanceDateTime` only cross-checks it. SEC writes that value in one of",
            "two conventions: the true UTC instant, or the instant's Eastern wall-clock",
            "digits followed by `Z`.",
            "",
            "This record recomputes the finding from saved pages, and sends no request.",
            "Each leg reads every saved submissions file and older page, and",
            "cross-checks each row whose filing's index page is also saved. A file's",
            "convention is the one its cross-checked rows share.",
            "",
            *sources,
            *pending,
            "",
            *table,
            "",
            *verdict,
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=REPO)
    repo = parser.parse_args().repo.resolve()
    first = stage_1(repo)
    if not first[0] or not first[1]:
        parser.error(f"no Stage 1 pages under {repo / STAGE_1}")
    legs = [leg("Leg 1", "Stage 1's pages, under `data/raw/discovery/`", *first)]
    second = stage_5(repo)
    if second[0] and second[1]:
        legs.append(leg("Leg 2", "Stage 5's pages, under `data/raw/events/`", *second))
    (REPO / RECORD).write_text(render(legs), encoding="utf-8")
    print(f"wrote {RECORD} with {len(legs)} leg(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
