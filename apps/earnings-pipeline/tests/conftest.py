"""Shared fixtures: a test's client locks never reach the user's cache (plan 7)."""

import pytest
from earnings_ingestion.fetch.client import LOCK_DIR_VARIABLE


@pytest.fixture(autouse=True)
def machine_locks(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The machine's lock directory, for this test only (plan 7, P7-5)."""
    monkeypatch.setenv(LOCK_DIR_VARIABLE, str(tmp_path_factory.mktemp("locks")))
