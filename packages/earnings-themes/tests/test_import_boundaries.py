"""earnings-themes imports neither earnings-ingestion nor the application, no
browser, and no model SDK or HTTP client (A §173; browser-rendering spec, Stage 2
verification; the Stage 6 spec, R14.1: drafting stays outside the code)."""

import json
import pkgutil
import subprocess
import sys

import earnings_themes

FORBIDDEN = {
    "earnings_ingestion",
    "earnings_pipeline",
    "selenium",
    "playwright",
    "pyppeteer",
    "pydantic_ai",
    "openai",
    "anthropic",
    "typesafe_sdk",
    "langchain_typesafe",
    "httpx",
}
MODULES = [
    "earnings_themes",
    *(
        f"earnings_themes.{module.name}"
        for module in pkgutil.iter_modules(earnings_themes.__path__)
    ),
]


def modules_loaded_by(modules: list[str]) -> set[str]:
    """Top-level modules a fresh interpreter holds after importing ``modules``."""
    code = (
        f"import json, sys, {', '.join(modules)};"
        " print(json.dumps(sorted(sys.modules)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return {name.partition(".")[0] for name in json.loads(result.stdout)}


def test_every_module_is_imported() -> None:
    assert "earnings_themes.annotation" in MODULES
    assert len(MODULES) >= 12


def test_importing_earnings_themes_loads_nothing_forbidden() -> None:
    assert modules_loaded_by(MODULES) & FORBIDDEN == set()
