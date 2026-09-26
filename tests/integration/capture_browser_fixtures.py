"""Capture the committed browser fixtures with the pinned browser (Stage 3, plan B).

    uv run --locked --all-packages --extra browser-capture python tests/integration/capture_browser_fixtures.py contract
    uv run --locked --all-packages --extra browser-capture python tests/integration/capture_browser_fixtures.py releases

``contract`` captures tests/fixtures/browser/contract-release.html, the two-parser
contract's source. ``releases`` captures the eight Stage 1 releases, and refuses to
run until layout-1's pre-registration is committed and intact: no fixture is captured
before the comparison is fixed (plan 5, PB-13).

Each capture goes through the capture store under data/runs/browser-capture/, which
reuses a stored capture with the same cache key and never overwrites one, and is then
written to tests/fixtures/browser/<name>.capture.json without screenshots. A capture
that is not completed or partial stops the run. pytest never collects this file.
"""

import subprocess
import sys
from pathlib import Path

from earnings_ingestion.browser import ISOLATED_1, CaptureStatus, CaptureStore
from earnings_ingestion.browser import capture_once as capture_stored
from earnings_ingestion.browser.install import installed
from earnings_ingestion.browser.selenium_capture import SeleniumRenderer
from earnings_ingestion.browser.serialize import to_capture_json

REPO = Path(__file__).resolve().parents[2]
BROWSER = REPO / "tests" / "fixtures" / "browser"
RELEASES = REPO / "tests" / "fixtures" / "releases"
STORE = REPO / "data" / "runs" / "browser-capture"
PREREGISTER = REPO / "expirements" / "parser-fidelity" / "preregister.py"
USABLE = {CaptureStatus.COMPLETED, CaptureStatus.PARTIAL}


def preregistration_intact() -> str | None:
    """``None`` when ``preregister.py verify`` passes, else what it reported."""
    if not PREREGISTER.is_file():
        return "layout-1 is not pre-registered: preregister.py does not exist yet"
    result = subprocess.run(
        [sys.executable, str(PREREGISTER), "verify"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return None
    return (result.stdout + result.stderr).strip() or "verification failed"


def capture_one(renderer: SeleniumRenderer, source: Path, name: str) -> bool:
    store = CaptureStore(STORE, REPO)
    capture = capture_stored(
        renderer, store, source.read_bytes(), ISOLATED_1, source_document_id=name
    )
    if capture.status not in USABLE:
        print(
            f"{name}: {capture.status.value}: {capture.reason.value}: {capture.detail}"
        )
        return False
    target = BROWSER / f"{name}.capture.json"
    target.write_text(to_capture_json(capture), encoding="utf-8", newline="\n")
    print(f"wrote {target.relative_to(REPO)} ({capture.status.value})")
    return True


def main(argv: list[str]) -> int:
    if argv not in (["contract"], ["releases"]):
        print(__doc__)
        return 2
    binaries = installed()
    if binaries is None:
        print(
            "the pinned browser is not installed: run earnings-pipeline browser setup"
        )
        return 1
    renderer = SeleniumRenderer(binaries)
    if argv == ["contract"]:
        source = BROWSER / "contract-release.html"
        return 0 if capture_one(renderer, source, "contract-release") else 1
    refused = preregistration_intact()
    if refused is not None:
        print(f"refused: {refused}")
        return 1
    sources = sorted(RELEASES.glob("*/source.html"))
    captured = [capture_one(renderer, s, s.parent.name) for s in sources]
    return 0 if all(captured) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
