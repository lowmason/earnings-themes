"""The root pytest configuration: registered markers, collision-safe imports, and the
repository root on the import path (A §193)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "pyproject.toml"


def run_pytest(
    *args: str, interpreter_flags: tuple[str, ...] = ()
) -> subprocess.CompletedProcess[str]:
    """Run pytest under the root configuration, without touching the repo's cache.

    ``python -m pytest`` puts the working directory on ``sys.path``, as the ``pytest``
    console script does not; ``interpreter_flags=("-I",)`` takes it off again.
    """
    return subprocess.run(
        [
            sys.executable,
            *interpreter_flags,
            "-m",
            "pytest",
            "-c",
            str(CONFIG),
            "-p",
            "no:cacheprovider",
        ]
        + list(args),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_live_marker_is_registered() -> None:
    result = run_pytest("--markers")
    assert result.returncode == 0, result.stderr
    assert "@pytest.mark.live:" in result.stdout


def test_not_live_deselects_live_tests(tmp_path: Path) -> None:
    (tmp_path / "test_marks.py").write_text(
        "import pytest\n"
        "\n"
        "def test_offline():\n"
        "    pass\n"
        "\n"
        "@pytest.mark.live\n"
        "def test_online():\n"
        "    raise AssertionError('a live test ran by default')\n",
        encoding="utf-8",
    )
    result = run_pytest(str(tmp_path), "-m", "not live", "-q")
    assert result.returncode == 0, result.stdout
    assert "1 passed, 1 deselected" in result.stdout


def test_a_bare_run_deselects_live_tests(tmp_path: Path) -> None:
    (tmp_path / "test_marks.py").write_text(
        "import pytest\n"
        "\n"
        "def test_offline():\n"
        "    pass\n"
        "\n"
        "@pytest.mark.live\n"
        "def test_online():\n"
        "    raise AssertionError('a live test ran by default')\n",
        encoding="utf-8",
    )
    result = run_pytest(str(tmp_path), "-q")
    assert result.returncode == 0, result.stdout
    assert "1 passed, 1 deselected" in result.stdout


MARKED = (
    "import pytest\n"
    "\n"
    "def test_offline():\n"
    "    pass\n"
    "\n"
    "@pytest.mark.live\n"
    "def test_online():\n"
    "    raise AssertionError('a live test ran by default')\n"
    "\n"
    "@pytest.mark.browser\n"
    "def test_in_a_browser():\n"
    "    raise AssertionError('a browser test ran by default')\n"
)


def test_browser_marker_is_registered() -> None:
    result = run_pytest("--markers")
    assert result.returncode == 0, result.stderr
    assert "@pytest.mark.browser:" in result.stdout


def test_a_bare_run_deselects_live_and_browser_tests(tmp_path: Path) -> None:
    (tmp_path / "test_marks.py").write_text(MARKED, encoding="utf-8")
    result = run_pytest(str(tmp_path), "-q")
    assert result.returncode == 0, result.stdout
    assert "1 passed, 2 deselected" in result.stdout


def test_the_documented_command_deselects_live_and_browser_tests(
    tmp_path: Path,
) -> None:
    (tmp_path / "test_marks.py").write_text(MARKED, encoding="utf-8")
    result = run_pytest(str(tmp_path), "-m", "not live and not browser", "-q")
    assert result.returncode == 0, result.stdout
    assert "1 passed, 2 deselected" in result.stdout


def test_minus_m_browser_selects_only_browser_tests(tmp_path: Path) -> None:
    (tmp_path / "test_marks.py").write_text(MARKED, encoding="utf-8")
    result = run_pytest(str(tmp_path), "-m", "browser", "-q")
    assert result.returncode == 1, result.stdout
    assert "1 failed, 2 deselected" in result.stdout
    assert "a browser test ran by default" in result.stdout


def test_unregistered_marker_is_an_error(tmp_path: Path) -> None:
    (tmp_path / "test_typo.py").write_text(
        "import pytest\n\n@pytest.mark.lvie\ndef test_typo():\n    pass\n",
        encoding="utf-8",
    )
    result = run_pytest(str(tmp_path), "-q")
    assert result.returncode != 0
    assert "'lvie' not found in `markers`" in result.stdout


def test_same_named_test_modules_do_not_collide(tmp_path: Path) -> None:
    for member in ("first", "second"):
        tests = tmp_path / member / "tests"
        tests.mkdir(parents=True)
        (tests / "test_same_name.py").write_text(
            f"def test_{member}():\n    pass\n", encoding="utf-8"
        )
    result = run_pytest(str(tmp_path), "-q")
    assert result.returncode == 0, result.stdout
    assert "2 passed" in result.stdout


ROOT_PACKAGES = ("tools", "apps", "packages", "tests")


def write_import_probe(directory: Path) -> None:
    """A test file that asks where each root-level package name resolves."""
    (directory / "test_names.py").write_text(
        "import importlib.util\n"
        "from pathlib import Path\n"
        "\n"
        "import pytest\n"
        "\n"
        f"ROOT = Path({str(ROOT)!r})\n"
        "\n"
        f"@pytest.mark.parametrize('name', {list(ROOT_PACKAGES)!r})\n"
        "def test_resolves_to_the_repository(name):\n"
        "    spec = importlib.util.find_spec(name)\n"
        "    assert spec is not None\n"
        "    assert (ROOT / name).resolve() in {\n"
        "        Path(entry).resolve() for entry in spec.submodule_search_locations\n"
        "    }\n",
        encoding="utf-8",
    )


def test_the_console_script_can_import_the_root_level_packages(tmp_path: Path) -> None:
    """The documented command runs the ``pytest`` console script, whose ``sys.path``
    holds neither the working directory nor the repository root, and importlib mode adds
    neither. The Stage 10 tests import ``tools``, ``apps``, ``packages`` and ``tests``
    by dotted name. Those namespace packages resolve only with the root on the path, or
    once an earlier-collected module has registered them, which a single-file run never
    does and ``tools``, with no test files, never does at all. ``-I`` models the script."""
    write_import_probe(tmp_path)
    result = run_pytest(str(tmp_path), "-q", interpreter_flags=("-I",))
    assert result.returncode == 0, result.stdout
    assert f"{len(ROOT_PACKAGES)} passed" in result.stdout


def test_the_import_probe_fails_when_the_root_is_not_on_the_path(
    tmp_path: Path,
) -> None:
    """The probe can fail: with the option blanked, nothing else puts the root on the
    path, so every name is unresolved."""
    write_import_probe(tmp_path)
    result = run_pytest(
        str(tmp_path), "-q", "-o", "pythonpath=", interpreter_flags=("-I",)
    )
    assert result.returncode == 1, result.stdout
    assert f"{len(ROOT_PACKAGES)} failed" in result.stdout
