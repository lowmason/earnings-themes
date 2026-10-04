"""earnings-themes imports neither earnings-ingestion nor the application, no
browser, and no model SDK, HTTP client, or framework (A §173; browser-rendering
spec, Stage 2 verification; the Stage 6 spec, R14.1: drafting stays outside the
code; the Stage 7 spec, §Packaging and ES10).

Every module is imported, subpackages included, in one fresh interpreter. The six
modules a drafting session may read import nothing from the extractor (the Stage 7
spec, §Verification, GS13).
"""

import ast
import json
import pkgutil
import subprocess
import sys
from pathlib import Path

import earnings_themes

HTTP_CLIENTS = {"httpx", "requests", "aiohttp", "urllib3"}
MODEL_SDKS = {
    "openai",
    "anthropic",
    "typesafe_sdk",
    "langchain_typesafe",
    "ollama",
    "mistralai",
    "cohere",
    "litellm",
}
FRAMEWORKS = {
    "pydantic_ai",
    "langgraph",
    "langchain",
    "langchain_core",
    "dspy",
    "crewai",
    "llama_index",
    "instructor",
    "outlines",
}
FORBIDDEN = {
    "earnings_ingestion",
    "earnings_pipeline",
    "selenium",
    "playwright",
    "pyppeteer",
    *HTTP_CLIENTS,
    *MODEL_SDKS,
    *FRAMEWORKS,
}
MODULES = [
    "earnings_themes",
    *(
        module.name
        for module in pkgutil.walk_packages(
            earnings_themes.__path__, prefix="earnings_themes."
        )
    ),
]
SOURCE = Path(earnings_themes.__file__).parent
DRAFTING = (
    "gold.py",
    "annotation.py",
    "anchoring.py",
    "codebook.py",
    "records.py",
    "tomlfile.py",
)
"""The modules the gold brief lets a drafting session read (GS13)."""


def modules_loaded_by(modules: list[str]) -> set[str]:
    """Every module a fresh interpreter holds after importing ``modules``."""
    code = (
        f"import json, sys, {', '.join(modules)};"
        " print(json.dumps(sorted(sys.modules)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return set(json.loads(result.stdout))


def top_level(names: set[str]) -> set[str]:
    return {name.partition(".")[0] for name in names}


def test_every_module_is_imported() -> None:
    assert "earnings_themes.annotation" in MODULES
    assert "earnings_themes.extraction.windows" in MODULES
    assert len(MODULES) >= 15


def test_importing_earnings_themes_loads_nothing_forbidden() -> None:
    assert top_level(modules_loaded_by(MODULES)) & FORBIDDEN == set()


def extraction_imports(path: Path) -> list[str]:
    """What a module imports from the extractor, at any depth."""
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), str(path))):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names = [f"{node.module}.{alias.name}" for alias in node.names]
            names.append(node.module)
        else:
            continue
        found += [n for n in names if n.startswith("earnings_themes.extraction")]
    return found


def test_the_drafting_modules_import_nothing_from_the_extractor() -> None:
    """GS13: no drafting session sees Stage 7's code. The six modules import nothing
    from ``earnings_themes.extraction``, directly or through another module."""
    assert {name: extraction_imports(SOURCE / name) for name in DRAFTING} == {
        name: [] for name in DRAFTING
    }
    modules = [f"earnings_themes.{name.removesuffix('.py')}" for name in DRAFTING]
    loaded = modules_loaded_by(modules)
    assert sorted(n for n in loaded if n.startswith("earnings_themes.extraction")) == []


def test_the_drafting_scan_sees_an_import_inside_a_function(tmp_path: Path) -> None:
    module = tmp_path / "late.py"
    module.write_text(
        "def later():\n"
        "    from earnings_themes.extraction import windows\n"
        "    import earnings_themes.extraction.records\n",
        encoding="utf-8",
    )
    assert extraction_imports(module) == [
        "earnings_themes.extraction.windows",
        "earnings_themes.extraction",
        "earnings_themes.extraction.records",
    ]
