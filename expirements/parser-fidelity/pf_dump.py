"""Element dumps, the network guard, and the adapter entry point (spec: Candidate harness).

A dump is the ordered list of elements a candidate emits for one release, in the
candidate's document order. Containers carry empty text (their children carry it), so
joining element texts never duplicates content. ``parent`` is an index into the same
list; no library identifier is ever written, so two runs can be compared byte for
byte. Dumps carry no run metadata: timing and status go to a separate sidecar.

This module shapes every dump, so it is frozen with the adapters (freeze.py).
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import socket
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from pf_decode import decode_html_bytes

COMMON_TYPES = frozenset(
    {"heading", "paragraph", "list_item", "footnote", "table", "other"}
)
DUMP_SCHEMA_VERSION = 1
EXIT_OK, EXIT_CRASH, EXIT_NETWORK = 0, 2, 3


@dataclass(frozen=True)
class Cell:
    text: str
    colspan: int = 1
    rowspan: int = 1


@dataclass(frozen=True)
class Row:
    header: bool
    cells: tuple[Cell, ...]


@dataclass(frozen=True)
class Element:
    type: str
    text: str
    parent: int | None = None
    level: int | None = None
    source_type: str = ""  # the library's own type name, for the published type mapping
    rows: tuple[Row, ...] | None = (
        None  # the grid, when the candidate exposes table cells
    )


def grid_text(rows: Sequence[Row]) -> str:
    """A grid read row by row in the given order: cells joined by spaces, rows by newlines."""
    return "\n".join(" ".join(cell.text for cell in row.cells) for row in rows)


def validate_elements(elements: Sequence[Element]) -> None:
    for index, element in enumerate(elements):
        if element.type not in COMMON_TYPES:
            raise ValueError(
                f"element {index}: type {element.type!r} is not a common type"
            )
        if element.parent is not None and not 0 <= element.parent < index:
            raise ValueError(
                f"element {index}: parent {element.parent} must precede it"
            )
        if element.rows is not None and element.type != "table":
            raise ValueError(f"element {index}: only tables carry rows")
        if element.rows is not None and element.text != grid_text(element.rows):
            raise ValueError(
                f"element {index}: a grid table's text must be its grid read row by row"
            )


def _element_json(element: Element) -> dict:
    data: dict = {
        "type": element.type,
        "text": element.text,
        "parent": element.parent,
        "source_type": element.source_type,
    }
    if element.level is not None:
        data["level"] = element.level
    if element.rows is not None:
        data["rows"] = [
            {
                "header": row.header,
                "cells": [[c.text, c.colspan, c.rowspan] for c in row.cells],
            }
            for row in element.rows
        ]
    return data


def dump_bytes(elements: Sequence[Element]) -> bytes:
    document = {
        "schema_version": DUMP_SCHEMA_VERSION,
        "elements": [_element_json(e) for e in elements],
    }
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode()


def read_dump(path: Path) -> list[Element]:
    document = json.loads(path.read_text(encoding="utf-8"))
    elements = []
    for data in document["elements"]:
        rows = None
        if "rows" in data:
            rows = tuple(
                Row(r["header"], tuple(Cell(t, cs, rs) for t, cs, rs in r["cells"]))
                for r in data["rows"]
            )
        elements.append(
            Element(
                data["type"],
                data["text"],
                data["parent"],
                data.get("level"),
                data["source_type"],
                rows,
            )
        )
    return elements


class NetworkGuardTripped(RuntimeError):
    pass


@dataclass
class NetworkGuard:
    trips: list[str] = field(default_factory=list)
    _saved: dict[tuple[object, str], object] = field(default_factory=dict)

    def restore(self) -> None:
        for (owner, name), original in self._saved.items():
            setattr(owner, name, original)
        self._saved.clear()


_GUARDED = (
    (socket.socket, "connect"),
    (socket.socket, "connect_ex"),
    (socket, "create_connection"),
    (socket, "getaddrinfo"),
    (socket, "gethostbyname"),
    (socket, "gethostbyname_ex"),
)


def install_network_guard() -> NetworkGuard:
    """Make every socket connection or name lookup raise, and record it.

    Libraries sometimes swallow exceptions, so a trip is recorded before raising and the
    runner checks ``trips`` after parsing: any trip voids the run.
    """
    guard = NetworkGuard()

    def blocked(name: str) -> Callable[..., object]:
        def _raise(*args: object, **kwargs: object) -> object:
            guard.trips.append(name)
            raise NetworkGuardTripped(f"network use blocked during parsing: {name}")

        return _raise

    for owner, name in _GUARDED:
        guard._saved[(owner, name)] = getattr(owner, name)
        setattr(owner, name, blocked(f"{getattr(owner, '__name__', owner)}.{name}"))
    return guard


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def run_adapter(
    parse: Callable[[str], list[Element]],
    *,
    library: str | None,
    argv: list[str] | None = None,
) -> int:
    """Shared adapter entry point: guard, decode, parse, validate, write dump and sidecar.

    ``parse`` imports its library inside the function, so the guard is in place first.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    args = parser.parse_args(argv)

    guard = install_network_guard()
    decoded = decode_html_bytes(args.input.read_bytes())
    sidecar: dict = {
        "python": platform.python_version(),
        "encoding": decoded.encoding,
        "encoding_basis": decoded.basis,
        "library": library,
        "library_version": importlib.metadata.version(library) if library else None,
    }
    status, code = "ok", EXIT_OK
    started = time.perf_counter()
    try:
        elements = parse(decoded.text)
        validate_elements(elements)
    except Exception as exc:  # noqa: BLE001 - a crash is a result to record
        status, code = "crash", EXIT_CRASH
        sidecar["error"] = f"{type(exc).__name__}: {exc}"
    sidecar["parse_seconds"] = round(time.perf_counter() - started, 4)
    guard.restore()
    if guard.trips:
        status, code = "void_network", EXIT_NETWORK
        sidecar["guard_trips"] = guard.trips
    sidecar["status"] = status
    if code == EXIT_OK:
        sidecar["elements"] = len(elements)
        _write_atomic(args.output, dump_bytes(elements))
    _write_atomic(
        args.sidecar, (json.dumps(sidecar, indent=2, sort_keys=True) + "\n").encode()
    )
    return code
