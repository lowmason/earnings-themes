from lock_gate import add_dependency, locked_versions, lowered_versions, runtime_closure

PYPROJECT = '[project]\nname = "earnings-ingestion"\ndependencies = [\n    "earnings-core",\n    "lxml",\n]\n'

LOCK = {
    "package": [
        {
            "name": "earnings-ingestion",
            "version": "0.1.0",
            "dependencies": [{"name": "lxml"}, {"name": "edgartools"}],
        },
        {"name": "lxml", "version": "6.1.3"},
        {
            "name": "edgartools",
            "version": "5.58.0",
            "dependencies": [
                {"name": "pandas"},
                {"name": "httpxthrottlecache", "extra": ["httpx"]},
            ],
        },
        {"name": "pandas", "version": "3.0.6", "dependencies": [{"name": "numpy"}]},
        {"name": "numpy", "version": "2.3.0"},
        {
            "name": "httpxthrottlecache",
            "version": "0.6.1",
            "dependencies": [{"name": "filelock"}],
            "optional-dependencies": {"httpx": [{"name": "httpx"}]},
        },
        {"name": "filelock", "version": "3.0"},
        {"name": "httpx", "version": "0.28.1"},
        {"name": "rapidfuzz", "version": "3.0"},
    ]
}


def test_add_dependency_inserts_into_runtime_dependencies():
    text = add_dependency(PYPROJECT, "edgartools==5.58.0")
    assert '    "edgartools==5.58.0",\n    "earnings-core",' in text


def test_lowered_versions_compare_as_versions():
    old = {"lxml": "6.1.3", "pandas": "3.0.6", "numpy": "2.10.0"}
    new = {"lxml": "5.4.0", "pandas": "3.0.6", "numpy": "2.9.9"}
    assert lowered_versions(old, new) == [
        "lxml 6.1.3 -> 5.4.0",
        "numpy 2.10.0 -> 2.9.9",
    ]
    assert locked_versions(LOCK)["pandas"] == "3.0.6"


def test_runtime_closure_follows_requested_extras_only():
    closure = runtime_closure(LOCK)
    assert closure == {
        "lxml",
        "edgartools",
        "pandas",
        "numpy",
        "httpxthrottlecache",
        "filelock",
        "httpx",
    }
    assert "rapidfuzz" not in closure
