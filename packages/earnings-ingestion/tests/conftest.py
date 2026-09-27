"""Shared test data. Plan 5: a small completed capture, its layout payload, and
builders for synthetic layout metadata. Plan 6: the synthetic cohort, and for
pdftext-1 a PDF builder and the cohort with a PDF notice (Task 16b). Plan 7: every
test's client locks live in a fresh directory, never in the user's cache."""

import copy
import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.browser.metadata import METADATA_VERSION, parse_metadata
from earnings_ingestion.browser.policy import ISOLATED_1
from earnings_ingestion.browser.records import (
    CaptureStatus,
    RenderedCapture,
    layout_hash,
)
from earnings_ingestion.browser.renderer import (
    CaptureEnvironment,
    cache_key,
    capture_id,
)
from earnings_ingestion.cohort.acquire import cite, register_saved
from earnings_ingestion.cohort.register import load_registers
from earnings_ingestion.cohort.synthetic import (
    FIXTURE_DIR,
    build_options,
    write_synthetic_cohort,
)
from earnings_ingestion.fetch.client import LOCK_DIR_VARIABLE
from earnings_ingestion.fetch.store import ArtifactStore

ENVIRONMENT = CaptureEnvironment(
    browser_engine="Chrome for Testing",
    browser_version="154.0.8037.57",
    driver_version="154.0.8037.57",
    selenium_version="4.49.0",
    os_name="Darwin",
    os_version="26.6.2",
    architecture="arm64",
)
PAYLOAD = {
    "blocks": [
        {
            "tag": "p",
            "display": "block",
            "heading_level": None,
            "list_item": False,
            "list_depth": 0,
            "table": None,
            "row": None,
            "cell": None,
            "x": 8,
            "y": 16,
            "width": 1264,
            "height": 18,
            "runs": [
                {
                    "text": "Revenue rose.",
                    "br": False,
                    "visible": True,
                    "bold": False,
                    "underline": False,
                    "superscript": False,
                    "symbol_font": False,
                    "font_size": 16,
                }
            ],
        }
    ],
    "tables": [],
}


@pytest.fixture(autouse=True)
def machine_locks(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The machine's lock directory, for this test only: a client opened by a test
    never takes, or waits on, the lock a live run holds (plan 7, P7-5)."""
    monkeypatch.setenv(LOCK_DIR_VARIABLE, str(tmp_path_factory.mktemp("locks")))


def build_capture(**changes: object) -> RenderedCapture:
    layout = changes.pop("layout", parse_metadata(PAYLOAD))
    text = changes.pop("rendered_text", "Revenue rose.")
    raw = b"<p>Revenue rose.</p>"
    key = cache_key(sha256_hex(raw), ISOLATED_1, ENVIRONMENT)
    fields = {
        "capture_id": capture_id("release", ISOLATED_1, key),
        "cache_key": key,
        "source_document_id": "release",
        "raw_sha256": sha256_hex(raw),
        "capture_policy": "isolated",
        "capture_policy_version": "1",
        "metadata_version": METADATA_VERSION,
        "browser_engine": "Chrome for Testing",
        "browser_version": "154.0.8037.57",
        "driver_version": "154.0.8037.57",
        "selenium_version": "4.49.0",
        "os_name": "Darwin",
        "os_version": "26.6.2",
        "architecture": "arm64",
        "viewport_width": 1280,
        "viewport_height": 1024,
        "device_scale_factor": 1,
        "locale": "en-US",
        "timezone": "UTC",
        "font_set": "Darwin 26.6.2 system fonts",
        "document_charset": "UTF-8",
        "script_policy": "disabled",
        "network_policy": "blocked",
        "image_policy": "blocked",
        "missing_resource_policy": "recorded",
        "rendered_text": text,
        "rendered_text_sha256": sha256_hex(text.encode("utf-8")),
        "layout": layout,
        "layout_sha256": layout_hash(layout),
        "screenshots": (),
        "blocked_requests": (),
        "captured_at": datetime(2026, 9, 26, 12, 0, tzinfo=UTC),
        "duration_seconds": 0.8,
        "status": CaptureStatus.COMPLETED,
        "reason": None,
        "detail": "",
    }
    fields.update(changes)
    return RenderedCapture(**fields)


@pytest.fixture
def make_capture() -> Callable[..., RenderedCapture]:
    """A factory: a completed capture of one paragraph, with any field replaced."""
    return build_capture


@pytest.fixture
def payload() -> dict:
    """The layout-metadata script's result for that paragraph, safe to change."""
    return copy.deepcopy(PAYLOAD)


class LayoutParts:
    """Builders for the layout-metadata script's output: runs, blocks, and tables."""

    @staticmethod
    def run(text: str, **style: object) -> dict:
        base = {
            "text": text,
            "br": False,
            "visible": True,
            "bold": False,
            "underline": False,
            "superscript": False,
            "symbol_font": False,
            "font_size": 16,
        }
        return {**base, **style}

    @staticmethod
    def br() -> dict:
        return LayoutParts.run("\n", br=True)

    @staticmethod
    def block(
        *runs: dict,
        tag: str = "p",
        cell: tuple[int, int, int] | None = None,
        **context: object,
    ) -> dict:
        base = {
            "tag": tag,
            "display": "block",
            "heading_level": None,
            "list_item": False,
            "list_depth": 0,
            "table": None if cell is None else cell[0],
            "row": None if cell is None else cell[1],
            "cell": None if cell is None else cell[2],
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 10,
            "runs": list(runs),
        }
        return {**base, **context}

    @staticmethod
    def table(
        *rows: list[int],
        parent: tuple[int, int, int] | None = None,
        head: int = 0,
        th: bool = False,
    ) -> dict:
        """Rows as colspans, one per rendered cell; the first ``head`` rows in thead."""
        return {
            "parent_table": None if parent is None else parent[0],
            "parent_row": None if parent is None else parent[1],
            "parent_cell": None if parent is None else parent[2],
            "rows": [
                {
                    "head": index < head,
                    "cells": [
                        {"header": th, "colspan": span, "rowspan": 1} for span in row
                    ],
                }
                for index, row in enumerate(rows)
            ],
        }

    @staticmethod
    def cells(rows: list[list[str]], table_index: int = 0) -> list[dict]:
        """One ``td`` block per non-empty cell text, in row-major order."""
        return [
            LayoutParts.block(LayoutParts.run(text), tag="td", cell=(table_index, r, c))
            for r, row in enumerate(rows)
            for c, text in enumerate(row)
            if text
        ]


@pytest.fixture
def parts() -> type[LayoutParts]:
    return LayoutParts


@pytest.fixture(scope="session")
def synthetic_cohort(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A repository holding the synthetic cohort, generated once; never change it."""
    repo = tmp_path_factory.mktemp("synthetic-cohort")
    write_synthetic_cohort(repo)
    return repo


@pytest.fixture
def cohort_repo(synthetic_cohort: Path, tmp_path: Path) -> Path:
    """A private copy of the synthetic cohort's repository, safe to change."""
    shutil.copytree(synthetic_cohort, tmp_path, dirs_exist_ok=True)
    return tmp_path


def _pdf_string(text: str) -> str:
    """``text`` as an ASCII PDF literal string: a WinAnsi character as an octal
    escape, and U+0301 as code 0x81, which the font's /Differences names /acutecomb."""
    out = []
    for char in text:
        if char in "\\()":
            out.append("\\" + char)
        elif " " <= char <= "~":
            out.append(char)
        else:
            code = 0x81 if char == chr(0x301) else char.encode("cp1252")[0]
            out.append(f"\\{code:03o}")
    return "".join(out)


def build_pdf(*pages: list[tuple[int, int, str]]) -> bytes:
    """A PDF with one page per argument, each a list of (x, y, text) runs in 12-point
    Helvetica: ASCII bytes, no compressed stream, and a computed cross-reference
    table. Runs on one baseline extract as one line, joined by single spaces."""
    count = len(pages)
    kids = " ".join(f"{3 + 2 * index} 0 R" for index in range(count))
    font = 3 + 2 * count
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {count} >>",
    ]
    for index, runs in enumerate(pages):
        content = "\n".join(
            f"BT /F1 12 Tf {x} {y} Td ({_pdf_string(text)}) Tj ET"
            for x, y, text in runs
        )
        objects.append(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources"
            f" << /Font << /F1 {font} 0 R >> >> /Contents {4 + 2 * index} 0 R >>"
        )
        objects.append(f"<< /Length {len(content)} >>\nstream\n{content}\nendstream")
    objects.append(
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding << /Type"
        " /Encoding /BaseEncoding /WinAnsiEncoding /Differences [129 /acutecomb] >> >>"
    )
    pdf = "%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{number} 0 obj\n{body}\nendobj\n"
    xref = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    pdf += "".join(f"{offset:010d} 00000 n \n" for offset in offsets)
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
    pdf += f"startxref\n{xref}\n%%EOF\n"
    return pdf.encode("ascii")


@pytest.fixture
def make_pdf() -> Callable[..., bytes]:
    """A factory: a small PDF built from text runs, one argument per page."""
    return build_pdf


PDF_NOTICE = [
    (72, 720, "Synthetic Index Services announces a change"),
    (72, 690, "Corvid Systems will replace Borealis Air in the Synthetic Industrial"),
    (72, 675, "Average prior to"),
    (72, 660, "the open of trading on Friday, November 8, 2024."),
    (72, 630, "Company"),
    (250, 630, "Ticker"),
    (330, 630, "Action"),
    (72, 612, "Corvid Systems"),
    (250, 612, "CRVD"),
    (330, 612, "Added"),
    (72, 594, "Borealis Air"),
    (250, 594, "BORA"),
    (330, 594, "Removed"),
]
PDF_NOTICE_URL = "https://index.example/notices/index-2024-11-01"


@pytest.fixture
def pdf_cohort(cohort_repo: Path) -> Path:
    """The private copy, its official notice index-2024-11-01 replaced by an invented
    PDF that states the same facts. The PDF is registered as Task 17 registers a
    saved notice, and its rows and effective date are cited through pdftext-1."""
    store = ArtifactStore(cohort_repo / FIXTURE_DIR / "raw", cohort_repo)
    options = build_options()
    registers = load_registers(
        cohort_repo, options["register"], options["sec_register"]
    )
    ref = register_saved(
        store,
        registers,
        "synthetic-index",
        build_pdf(PDF_NOTICE),
        url=PDF_NOTICE_URL,
        media_type="application/pdf",
        saved_at=datetime(2026, 9, 28, 12, 0, tzinfo=UTC),
    )

    def locate(needle: str, line: bool = False):
        sha = ref.content_sha256
        return cite(store, registers, "synthetic-index", sha, find=needle, line=line)[0]

    when = locate("prior to\nthe open of trading on Friday, November 8, 2024")
    added = locate("Corvid Systems CRVD", line=True)
    removed = locate("Borealis Air BORA", line=True)
    block = (
        '[[changes]]\nevidence_id = "index-2024-11-01"\nsource_id = "synthetic-index"\n'
        f'url = "{PDF_NOTICE_URL}"\nartifact_sha256 = "{ref.content_sha256}"\n'
        f'canonical_sha256 = "{when.canonical_sha256}"\nannounced_on = 2024-11-01\n'
        'published_on = 2024-11-01\npublished_at = "2024-11-01T21:15:00Z"\n'
        'effective_on = 2024-11-08\ntiming = "before_open"\n'
        f"date_span = [{when.start}, {when.end}]\n"
        f'date_cited_sha256 = "{when.cited_sha256}"\n\n'
        '[[changes.entries]]\naction = "added"\nsecurity_id = "corvid-common"\n'
        'name = "Corvid Systems"\nticker = "CRVD"\n'
        f"span = [{added.start}, {added.end}]\n"
        f'cited_sha256 = "{added.cited_sha256}"\n\n'
        '[[changes.entries]]\naction = "removed"\nsecurity_id = "borealis-common"\n'
        'name = "Borealis Air"\nticker = "BORA"\n'
        f"span = [{removed.start}, {removed.end}]\n"
        f'cited_sha256 = "{removed.cited_sha256}"\n\n'
    )
    path = cohort_repo / FIXTURE_DIR / "evidence.toml"
    evidence = path.read_text(encoding="utf-8")
    start = evidence.index('[[changes]]\nevidence_id = "index-2024-11-01"\n')
    end = evidence.index("[[changes]]\n", start + 1)
    path.write_text(evidence[:start] + block + evidence[end:], encoding="utf-8")
    return cohort_repo
