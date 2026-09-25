"""Copy approved discovery responses into the fixture corpus and write its manifest.

    uv run --locked --all-packages python expirements/parser-fidelity/promote_fixtures.py

Reads the user's approval (expirements/parser-fidelity/approval.toml) and the discovery
records (data/raw/discovery/candidates.jsonl). Each approved exhibit is copied
byte-for-byte into tests/fixtures/releases/<fixture_id>/source.html after its sha256 is
checked against the saved response metadata, so the recorded class tests ran on exactly
the committed bytes. Development releases are copied to data/raw/devset/ and never
committed. Standard library only.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import tomllib
from pf_paths import DEVSET, DISCOVERY, FIXTURES, HARNESS, MAX_FIXTURE_BYTES
from pf_toml import Bare, toml_value

APPROVAL = HARNESS / "approval.toml"
PRIMARY_CLASSES = ("clean_html", "malformed_layout", "table_heavy", "narrative_only")
FIXTURES_PER_CLASS = 2
SOURCE_ID = "sec-edgar"
REDISTRIBUTION_BASIS = (
    "docs/source-register.toml entry sec-edgar: the SEC's quoted website reuse policy. That policy "
    "does not address issuers' copyright in their filings; the register draws no conclusion about it."
)
PILOT_SPLIT = "train_or_exclude"


class PromotionError(ValueError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _meta(source: Path) -> dict:
    return json.loads(
        source.with_name(source.name + ".meta.json").read_text(encoding="utf-8")
    )


def check_approval(approval: dict, candidates: dict[str, dict]) -> None:
    fixtures = approval.get("fixtures", [])
    devset = [entry["fixture_id"] for entry in approval.get("devset", [])]
    short = set(approval.get("short_classes", []))
    problems = []
    for entry in fixtures:
        fid, cls = entry["fixture_id"], entry["primary_class"]
        record = candidates.get(fid)
        if record is None:
            problems.append(f"{fid}: not among the discovery candidates")
            continue
        if cls not in PRIMARY_CLASSES:
            problems.append(f"{fid}: unknown primary_class {cls!r}")
        elif not record["class_tests"][cls]:
            problems.append(f"{fid}: class tests do not support primary_class {cls!r}")
        if not record["within_size_cap"]:
            problems.append(f"{fid}: exceeds the 1 MiB cap")
    per_class = Counter(entry["primary_class"] for entry in fixtures)
    for cls in PRIMARY_CLASSES:
        expected = 1 if cls in short else FIXTURES_PER_CLASS
        if per_class[cls] != expected:
            problems.append(
                f"class {cls}: {per_class[cls]} fixtures approved, expected {expected}"
            )
    per_issuer = Counter(
        candidates[e["fixture_id"]]["cik"]
        for e in fixtures
        if e["fixture_id"] in candidates
    )
    problems += [
        f"issuer {cik}: {n} fixtures (at most 2)"
        for cik, n in per_issuer.items()
        if n > 2
    ]
    listed = {
        "fixtures": [entry["fixture_id"] for entry in fixtures],
        "development set": devset,
    }
    for where, ids in listed.items():
        problems += [
            f"{fid}: listed {n} times in the {where}"
            for fid, n in sorted(Counter(ids).items())
            if n > 1
        ]
    if not 2 <= len(devset) <= 3:
        problems.append(
            f"development set has {len(devset)} releases; approve two or three"
        )
    overlap = set(devset) & {entry["fixture_id"] for entry in fixtures}
    problems += [
        f"{fid}: in both the fixtures and the development set"
        for fid in sorted(overlap)
    ]
    problems += [
        f"{fid}: development release not among the discovery candidates"
        for fid in devset
        if fid not in candidates
    ]
    if problems:
        raise PromotionError("\n".join(problems))


def _copy_verified(source: Path, dest: Path) -> dict:
    meta = _meta(source)
    if _sha256(source) != meta["sha256"] or source.stat().st_size != meta["bytes"]:
        raise PromotionError(
            f"{source}: bytes do not match the saved response metadata"
        )
    if dest.exists():
        if _sha256(dest) != meta["sha256"]:
            raise PromotionError(
                f"{dest} exists with different bytes; refusing to overwrite"
            )
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    if _sha256(dest) != meta["sha256"]:
        raise PromotionError(f"{dest}: copy does not match the saved response")
    return meta


def manifest_entry(record: dict, primary_class: str, meta: dict) -> list[str]:
    flags = []
    if record["class_tests"]["narrative_only"]:
        flags.append("narrative_only_release")
    if record["exhibit_type"].strip().upper() != "EX-99.1":
        flags.append("alternative_exhibit_numbering")
    fields: list[tuple[str, object]] = [
        ("fixture_id", record["fixture_id"]),
        ("primary_class", primary_class),
        ("issuer_name", record["issuer_name"]),
        ("cik", record["cik"]),
        ("accession", record["accession"]),
        ("form", record["form"]),
        ("items", record["items"]),
        ("filing_date", Bare(record["filing_date"])),
        ("exhibit_type", record["exhibit_type"]),
        ("exhibit_filename", record["exhibit_filename"]),
        ("url", meta["url"]),
        ("retrieved_at", Bare(meta["retrieved_at"])),
        ("http_status", meta["http_status"]),
        ("content_type", meta["content_type"]),
        ("bytes", meta["bytes"]),
        ("sha256", meta["sha256"]),
        ("source_id", SOURCE_ID),
        ("redistribution_basis", REDISTRIBUTION_BASIS),
        ("acquisition_flags", flags),
        ("pilot_split", PILOT_SPLIT),
    ]
    lines = ["[[fixtures]]"] + [f"{key} = {toml_value(value)}" for key, value in fields]
    lines += ["", "[fixtures.class_tests]"]
    lines += [
        f"{key} = {toml_value(value)}" for key, value in record["class_tests"].items()
    ]
    return lines


def promote(
    approval_path: Path = APPROVAL,
    discovery: Path = DISCOVERY,
    fixtures_root: Path = FIXTURES,
    devset_root: Path = DEVSET,
) -> list[str]:
    approval = tomllib.loads(approval_path.read_text(encoding="utf-8"))
    lines = (discovery / "candidates.jsonl").read_text(encoding="utf-8").splitlines()
    candidates = {
        record["fixture_id"]: record
        for record in map(json.loads, filter(str.strip, lines))
    }
    check_approval(approval, candidates)

    manifest = [
        "# Provenance for the Stage 1 release fixtures (specs/release-parser-fidelity.md).",
        "# Generated by expirements/parser-fidelity/promote_fixtures.py from approval.toml.",
        "schema_version = 1",
        "",
    ]
    for entry in sorted(approval["fixtures"], key=lambda e: e["fixture_id"]):
        fid = entry["fixture_id"]
        meta = _copy_verified(
            discovery / fid / "source.html", fixtures_root / fid / "source.html"
        )
        if meta["bytes"] > MAX_FIXTURE_BYTES:
            raise PromotionError(f"{fid}: {meta['bytes']} bytes exceeds the 1 MiB cap")
        manifest += manifest_entry(candidates[fid], entry["primary_class"], meta) + [""]
    for entry in approval.get("devset", []):
        fid = entry["fixture_id"]
        source = discovery / fid / "source.html"
        dest = devset_root / fid / "source.html"
        _copy_verified(source, dest)
        shutil.copyfile(
            source.with_name("source.html.meta.json"),
            dest.with_name("source.html.meta.json"),
        )
    text = "\n".join(manifest).rstrip("\n") + "\n"
    tomllib.loads(text)  # the generated manifest must parse
    (fixtures_root / "manifest.toml").write_text(text, encoding="utf-8")
    return sorted(entry["fixture_id"] for entry in approval["fixtures"])


def main() -> int:
    try:
        promoted = promote()
    except PromotionError as exc:
        print(f"approval rejected:\n{exc}", file=sys.stderr)
        return 1
    print(f"promoted {len(promoted)} fixtures: {', '.join(promoted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
