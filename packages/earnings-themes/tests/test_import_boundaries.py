"""earnings-themes imports neither earnings-ingestion nor the application, no
browser, and no model SDK, HTTP client, or framework (A §173; browser-rendering
spec, Stage 2 verification; the Stage 6 spec, R14.1: drafting stays outside the
code; the Stage 7 spec, §Packaging and ES10).

Every module is imported, subpackages included, in one fresh interpreter. The local
adapter, behind the ``local-model`` extra, is the one module that loads an HTTP
client, httpx, and nothing else forbidden; no other module loads it (ES15). The six
modules a drafting session may read import nothing from the extractor (the Stage 7
spec, §Verification, GS13).
"""

import ast
import importlib.util
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
PIPELINE_PREFIXES = (
    "earnings_themes.extraction",
    "earnings_themes.support",
    "earnings_themes.coding",
    "earnings_pipeline",
)
NLI_RUNTIME = {
    "torch",
    "transformers",
    "tokenizers",
    "sentencepiece",
    "safetensors",
    "minicheck",
}
LOCAL = "earnings_themes.extraction.local"
"""The local adapter, the one module that imports httpx (ES15)."""
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


def modules_loaded_by(modules: list[str], *, cwd: Path | None = None) -> set[str]:
    """Every module a fresh interpreter holds after importing ``modules``."""
    code = (
        f"import json, sys, {', '.join(modules)};"
        " print(json.dumps(sorted(sys.modules)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        cwd=cwd,
    )
    return set(json.loads(result.stdout))


def top_level(names: set[str]) -> set[str]:
    return {name.partition(".")[0] for name in names}


def test_every_module_is_imported() -> None:
    assert "earnings_themes.annotation" in MODULES
    assert "earnings_themes.extraction.windows" in MODULES
    assert LOCAL in MODULES
    assert len(MODULES) >= 15


def test_importing_earnings_themes_loads_nothing_forbidden() -> None:
    """Every module but the local adapter, which none of them loads."""
    loaded = modules_loaded_by(
        [m for m in MODULES if m not in {LOCAL, "earnings_themes.support.nli"}]
    )
    assert top_level(loaded) & FORBIDDEN == set()
    assert LOCAL not in loaded
    assert top_level(loaded) & NLI_RUNTIME == set()


def test_the_local_adapter_loads_httpx_and_nothing_else_forbidden() -> None:
    assert top_level(modules_loaded_by([LOCAL])) & FORBIDDEN == {"httpx"}


def forbidden_pipeline(names: set[str]) -> list[str]:
    return sorted(n for n in names if n.startswith(PIPELINE_PREFIXES))


def pipeline_imports(path: Path) -> list[str]:
    """Pipeline imports at every AST depth, including relative imports."""
    parts = list(path.with_suffix("").parts)
    if "earnings_themes" in parts:
        parts = parts[parts.index("earnings_themes") :]
        package = ".".join(parts[:-1])
    else:
        package = "earnings_themes"
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), str(path))):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = importlib.util.resolve_name("." * node.level + module, package)
            names = [f"{module}.{alias.name}" for alias in node.names]
            names.append(module)
        else:
            continue
        found += [n for n in names if n.startswith(PIPELINE_PREFIXES)]
    return found


def extraction_imports(path: Path) -> list[str]:
    """Keep the original extraction guard alongside the support extension."""
    return [
        name for name in pipeline_imports(path) if name.startswith(PIPELINE_PREFIXES[0])
    ]


def test_the_drafting_modules_import_nothing_from_the_extractor() -> None:
    """GS13: no drafting session sees Stage 7's code. The six modules import nothing
    from extraction, support, coding or the application, directly or transitively."""
    assert {name: pipeline_imports(SOURCE / name) for name in DRAFTING} == {
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


def test_pipeline_scan_detects_planted_support_and_relative_imports(
    tmp_path: Path,
) -> None:
    package = tmp_path / "earnings_themes"
    package.mkdir()
    module = package / "gold.py"
    module.write_text(
        "def later():\n    from .support import records\n    import earnings_themes.support.records\n",
        encoding="utf-8",
    )
    assert pipeline_imports(module) == [
        "earnings_themes.support.records",
        "earnings_themes.support",
        "earnings_themes.support.records",
    ]


def test_pipeline_scan_detects_planted_coding_import(tmp_path: Path) -> None:
    package = tmp_path / "earnings_themes"
    package.mkdir()
    module = package / "gold.py"
    module.write_text(
        "def later():\n    from .coding import records\n", encoding="utf-8"
    )
    assert pipeline_imports(module) == [
        "earnings_themes.coding.records",
        "earnings_themes.coding",
    ]


def test_pipeline_scan_detects_planted_application_import(tmp_path: Path) -> None:
    module = tmp_path / "gold.py"
    module.write_text(
        "def later():\n    from earnings_pipeline import cli\n", encoding="utf-8"
    )
    assert pipeline_imports(module) == ["earnings_pipeline.cli", "earnings_pipeline"]


def test_drafting_closure_has_no_pipeline_modules() -> None:
    modules = [f"earnings_themes.{n.removesuffix('.py')}" for n in DRAFTING]
    assert forbidden_pipeline(modules_loaded_by(modules)) == []


def test_fresh_process_guard_detects_planted_transitive_support(tmp_path: Path) -> None:
    import shutil

    package = tmp_path / "earnings_themes"
    shutil.copytree(SOURCE, package, ignore=shutil.ignore_patterns("__pycache__"))
    with (package / "tomlfile.py").open("a", encoding="utf-8") as stream:
        stream.write("\nimport earnings_themes.support.records\n")
    loaded = modules_loaded_by(["earnings_themes.gold"], cwd=tmp_path)
    assert "earnings_themes.support.records" in forbidden_pipeline(loaded)


def test_fresh_process_guard_detects_planted_transitive_coding(tmp_path: Path) -> None:
    import shutil

    package = tmp_path / "earnings_themes"
    shutil.copytree(SOURCE, package, ignore=shutil.ignore_patterns("__pycache__"))
    with (package / "tomlfile.py").open("a", encoding="utf-8") as stream:
        stream.write("\nimport earnings_themes.coding.records\n")
    loaded = modules_loaded_by(["earnings_themes.gold"], cwd=tmp_path)
    assert "earnings_themes.coding.records" in forbidden_pipeline(loaded)


def test_fresh_process_guard_detects_planted_application_import(tmp_path: Path) -> None:
    import shutil

    package = tmp_path / "earnings_themes"
    shutil.copytree(SOURCE, package, ignore=shutil.ignore_patterns("__pycache__"))
    application = tmp_path / "earnings_pipeline"
    application.mkdir()
    (application / "__init__.py").write_text(
        "import earnings_themes.coding.records\n", encoding="utf-8"
    )
    with (package / "tomlfile.py").open("a", encoding="utf-8") as stream:
        stream.write("\nimport earnings_pipeline\n")
    loaded = modules_loaded_by(["earnings_themes.gold"], cwd=tmp_path)
    assert {"earnings_pipeline", "earnings_themes.coding.records"} <= set(
        forbidden_pipeline(loaded)
    )


def test_public_coding_import_loads_no_optional_or_concrete_adapter() -> None:
    loaded = modules_loaded_by(["earnings_themes.coding"])
    assert top_level(loaded) & (FORBIDDEN | NLI_RUNTIME) == set()
    assert {
        LOCAL,
        "earnings_themes.support.nli",
        "earnings_themes.coding.local",
    }.isdisjoint(loaded)


def test_nli_import_loads_no_optional_runtime():
    assert (
        top_level(modules_loaded_by(["earnings_themes.support.nli"]))
        & (FORBIDDEN | NLI_RUNTIME)
        == set()
    )


def test_ordinary_imports_do_not_load_nli_adapter():
    loaded = modules_loaded_by(
        [m for m in MODULES if m not in {LOCAL, "earnings_themes.support.nli"}]
    )
    assert "earnings_themes.support.nli" not in loaded


def test_fresh_guard_detects_planted_nli(tmp_path):
    import shutil

    package = tmp_path / "earnings_themes"
    shutil.copytree(SOURCE, package, ignore=shutil.ignore_patterns("__pycache__"))
    with (package / "tomlfile.py").open("a", encoding="utf-8") as stream:
        stream.write("\nimport earnings_themes.support.nli\n")
    assert "earnings_themes.support.nli" in forbidden_pipeline(
        modules_loaded_by(["earnings_themes.gold"], cwd=tmp_path)
    )
