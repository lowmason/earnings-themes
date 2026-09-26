"""Saved artifacts: content-addressed, never overwritten, every retrieval kept in a
checked retrieval record."""

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from earnings_core import RightsStatus, sha256_hex
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore, write_new
from pydantic import ValidationError

BODY = b"<p>An announcement.</p>"
WHEN = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)
RIGHTS = {"rights_status": RightsStatus.LOCAL_ONLY, "rights_basis": "unclear terms"}


def retrieval(body: bytes = BODY, when: datetime = WHEN) -> Retrieval:
    return Retrieval(
        request_url="https://press.example.org/a",
        final_url="https://press.example.org/a",
        retrieved_at=when,
        retrieval_method=RetrievalMethod.HTTP,
        http_status=200,
        media_type="text/html",
        content_type="text/html; charset=utf-8",
        byte_count=len(body),
        sha256=sha256_hex(body),
    )


def store_in(tmp_path: Path) -> ArtifactStore:
    return ArtifactStore(tmp_path / "data" / "raw" / "cohort", tmp_path)


def test_an_artifact_is_stored_by_hash_with_a_portable_reference(tmp_path) -> None:
    store = store_in(tmp_path)
    ref = store.put("press", BODY, retrieval(), **RIGHTS)
    digest = sha256_hex(BODY)
    assert ref.storage_ref == f"data/raw/cohort/press/{digest}.html"
    assert ref.rights_status is RightsStatus.LOCAL_ONLY
    stored = store.get("press", digest, **RIGHTS)
    assert stored.body == BODY
    assert stored.ref == ref
    assert stored.retrievals == (retrieval(),)


def test_each_retrieval_is_kept_and_the_bytes_once(tmp_path) -> None:
    store = store_in(tmp_path)
    later = WHEN + timedelta(days=1)
    store.put("press", BODY, retrieval(when=later), **RIGHTS)
    store.put("press", BODY, retrieval(), **RIGHTS)
    stored = store.get("press", sha256_hex(BODY), **RIGHTS)
    assert [r.retrieved_at for r in stored.retrievals] == [WHEN, later]
    assert (
        len(list((tmp_path / "data" / "raw" / "cohort" / "press").glob("*.html"))) == 1
    )


def test_a_record_for_other_bytes_is_refused(tmp_path) -> None:
    with pytest.raises(ValueError, match="other bytes"):
        store_in(tmp_path).put("press", b"other", retrieval(), **RIGHTS)


def test_changed_bytes_on_disk_are_detected(tmp_path) -> None:
    store = store_in(tmp_path)
    ref = store.put("press", BODY, retrieval(), **RIGHTS)
    (tmp_path / ref.storage_ref).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="no longer hashes"):
        store.get("press", sha256_hex(BODY), **RIGHTS)


def test_a_missing_artifact_is_reported_not_empty(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        store_in(tmp_path).get("press", sha256_hex(b"absent"), **RIGHTS)


@pytest.mark.parametrize("source_id", ["../escape", "Press", "", "a/b"])
def test_a_source_id_must_be_a_slug(tmp_path, source_id) -> None:
    with pytest.raises(ValueError, match="slug"):
        store_in(tmp_path).put(source_id, BODY, retrieval(), **RIGHTS)


def test_the_latest_retrieval_of_a_url_names_its_artifact(tmp_path) -> None:
    store = store_in(tmp_path)
    newer = b"<p>A corrected announcement.</p>"
    store.put("press", BODY, retrieval(), **RIGHTS)
    store.put("press", newer, retrieval(newer, WHEN + timedelta(hours=1)), **RIGHTS)
    latest = store.latest("press", "https://press.example.org/a", **RIGHTS)
    assert latest.body == newer
    assert store.latest("press", "https://press.example.org/b", **RIGHTS) is None
    assert store.latest("other", "https://press.example.org/a", **RIGHTS) is None


def test_a_written_file_is_never_replaced(tmp_path) -> None:
    path = tmp_path / "manifest.json"
    write_new(path, b"first")
    write_new(path, b"first")
    with pytest.raises(FileExistsError, match="holds other bytes"):
        write_new(path, b"second")
    assert path.read_bytes() == b"first"
    assert [p.name for p in tmp_path.iterdir()] == ["manifest.json"]


def test_a_retrieval_is_utc_and_records_status_only_for_http() -> None:
    fields = {
        "request_url": "https://www.example.gov/x",
        "final_url": "https://www.example.gov/x",
        "retrieved_at": WHEN,
        "retrieval_method": RetrievalMethod.HTTP,
        "http_status": 200,
        "media_type": "text/html",
        "content_type": "text/html",
        "byte_count": 1,
        "sha256": sha256_hex(b"x"),
    }
    Retrieval(**fields)
    with pytest.raises(ValidationError, match="UTC"):
        Retrieval(
            **fields | {"retrieved_at": WHEN.astimezone(timezone(timedelta(hours=-4)))}
        )
    with pytest.raises(ValidationError, match="http_status"):
        Retrieval(**fields | {"retrieval_method": RetrievalMethod.SAVED_BY_USER})
