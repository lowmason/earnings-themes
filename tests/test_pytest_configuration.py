"""The root pytest configuration: registered markers and collision-safe imports (A §193)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "pyproject.toml"


def run_pytest(*args: str) -> subprocess.CompletedProcess[str]:
    """Run pytest under the root configuration, without touching the repo's cache."""
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-c", str(CONFIG), "-p", "no:cacheprovider"]
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
