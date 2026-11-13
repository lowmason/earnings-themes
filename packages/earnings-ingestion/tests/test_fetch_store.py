"""Saved artifacts: content-addressed, never overwritten, every retrieval kept in a
checked retrieval record."""

import os
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


def test_a_file_is_synced_before_it_is_linked(tmp_path, monkeypatch) -> None:
    calls: list[str] = []
    real_fsync, real_link = os.fsync, os.link
    data = b"x" * 100

    def fsync(fd: int) -> None:
        # The bytes must have left Python's buffer before the sync, or it syncs nothing.
        assert os.fstat(fd).st_size == len(data)
        calls.append("fsync")
        real_fsync(fd)

    def link(source, destination) -> None:
        calls.append("link")
        real_link(source, destination)

    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(os, "link", link)
    write_new(tmp_path / "a.json", data)
    assert calls == ["fsync", "link"]
    assert (tmp_path / "a.json").read_bytes() == data


def test_a_failed_sync_leaves_nothing_at_the_path(tmp_path, monkeypatch) -> None:
    def fsync(fd: int) -> None:
        raise OSError("disk")

    monkeypatch.setattr(os, "fsync", fsync)
    with pytest.raises(OSError, match="disk"):
        write_new(tmp_path / "a.json", b"x")
    assert list(tmp_path.iterdir()) == []


def test_empty_bytes_in_a_new_folder_are_synced_before_they_are_linked(
    tmp_path, monkeypatch
) -> None:
    calls: list[str] = []
    real_fsync, real_link = os.fsync, os.link

    def fsync(fd: int) -> None:
        calls.append("fsync")
        real_fsync(fd)

    def link(source, destination) -> None:
        calls.append("link")
        real_link(source, destination)

    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(os, "link", link)
    write_new(tmp_path / "new" / "empty.json", b"")
    assert calls == ["fsync", "link"]
    assert (tmp_path / "new" / "empty.json").read_bytes() == b""
    assert [p.name for p in (tmp_path / "new").iterdir()] == ["empty.json"]


def damage_and_rewrite(tmp_path: Path) -> tuple[ArtifactStore, Path]:
    """Store ``BODY``, change its bytes to ``BODY[:5]``, then put it again a day later."""
    store = store_in(tmp_path)
    path = tmp_path / store.put("press", BODY, retrieval(), **RIGHTS).storage_ref
    path.write_bytes(BODY[:5])
    store.put("press", BODY, retrieval(when=WHEN + timedelta(days=1)), **RIGHTS)
    return store, path


def test_changed_bytes_are_moved_aside_by_a_rewrite_never_deleted(tmp_path) -> None:
    store, path = damage_and_rewrite(tmp_path)
    assert store.get("press", sha256_hex(BODY), **RIGHTS).body == BODY
    moved = (
        path.parent / "quarantine" / sha256_hex(BODY) / f"{sha256_hex(BODY[:5])}.html"
    )
    assert moved.read_bytes() == BODY[:5]
    assert store.quarantined == [moved]
    assert len(store.retrievals("press", sha256_hex(BODY))) == 2


def test_bytes_that_are_gone_need_no_quarantine(tmp_path) -> None:
    store = store_in(tmp_path)
    path = tmp_path / store.put("press", BODY, retrieval(), **RIGHTS).storage_ref
    path.unlink()
    store.put("press", BODY, retrieval(when=WHEN + timedelta(days=1)), **RIGHTS)
    assert store.quarantined == []
    assert not (path.parent / "quarantine").exists()
    assert store.get("press", sha256_hex(BODY), **RIGHTS).body == BODY


def test_valid_bytes_are_never_moved_or_replaced(tmp_path) -> None:
    store = store_in(tmp_path)
    path = tmp_path / store.put("press", BODY, retrieval(), **RIGHTS).storage_ref
    inode = path.stat().st_ino
    store.put("press", BODY, retrieval(when=WHEN + timedelta(days=1)), **RIGHTS)
    assert path.stat().st_ino == inode
    assert store.quarantined == []


def test_the_same_damage_twice_is_kept_once_and_other_damage_beside_it(
    tmp_path,
) -> None:
    store = store_in(tmp_path)
    path = tmp_path / store.put("press", BODY, retrieval(), **RIGHTS).storage_ref
    for day, damage in enumerate([BODY[:5], BODY[:5], BODY[:7]], start=1):
        path.write_bytes(damage)
        store.put("press", BODY, retrieval(when=WHEN + timedelta(days=day)), **RIGHTS)
    folder = path.parent / "quarantine" / sha256_hex(BODY)
    assert len(list(folder.iterdir())) == 2


def test_a_failed_rewrite_after_the_move_loses_nothing(tmp_path, monkeypatch) -> None:
    store = store_in(tmp_path)
    path = tmp_path / store.put("press", BODY, retrieval(), **RIGHTS).storage_ref
    path.write_bytes(BODY[:5])
    later = retrieval(when=WHEN + timedelta(days=1))
    calls: list[Path] = []

    def write_new(target: Path, data: bytes) -> None:
        calls.append(target)
        raise OSError("disk")

    monkeypatch.setattr("earnings_ingestion.fetch.store.write_new", write_new)
    with pytest.raises(OSError, match="disk"):
        store.put("press", BODY, later, **RIGHTS)
    monkeypatch.undo()
    assert len(calls) == 1
    (moved,) = (path.parent / "quarantine" / sha256_hex(BODY)).iterdir()
    assert moved.read_bytes() == BODY[:5]
    with pytest.raises(FileNotFoundError, match="bytes are gone"):
        store.get("press", sha256_hex(BODY), **RIGHTS)
    store.put("press", BODY, later, **RIGHTS)
    assert store.get("press", sha256_hex(BODY), **RIGHTS).body == BODY


def test_the_quarantine_is_not_read_as_a_saved_response(tmp_path) -> None:
    store, path = damage_and_rewrite(tmp_path)
    assert len(store.retrievals("press", sha256_hex(BODY))) == 2
    assert [p.name for p in path.parent.glob("*.html")] == [path.name]
    latest = store.latest("press", "https://press.example.org/a", **RIGHTS)
    assert latest.body == BODY


def test_an_empty_damaged_artifact_is_quarantined_not_left_in_the_way(
    tmp_path,
) -> None:
    store = store_in(tmp_path)
    path = tmp_path / store.put("press", BODY, retrieval(), **RIGHTS).storage_ref
    path.write_bytes(b"")
    store.put("press", BODY, retrieval(when=WHEN + timedelta(days=1)), **RIGHTS)
    assert store.get("press", sha256_hex(BODY), **RIGHTS).body == BODY
    moved = path.parent / "quarantine" / sha256_hex(BODY) / f"{sha256_hex(b'')}.html"
    assert moved.read_bytes() == b""
    assert store.quarantined == [moved]


def test_quarantine_moves_nothing_absent_or_valid(tmp_path) -> None:
    store = store_in(tmp_path)
    assert store.quarantine("press", sha256_hex(BODY), "text/html") is None
    path = tmp_path / store.put("press", BODY, retrieval(), **RIGHTS).storage_ref
    assert store.quarantine("press", sha256_hex(BODY), "text/html") is None
    assert path.read_bytes() == BODY
    assert not (path.parent / "quarantine").exists()
    assert store.quarantined == []


def test_quarantine_links_the_damaged_file_under_its_own_extension(tmp_path) -> None:
    store = store_in(tmp_path)
    body = b"%PDF-1.4\n%%EOF\n"
    record = retrieval(body).model_copy(
        update={"media_type": "application/pdf", "content_type": "application/pdf"}
    )
    path = tmp_path / store.put("press", body, record, **RIGHTS).storage_ref
    path.write_bytes(body[:4])
    inode = path.stat().st_ino
    moved = store.quarantine("press", sha256_hex(body), "application/pdf")
    assert moved == (
        path.parent / "quarantine" / sha256_hex(body) / f"{sha256_hex(body[:4])}.pdf"
    )
    assert moved.stat().st_ino == inode
    assert moved.read_bytes() == body[:4]
    assert not path.exists()
    assert store.quarantined == [moved]


def test_every_move_is_listed_oldest_first_and_no_kept_copy_is_replaced(
    tmp_path,
) -> None:
    store = store_in(tmp_path)
    path = tmp_path / store.put("press", BODY, retrieval(), **RIGHTS).storage_ref
    folder = path.parent / "quarantine" / sha256_hex(BODY)
    first, other = (folder / f"{sha256_hex(d)}.html" for d in (BODY[:5], BODY[:7]))
    inodes = []
    for day, damage in enumerate([BODY[:5], BODY[:5], BODY[:7]], start=1):
        path.write_bytes(damage)
        store.put("press", BODY, retrieval(when=WHEN + timedelta(days=day)), **RIGHTS)
        inodes.append(first.stat().st_ino)
    assert store.quarantined == [first, first, other]
    assert inodes[0] == inodes[1] == inodes[2]
    assert (first.read_bytes(), other.read_bytes()) == (BODY[:5], BODY[:7])
    assert store_in(tmp_path).quarantined == []


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


def test_a_pdf_is_stored_as_a_pdf(tmp_path) -> None:
    body = b"%PDF-1.4\n%%EOF\n"
    record = retrieval(body).model_copy(
        update={"media_type": "application/pdf", "content_type": "application/pdf"}
    )
    ref = store_in(tmp_path).put("press", body, record, **RIGHTS)
    assert ref.storage_ref == f"data/raw/cohort/press/{sha256_hex(body)}.pdf"
    assert (tmp_path / ref.storage_ref).read_bytes() == body
