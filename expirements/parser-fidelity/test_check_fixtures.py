import hashlib
import subprocess

import pytest
from check_fixtures import check_fixtures, check_locks, declared_dependencies
from test_validate_gold import FID, GOOD_BLOCKS, HEADER, SOURCE

REGISTER = '[sources.sec-edgar]\nredistribution_status = "SEC reuse policy quoted; issuers\' copyright not addressed."\n'


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    fixtures = tmp_path / "tests" / "fixtures" / "releases"
    folder = fixtures / FID
    folder.mkdir(parents=True)
    (folder / "source.html").write_text(SOURCE, encoding="utf-8")
    (folder / "gold.toml").write_text(HEADER + GOOD_BLOCKS, encoding="utf-8")
    sha = hashlib.sha256(SOURCE.encode()).hexdigest()
    (fixtures / "manifest.toml").write_text(
        f'[[fixtures]]\nfixture_id = "{FID}"\nsha256 = "{sha}"\nsource_id = "sec-edgar"\n'
    )
    (tmp_path / ".gitattributes").write_text(
        "tests/fixtures/releases/*/source.html -text\n"
    )
    (tmp_path / ".gitignore").write_text(".DS_Store\n")
    (tmp_path / "register.toml").write_text(REGISTER)
    return tmp_path


def run(repo):
    return check_fixtures(
        repo / "tests" / "fixtures" / "releases", repo / "register.toml", repo
    )


def test_a_complete_fixture_passes(repo):
    assert run(repo) == []


def test_ignored_files_such_as_ds_store_do_not_count(repo):
    folder = repo / "tests" / "fixtures" / "releases" / FID
    (folder / ".DS_Store").write_bytes(b"finder")
    assert run(repo) == []


def test_missing_attribute_extra_file_and_bad_hash_are_reported(repo):
    (repo / ".gitattributes").write_text("")
    folder = repo / "tests" / "fixtures" / "releases" / FID
    (folder / "notes.txt").write_text("x")
    (folder / "source.html").write_text(SOURCE + " ", encoding="utf-8")
    problems = run(repo)
    assert any("does not mark source.html -text" in p for p in problems)
    assert any("expected exactly" in p for p in problems)
    assert any("does not match its manifest sha256" in p for p in problems)


def test_unknown_source_and_orphan_entries_are_reported(repo):
    (repo / "register.toml").write_text(
        "[sources.other]\nredistribution_status = 'x'\n"
    )
    (repo / "tests" / "fixtures" / "releases" / "0009999999-25-000001_ex-99").mkdir()
    problems = run(repo)
    assert any("has no register entry" in p for p in problems)
    assert any("directory has no manifest entry" in p for p in problems)


def test_locks_must_be_committed_for_scripts_with_dependencies(tmp_path):
    git(tmp_path, "init", "-q")
    harness = tmp_path / "h"
    harness.mkdir()
    (harness / "tool.py").write_text(
        '# /// script\n# requires-python = ">=3.14"\n# dependencies = ["httpx==0.28.1"]\n# ///\n'
    )
    (harness / "plain.py").write_text("import json\n")
    assert declared_dependencies(harness / "tool.py") == ["httpx==0.28.1"]
    assert check_locks(harness, tmp_path) == [
        "tool.py: declares dependencies but tool.py.lock is not committed"
    ]
    (harness / "tool.py.lock").write_text("version = 1\n")
    git(tmp_path, "add", "h/tool.py.lock")
    assert check_locks(harness, tmp_path) == []
