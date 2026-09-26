"""A static scan of every package's imports, alongside the runtime checks (A §173; B3).

The runtime checks in ``packages/*/tests/test_import_boundaries.py`` see only what a
top-level import loads, so an import inside a function escapes them. This scan reads
every module under each member's ``src/`` with ``ast`` and refuses:

- a sibling import the dependency table in ``CLAUDE.md`` forbids;
- a browser import (Selenium, websocket-client, Playwright, pyppeteer) anywhere but
  ``earnings_ingestion.browser.selenium_capture``, the one adapter behind the
  ``browser-capture`` extra.
"""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "earnings_core": ROOT / "packages" / "earnings-core" / "src" / "earnings_core",
    "earnings_ingestion": ROOT
    / "packages"
    / "earnings-ingestion"
    / "src"
    / "earnings_ingestion",
    "earnings_themes": ROOT
    / "packages"
    / "earnings-themes"
    / "src"
    / "earnings_themes",
    "earnings_pipeline": ROOT
    / "apps"
    / "earnings-pipeline"
    / "src"
    / "earnings_pipeline",
}
ALLOWED = {
    "earnings_core": set(),
    "earnings_ingestion": {"earnings_core"},
    "earnings_themes": {"earnings_core"},
    "earnings_pipeline": {"earnings_core", "earnings_ingestion", "earnings_themes"},
}
BROWSERS = frozenset({"selenium", "websocket", "playwright", "pyppeteer"})
ADAPTER = SOURCES["earnings_ingestion"] / "browser" / "selenium_capture.py"


def imported(path: Path) -> list[tuple[int, str]]:
    """Every absolute module a file imports, at any depth, with its line."""
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), str(path))):
        if isinstance(node, ast.Import):
            found += [(node.lineno, alias.name) for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.append((node.lineno, node.module))
    return found


def violations(package: str) -> list[str]:
    members = set(SOURCES) - {package}
    out: list[str] = []
    for path in sorted(SOURCES[package].rglob("*.py")):
        for line, module in imported(path):
            top = module.partition(".")[0]
            where = f"{path.relative_to(ROOT)}:{line}"
            if top in members and top not in ALLOWED[package]:
                out.append(f"{where} imports {module}")
            if top in BROWSERS and path != ADAPTER:
                out.append(f"{where} imports the browser module {module}")
    return out


@pytest.mark.parametrize("package", sorted(SOURCES))
def test_no_package_imports_what_its_boundary_forbids(package: str) -> None:
    assert violations(package) == []


def test_the_scan_sees_imports_inside_functions(tmp_path: Path) -> None:
    module = tmp_path / "late.py"
    module.write_text(
        "def later():\n    import selenium.webdriver\n    from earnings_themes import x\n",
        encoding="utf-8",
    )
    assert imported(module) == [(2, "selenium.webdriver"), (3, "earnings_themes")]


def test_the_adapter_is_the_one_module_that_imports_a_browser() -> None:
    assert any(module.startswith("selenium") for _, module in imported(ADAPTER))
