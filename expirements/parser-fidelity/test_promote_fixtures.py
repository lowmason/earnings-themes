import hashlib
import json
import re

import pytest
import tomllib
from pf_toml import toml_value
from promote_fixtures import PromotionError, promote

CLASSES = ("clean_html", "malformed_layout", "table_heavy", "narrative_only")


def write_candidate(discovery, fid, cik, cls, exhibit_type="EX-99.1"):
    body = f"<html><body><p>{fid}</p></body></html>".encode()
    folder = discovery / fid
    folder.mkdir(parents=True)
    (folder / "source.html").write_bytes(body)
    meta = {
        "url": f"https://www.sec.gov/Archives/{fid}.htm",
        "retrieved_at": "2026-09-23T10:00:00Z",
        "http_status": 200,
        "content_type": "text/html",
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    (folder / "source.html.meta.json").write_text(json.dumps(meta))
    tests = {name: name == cls for name in CLASSES}
    tests["clean_html"] = cls != "malformed_layout"
    tests["malformed_layout"] = cls == "malformed_layout"
    tests["data_table_share"] = 0.61
    return {
        "fixture_id": fid,
        "cik": cik,
        "issuer_name": f"Issuer {cik}",
        "accession": fid.split("_")[0],
        "agent": fid[:10],
        "form": "8-K",
        "items": "2.02,9.01",
        "filing_date": "2025-01-30",
        "exhibit_type": exhibit_type,
        "exhibit_filename": "ex99.htm",
        "exhibit_description": "PRESS RELEASE",
        "url": meta["url"],
        "year": 2025,
        "quarter": 1,
        "within_size_cap": True,
        "class_tests": tests,
    }


@pytest.fixture
def layout(tmp_path):
    discovery = tmp_path / "discovery"
    records, approval = [], ['approved_by = "Tester"', "approved_on = 2026-09-24", ""]
    for number in range(10):
        cls = CLASSES[number % 4]
        fid = f"000000000{number}-25-00000{number}_ex-99-1"
        records.append(write_candidate(discovery, fid, cik=f"{number:010d}", cls=cls))
        if number < 8:
            approval += [
                "[[fixtures]]",
                f'fixture_id = "{fid}"',
                f'primary_class = "{cls}"',
                "",
            ]
        else:
            approval += ["[[devset]]", f'fixture_id = "{fid}"', ""]
    (discovery / "candidates.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in records)
    )
    approval_path = tmp_path / "approval.toml"
    approval_path.write_text("\n".join(approval))
    return tmp_path, discovery, approval_path


def run(layout):
    root, discovery, approval_path = layout
    return promote(approval_path, discovery, root / "fixtures", root / "devset")


def test_promote_copies_bytes_and_writes_a_parsable_manifest(layout):
    root, discovery, _ = layout
    promoted = run(layout)
    assert len(promoted) == 8
    manifest = tomllib.loads((root / "fixtures" / "manifest.toml").read_text())
    entry = manifest["fixtures"][0]
    fid = entry["fixture_id"]
    assert (root / "fixtures" / fid / "source.html").read_bytes() == (
        discovery / fid / "source.html"
    ).read_bytes()
    assert entry["cik"] == "0000000000"
    assert entry["source_id"] == "sec-edgar"
    assert entry["pilot_split"] == "train_or_exclude"
    assert str(entry["filing_date"]) == "2025-01-30"
    assert entry["retrieved_at"].tzinfo is not None
    assert entry["class_tests"]["data_table_share"] == 0.61
    assert sorted(p.name for p in (root / "devset").iterdir()) == sorted(
        f"000000000{n}-25-00000{n}_ex-99-1" for n in (8, 9)
    )


def test_promote_is_idempotent(layout):
    assert run(layout) == run(layout)


def test_stage4_flags(layout):
    root = layout[0]
    run(layout)
    flags = {
        e["primary_class"]: e["stage4_flags"]
        for e in tomllib.loads((root / "fixtures" / "manifest.toml").read_text())[
            "fixtures"
        ]
    }
    assert flags["narrative_only"] == ["narrative_only_release"]
    assert flags["table_heavy"] == []


def test_wrong_class_count_and_mismatched_class_are_rejected(layout):
    approval_path = layout[2]
    text = approval_path.read_text().replace(
        'primary_class = "table_heavy"', 'primary_class = "clean_html"', 1
    )
    approval_path.write_text(text)
    with pytest.raises(PromotionError) as excinfo:
        run(layout)
    message = str(excinfo.value)
    assert "class table_heavy: 1 fixtures approved, expected 2" in message
    assert (
        "class tests do not support primary_class 'clean_html'" not in message
    )  # table-heavy fixtures here are clean


@pytest.mark.parametrize(
    ("replaced", "kept", "where"),
    [
        # Same class, so the per-class and per-issuer counts still pass.
        ("0000000004-25-000004_ex-99-1", "0000000000-25-000000_ex-99-1", "fixtures"),
        # Still two entries, so the two-or-three count still passes.
        (
            "0000000009-25-000009_ex-99-1",
            "0000000008-25-000008_ex-99-1",
            "development set",
        ),
    ],
)
def test_an_id_listed_twice_is_rejected(layout, replaced, kept, where):
    approval_path = layout[2]
    approval_path.write_text(approval_path.read_text().replace(replaced, kept))
    with pytest.raises(
        PromotionError, match=re.escape(f"{kept}: listed 2 times in the {where}")
    ):
        run(layout)


def test_tampered_bytes_are_rejected(layout):
    _, discovery, _ = layout
    victim = discovery / "0000000000-25-000000_ex-99-1" / "source.html"
    victim.write_bytes(victim.read_bytes() + b" ")
    with pytest.raises(PromotionError, match="do not match"):
        run(layout)


def test_toml_value_escapes_strings():
    assert (
        tomllib.loads("x = " + toml_value('A "quoted" \\ name\n'))["x"]
        == 'A "quoted" \\ name\n'
    )
