"""Visibility and partition boundaries refuse before any source or model is opened."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from earnings_pipeline.stage6 import Layout
from earnings_themes.split import Partition


def test_test_and_excluded_refuse_before_metadata_or_source_loading(
    tmp_path, monkeypatch
):
    import earnings_pipeline.pilot_inputs as module

    trips = []

    def blocked(*args):
        trips.append(True)
        raise AssertionError("INVENTED_SOURCE_SENTINEL")

    monkeypatch.setattr(module, "load_pinned", blocked)
    for partition in (Partition.TEST, Partition.EXCLUDED):
        with pytest.raises(module.WorkflowError, match="malformed_record"):
            module.open_pilot(
                Layout(tmp_path, Path("u"), Path("p"), "a" * 64),
                tmp_path / "settings.json",
                partition,
            )
    assert trips == []


def test_visibility_refuses_missing_gold_before_documents_or_settings(
    tmp_path, monkeypatch
):
    import earnings_pipeline.pilot_inputs as module
    from earnings_themes.records import RecordError

    trips = []
    pinned = SimpleNamespace(
        events=SimpleNamespace(definition=SimpleNamespace(corpus_id="invented")),
        gold_dir=tmp_path / "gold",
        evaluation=tmp_path / "evaluation",
    )
    split = SimpleNamespace(
        events_in=lambda p: (
            ("invented:train",) if p is Partition.TRAIN else ("invented:dev",)
        )
    )
    monkeypatch.setattr(module, "load_pinned", lambda layout: pinned)
    monkeypatch.setattr(module, "pinned_split", lambda layout, pin: split)
    monkeypatch.setattr(module, "derive_split", lambda layout, pin: split)
    monkeypatch.setattr(module, "pinned_codebook", lambda layout: object())

    def blocked(*args, **kwargs):
        trips.append(True)
        raise AssertionError("INVENTED_SOURCE_SENTINEL")

    monkeypatch.setattr(module, "documents", blocked)
    monkeypatch.setattr(module, "load_settings", blocked)
    with pytest.raises(RecordError, match="visibility"):
        module.open_pilot(
            Layout(tmp_path, Path("u"), Path("p"), "a" * 64),
            tmp_path / "settings.json",
            Partition.TRAIN,
        )
    assert trips == []


def test_self_sealed_reduced_split_refuses_before_gold_or_source(tmp_path, monkeypatch):
    from datetime import date

    import earnings_pipeline.pilot_inputs as module
    from earnings_pipeline import stage6
    from earnings_themes.records import Pin, RecordError, checked, sealed

    pin = Pin(
        pilot_id="invented",
        pilot_version=1,
        pilot_hash="a" * 64,
        events_version=1,
        events_hash="b" * 64,
        universe_version=1,
        universe_operative_hash="c" * 64,
    )
    rows = (
        SimpleNamespace(
            event_id="invented:train-a",
            issuer_id="invented:issuer-a",
            period_end=date(2025, 3, 31),
        ),
        SimpleNamespace(
            event_id="invented:train-b",
            issuer_id="invented:issuer-b",
            period_end=date(2025, 6, 30),
        ),
        SimpleNamespace(
            event_id="invented:dev",
            issuer_id="invented:issuer-dev",
            period_end=date(2025, 12, 31),
        ),
    )
    pinned = SimpleNamespace(
        pin=pin,
        events=SimpleNamespace(rows=rows),
        pilot=SimpleNamespace(rows=rows),
    )
    layout = Layout(tmp_path, Path("u"), Path("p"), "a" * 64)
    monkeypatch.setattr(stage6, "fixture_event_ids", lambda layout, events: frozenset())
    full = module.derive_split(layout, pinned)
    reduced = sealed(
        full.model_copy(
            update={
                "rows": tuple(
                    row for row in full.rows if row.event_id != "invented:train-b"
                )
            }
        )
    )
    assert checked(reduced, "split") == reduced
    assert len(full.events_in(Partition.TRAIN)) == 2
    assert len(reduced.events_in(Partition.TRAIN)) == 1
    trips = []

    def blocked(*args, **kwargs):
        trips.append(True)
        raise AssertionError("INVENTED_SOURCE_SENTINEL")

    monkeypatch.setattr(module, "load_pinned", lambda layout: pinned)
    monkeypatch.setattr(module, "pinned_split", lambda layout, pin: reduced)
    for name in ("pinned_codebook", "load_gold", "documents", "load_settings"):
        monkeypatch.setattr(module, name, blocked)
    with pytest.raises(RecordError, match="binding_mismatch"):
        module.open_pilot(layout, tmp_path / "settings.json", Partition.TRAIN)
    assert trips == []


def test_committed_metadata_refuses_missing_or_changed_head_bytes(
    tmp_path, monkeypatch
):
    import earnings_pipeline.pilot_inputs as module
    from earnings_themes.records import RecordError

    path = tmp_path / "metadata.json"
    path.write_bytes(b"INVENTED_METADATA_SENTINEL")
    calls = []

    def git(args, **kwargs):
        calls.append((args, kwargs["cwd"]))
        return SimpleNamespace(
            returncode=0, stdout=b"changed", stderr=b"INVENTED_EXCEPTION_SENTINEL"
        )

    monkeypatch.setattr(module.subprocess, "run", git)
    with pytest.raises(RecordError, match="not_committed") as caught:
        module.require_committed(tmp_path, path, "gold")
    assert "INVENTED" not in str(caught.value)
    assert calls == [(["git", "show", "HEAD:metadata.json"], tmp_path)]


@pytest.mark.parametrize("local_state", ("missing", "unreadable"))
def test_committed_metadata_closes_local_read_failures(
    tmp_path, monkeypatch, local_state
):
    import earnings_pipeline.pilot_inputs as module
    from earnings_themes.records import RecordError

    path = tmp_path / "metadata.json"
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout=b"invented", stderr=b""
        ),
    )
    if local_state == "unreadable":
        path.write_bytes(b"invented")

        def unreadable(self):
            raise PermissionError("INVENTED_EXCEPTION_SENTINEL")

        monkeypatch.setattr(Path, "read_bytes", unreadable)
    with pytest.raises(RecordError) as caught:
        module.require_committed(tmp_path, path, "gold")
    assert caught.value.name == "gold"
    assert caught.value.problems == ("not_committed",)
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__
    assert "INVENTED" not in str(caught.value)


def test_committed_metadata_closes_git_launch_failure(tmp_path, monkeypatch):
    import earnings_pipeline.pilot_inputs as module
    from earnings_themes.records import RecordError

    path = tmp_path / "metadata.json"
    path.write_bytes(b"invented")

    def unavailable(*args, **kwargs):
        raise OSError("INVENTED_EXCEPTION_SENTINEL")

    monkeypatch.setattr(module.subprocess, "run", unavailable)
    with pytest.raises(RecordError) as caught:
        module.require_committed(tmp_path, path, "gold")
    assert caught.value.name == "gold"
    assert caught.value.problems == ("not_committed",)
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__
    assert "INVENTED" not in str(caught.value)
