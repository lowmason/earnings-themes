import contextlib
import json
import socket

import pytest
from pf_dump import (
    EXIT_CRASH,
    EXIT_NETWORK,
    EXIT_OK,
    Cell,
    Element,
    NetworkGuardTripped,
    Row,
    dump_bytes,
    grid_text,
    install_network_guard,
    read_dump,
    run_adapter,
    validate_elements,
)

ROWS = (
    Row(True, (Cell(""), Cell("Three Months Ended", colspan=2))),
    Row(False, (Cell("Net sales"), Cell("4,321"), Cell("3,210"))),
)


def test_grid_text_reads_rows_in_order():
    assert grid_text(ROWS) == " Three Months Ended\nNet sales 4,321 3,210"


def test_dump_round_trips_and_is_canonical(tmp_path):
    elements = [
        Element("other", "", None, None, "DocumentNode"),
        Element("heading", "Results", 0, 1, "HeadingNode"),
        Element("table", grid_text(ROWS), 0, None, "TableNode", ROWS),
    ]
    data = dump_bytes(elements)
    assert data == dump_bytes(list(elements))
    assert data.endswith(b"\n") and b": " not in data
    path = tmp_path / "dump.json"
    path.write_bytes(data)
    assert read_dump(path) == elements


def test_validate_elements_rejects_bad_types_parents_and_grids():
    with pytest.raises(ValueError, match="common type"):
        validate_elements([Element("sidebar", "x")])
    with pytest.raises(ValueError, match="must precede"):
        validate_elements([Element("paragraph", "x", parent=0)])
    with pytest.raises(ValueError, match="only tables"):
        validate_elements([Element("paragraph", "x", rows=ROWS)])
    with pytest.raises(ValueError, match="grid read row by row"):
        validate_elements([Element("table", "wrong", rows=ROWS)])


def test_network_guard_records_trips_and_restores():
    original = socket.getaddrinfo
    guard = install_network_guard()
    try:
        with pytest.raises(NetworkGuardTripped):
            socket.getaddrinfo("example.com", 80)
        with pytest.raises(NetworkGuardTripped):
            socket.create_connection(("example.com", 80))
        with contextlib.suppress(
            NetworkGuardTripped
        ):  # a swallowed trip is still recorded
            socket.gethostbyname("example.com")
    finally:
        guard.restore()
    assert guard.trips == [
        "socket.getaddrinfo",
        "socket.create_connection",
        "socket.gethostbyname",
    ]
    assert socket.getaddrinfo is original


def _args(tmp_path):
    source = tmp_path / "source.html"
    source.write_bytes(b"<p>\x93Hi\x94</p>")
    return source, [
        "--input",
        str(source),
        "--output",
        str(tmp_path / "d.json"),
        "--sidecar",
        str(tmp_path / "s.json"),
    ]


def test_run_adapter_decodes_once_and_writes_dump_and_sidecar(tmp_path):
    _, argv = _args(tmp_path)
    seen = []

    def parse(text):
        seen.append(text)
        return [Element("paragraph", text)]

    assert run_adapter(parse, library=None, argv=argv) == EXIT_OK
    assert seen == ["<p>\u201cHi\u201d</p>"]
    sidecar = json.loads((tmp_path / "s.json").read_text())
    assert sidecar["status"] == "ok" and sidecar["encoding"] == "windows-1252"
    assert read_dump(tmp_path / "d.json") == [
        Element("paragraph", "<p>\u201cHi\u201d</p>")
    ]


def test_run_adapter_voids_a_run_whose_parse_touched_the_network(tmp_path):
    _, argv = _args(tmp_path)

    def parse(text):
        with contextlib.suppress(NetworkGuardTripped):  # a library that swallows it
            socket.create_connection(("example.com", 443))
        return [Element("paragraph", text)]

    assert run_adapter(parse, library=None, argv=argv) == EXIT_NETWORK
    assert not (tmp_path / "d.json").exists()
    assert json.loads((tmp_path / "s.json").read_text())["status"] == "void_network"


def test_run_adapter_records_a_crash(tmp_path):
    _, argv = _args(tmp_path)

    def parse(text):
        raise RuntimeError("boom")

    assert run_adapter(parse, library=None, argv=argv) == EXIT_CRASH
    assert (
        json.loads((tmp_path / "s.json").read_text())["error"] == "RuntimeError: boom"
    )
