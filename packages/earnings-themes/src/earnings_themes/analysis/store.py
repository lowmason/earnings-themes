"""Immutable analytical publication; external artifacts remain explicit inputs."""

import io
import os
import shutil
import tempfile
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote as urlquote
from urllib.parse import urlsplit, urlunsplit

import polars as pl
from earnings_core import TextSpan, canonical_json, digest, make_locator, sha256_hex

from .consume import reverify_analysis_inputs
from .prevalence import build_analysis
from .problems import AnalysisError
from .records import (
    TABLE_SCHEMAS,
    AnalysisInputs,
    AnalysisPolicy,
    AnalysisRun,
    AnalysisRunRecord,
    AnalysisTables,
    EvidenceViewReference,
    StoredAnalysisRun,
    ThemeFamilyMap,
    validate_analysis_tables,
)

PUBLICATION_FIELDS = frozenset({"table_hashes", "evidence_hashes"})


def _require(condition, reason="storage_corrupt"):
    if not condition:
        raise AnalysisError(reason)


def _record_content(record):
    return {
        k: v
        for k, v in record.model_dump(mode="json").items()
        if k not in PUBLICATION_FIELDS
    }


def analytical_content_hash(result):
    """Publication hashes/evidence are excluded; every original table row is bound."""
    return digest(
        {
            "record": _record_content(result.record),
            "tables": {
                name: frame.to_dicts()
                for name, frame in result.tables.frames.items()
                if name != "evidence"
            },
        }
    )


def _confined_path(path):
    _require(isinstance(path, Path))
    _require(not any(p.is_symlink() for p in (path, *path.parents)))


@contextmanager
def new_run_directory(
    directory: Path, *, destination_reason="analysis_destination_exists"
):
    """Own only one new sibling; write manifest last and rename once."""
    partial = None
    try:
        _confined_path(directory)
        if directory.exists():
            raise FileExistsError(destination_reason)
        directory.parent.mkdir(parents=True, exist_ok=True)
        partial = Path(
            tempfile.mkdtemp(dir=directory.parent, prefix="." + directory.name + "-")
        )
        yield partial
        _confined_path(directory)
        if directory.exists():
            raise FileExistsError(destination_reason)
        os.rename(partial, directory)
    finally:
        if partial is not None and partial.exists():
            shutil.rmtree(partial, ignore_errors=True)


def _checked_evidence(evidence, bound):
    _require(type(evidence) is tuple, "input_changed")
    seen = set()
    quotes = {
        (q.span.doc_id, q.quote_id): q for q in bound.inputs.sources.stored_run.quotes
    }
    metadata = {m.doc_id: m for m in bound.metadata}
    bundles = {b.document.doc_id: b for b in bound.inputs.sources.bundles}
    snapshots = {s.doc_id: s for s in bound.inputs.canonical_snapshots}
    raw = {s.doc_id: s for s in bound.inputs.raw_snapshots}
    checked = []
    for value in evidence:
        ref = EvidenceViewReference.model_validate_json(
            canonical_json(value.model_dump(mode="json"))
        )
        key = (ref.doc_id, ref.quote_id)
        _require(key not in seen and key in quotes, "input_changed")
        seen.add(key)
        quote, meta, bundle = quotes[key], metadata[ref.doc_id], bundles[ref.doc_id]
        span = quote.span
        identity = digest(
            (
                ref.doc_id,
                ref.quote_id,
                span.canonical_hash,
                span.start,
                span.end,
                span.validator_version,
            )
        )
        locator = make_locator(
            bundle.document, TextSpan(start=span.start, end=span.end)
        )
        plain = urlunsplit(urlsplit(meta.source_url)._replace(fragment=""))
        _require(
            (
                ref.evidence_id,
                ref.anchor_id,
                ref.canonical_hash,
                ref.start,
                ref.end,
                ref.validator_version,
                ref.element_id,
                ref.mask_ids,
                ref.locator_hash,
                ref.quote_text_hash,
                ref.source_url,
                ref.rights_status,
                ref.rights_basis,
            )
            == (
                "evidence-" + identity,
                "p-" + identity,
                span.canonical_hash,
                span.start,
                span.end,
                span.validator_version,
                span.element_id,
                quote.mask_ids,
                digest(locator),
                sha256_hex(
                    bundle.document.canonical_text[span.start : span.end].encode()
                ),
                plain,
                meta.rights_status,
                meta.rights_basis,
            ),
            "input_changed",
        )
        nested = bundle.document.text_artifact
        permitted = (
            meta.retain_text
            and meta.access_status == "available"
            and (
                ref.audience == "local"
                or meta.export_text
                and meta.rights_status.value == "redistributable"
            )
            and (
                nested is None
                or nested.rights_status.value == "redistributable"
                or ref.audience == "local"
                and nested.rights_status.value == "local_only"
            )
        )
        _require((ref.status == "available") == permitted, "input_changed")
        if permitted:
            encode = lambda value: urlquote(value, safe="").replace("-", "%2D")
            directive = (
                "#:~:text="
                + (encode(locator.prefix) + "-," if locator.prefix else "")
                + encode(locator.exact)
                + (",-" + encode(locator.suffix) if locator.suffix else "")
            )
            _require(ref.source_fragment_url == plain + directive, "input_changed")
            _require(
                ref.canonical_artifact is not None
                and ref.canonical_artifact.media_type == "application/json"
                and ref.canonical_artifact.matches(snapshots[ref.doc_id].data)
                and ref.view_artifact is not None
                and ref.view_artifact.media_type == "text/html; charset=utf-8",
                "input_changed",
            )
            for artifact, folder, suffix in (
                (ref.canonical_artifact, "canonical", ".json"),
                (ref.view_artifact, "views", ".html"),
            ):
                _require(
                    artifact.storage_ref
                    == folder + "/" + artifact.content_sha256 + suffix,
                    "input_changed",
                )
            expected_reason = (
                "raw_snapshot_missing"
                if meta.retain_raw and ref.doc_id not in raw
                else "snapshot_withheld"
                if not (
                    meta.retain_raw and (ref.audience == "local" or meta.export_raw)
                )
                else None
            )
            _require(ref.reason == expected_reason, "input_changed")
            if ref.raw_artifact is not None:
                _require(
                    ref.doc_id in raw
                    and ref.raw_artifact == raw[ref.doc_id].artifact
                    and ref.raw_artifact.matches(raw[ref.doc_id].data),
                    "input_changed",
                )
            elif expected_reason is None:
                raise AnalysisError("input_changed")
        checked.append(ref)
    return tuple(sorted(checked, key=lambda r: r.evidence_id))


def _check_record_tables(record, tables):
    frames = tables.frames
    book = record.codebook.model_dump(mode="python")
    assignment_policy = (
        record.assignment_policy.model_dump(mode="python")
        if record.assignment_policy
        else None
    )
    _require(
        set(frames["coverage"]["event_id"]) == set(record.analysis_policy.event_ids)
    )
    _require(
        all(
            row["policy_scope"] == record.scope
            for row in frames["coverage"].iter_rows(named=True)
        )
    )
    for name in ("classifications", "decisions", "novelty", "completions"):
        _require(
            all(row["codebook"] == book for row in frames[name].iter_rows(named=True))
        )
    _require(
        all(
            row["policy"] == assignment_policy
            for row in frames["decisions"].iter_rows(named=True)
        )
    )
    _require(
        all(
            row["assignment_policy"] == assignment_policy
            and row["analysis_policy_hash"] == record.analysis_policy.content_hash
            for row in frames["completions"].iter_rows(named=True)
        )
    )
    for name in ("quotes", "observations"):
        _require(
            all(
                row["validator_version"] == record.validator_version
                and row["source_run_hash"] == record.source_run_hash
                for row in frames[name].iter_rows(named=True)
            )
        )
    _require(
        all(
            row["source_run_hash"] == record.source_run_hash
            for row in frames["claims"].iter_rows(named=True)
        )
    )
    for row in frames["observations"].iter_rows(named=True):
        _require(record.assignment_policy is not None)
        _require(
            (
                row["codebook_id"],
                row["codebook_version"],
                row["codebook_hash"],
                row["coding_run_hash"],
                row["support_run_hash"],
                row["policy_kind"],
                row["policy_hash"],
                row["policy_scope"],
            )
            == (
                record.codebook.codebook_id,
                record.codebook.codebook_version,
                record.codebook.content_hash,
                record.coding_run_hash,
                record.support_run_hash,
                record.assignment_policy.kind,
                record.assignment_policy.policy_hash,
                record.scope,
            )
        )
    for row in frames["prevalence"].iter_rows(named=True):
        _require(
            (
                row["population_hash"],
                row["codebook_id"],
                row["codebook_version"],
                row["codebook_hash"],
                row["analysis_policy_hash"],
                row["policy_scope"],
            )
            == (
                record.population_hash,
                record.codebook.codebook_id,
                record.codebook.codebook_version,
                record.codebook.content_hash,
                record.analysis_policy.content_hash,
                record.scope,
            )
        )
        _require(
            row["family_map_hash"]
            == (
                record.family_map.content_hash
                if row["view_kind"] == "family" and record.family_map
                else None
            )
        )
    releases = list(
        frames["coverage"].filter(pl.col("doc_type") == "release").iter_rows(named=True)
    )
    _require(
        record.counts_by_state
        == tuple(sorted(Counter(r["latest_state"] for r in releases).items()))
    )
    _require(
        record.counts_by_reason
        == tuple(
            sorted(
                Counter(
                    reason for r in releases for reason in r["missing_reasons"]
                ).items()
            )
        )
    )
    _require(
        record.counts_by_decision
        == tuple(sorted(Counter(frames["decisions"]["status"]).items()))
    )
    for name, bindings in (
        ("completions", record.completion_hashes),
        ("copies", record.copy_hashes),
    ):
        _require(
            bindings
            == tuple(
                sorted(
                    (r["doc_id"], digest(r)) for r in frames[name].iter_rows(named=True)
                )
            )
        )
    _require(set(dict(record.documents)) == set(frames["completions"]["doc_id"]))
    _require(
        all(
            dict(record.documents).get(r["doc_id"]) == r["canonical_hash"]
            for r in frames["quotes"].iter_rows(named=True)
        )
    )
    refs = tuple(
        EvidenceViewReference.model_validate_json(canonical_json(r))
        for r in frames["evidence"].to_dicts()
    )
    _require(
        record.evidence_hashes
        == tuple(
            sorted((r.evidence_id, digest(r.model_dump(mode="json"))) for r in refs)
        )
    )


def write_analysis_run(
    directory: Path,
    result: AnalysisRun,
    inputs: AnalysisInputs,
    policy: AnalysisPolicy,
    families: ThemeFamilyMap | None,
    evidence: tuple[EvidenceViewReference, ...],
) -> Path:
    """Rebuild current analytical content before publishing any bytes."""
    try:
        _require(type(result) is AnalysisRun, "input_changed")
        current = build_analysis(inputs, policy, families)
        _require(
            analytical_content_hash(current) == analytical_content_hash(result),
            "input_changed",
        )
        refs = _checked_evidence(evidence, reverify_analysis_inputs(inputs))
        frames = dict(current.tables.frames)
        frames["evidence"] = pl.DataFrame(
            [r.model_dump(mode="python") for r in refs],
            schema=TABLE_SCHEMAS["evidence"],
        )
        tables = validate_analysis_tables(AnalysisTables(frames))
        _require(
            analytical_content_hash(build_analysis(inputs, policy, families))
            == analytical_content_hash(current),
            "input_changed",
        )
        with new_run_directory(directory) as temporary:
            hashes = []
            for name, frame in tables.frames.items():
                path = temporary / (name + ".parquet")
                frame.write_parquet(path)
                hashes.append((path.name, sha256_hex(path.read_bytes())))
            record = AnalysisRunRecord.model_validate_json(
                canonical_json(
                    current.record.model_dump(mode="json")
                    | {
                        "table_hashes": sorted(hashes),
                        "evidence_hashes": sorted(
                            (r.evidence_id, digest(r.model_dump(mode="json")))
                            for r in refs
                        ),
                    }
                )
            )
            _check_record_tables(record, tables)
            (temporary / "run.json").write_bytes(
                canonical_json(record.model_dump(mode="json"))
            )
        return directory
    except FileExistsError as error:
        if str(error) == "analysis_destination_exists":
            raise FileExistsError("analysis_destination_exists") from None
        raise AnalysisError("storage_corrupt") from None
    except AnalysisError as error:
        raise AnalysisError(error.reason) from None
    except Exception:  # noqa: BLE001 - never expose source or filesystem diagnostics
        raise AnalysisError("storage_corrupt") from None


def read_analysis_run(directory: Path) -> StoredAnalysisRun:
    """Structural read: exact schemas, confined files, byte hashes, rows and counts."""
    try:
        _confined_path(directory)
        manifest = directory / "run.json"
        _confined_path(manifest)
        payload = manifest.read_bytes()
        record = AnalysisRunRecord.model_validate_json(payload)
        expected = {name + ".parquet" for name in TABLE_SCHEMAS}
        _require(set(dict(record.table_hashes)) == expected)
        _require({p.name for p in directory.iterdir()} == expected | {"run.json"})
        frames = {}
        for name in TABLE_SCHEMAS:
            path = directory / (name + ".parquet")
            _confined_path(path)
            data = path.read_bytes()
            _require(sha256_hex(data) == dict(record.table_hashes)[path.name])
            frames[name] = pl.read_parquet(io.BytesIO(data))
        tables = validate_analysis_tables(AnalysisTables(frames))
        _check_record_tables(record, tables)
        return StoredAnalysisRun(
            record, tables, sha256_hex(payload), record.table_hashes
        )
    except Exception:  # noqa: BLE001 - closed corruption reason includes invalid paths
        raise AnalysisError("storage_corrupt") from None


def reverify_analysis_run(
    stored: StoredAnalysisRun,
    inputs: AnalysisInputs,
    policy: AnalysisPolicy,
    families: ThemeFamilyMap | None,
) -> None:
    """Structural validity does not replace current sources, masks or pure policy."""
    try:
        _require(type(stored) is StoredAnalysisRun, "input_changed")
        record = AnalysisRunRecord.model_validate_json(
            canonical_json(stored.record.model_dump(mode="json"))
        )
        tables = validate_analysis_tables(stored.tables)
        _check_record_tables(record, tables)
        _require(
            stored.manifest_hash
            == sha256_hex(canonical_json(record.model_dump(mode="json")))
            and stored.published_hashes == record.table_hashes,
            "input_changed",
        )
        current = build_analysis(inputs, policy, families)
        _require(
            analytical_content_hash(current) == analytical_content_hash(stored),
            "input_changed",
        )
        refs = tuple(
            EvidenceViewReference.model_validate_json(canonical_json(r))
            for r in tables.frames["evidence"].to_dicts()
        )
        _checked_evidence(refs, reverify_analysis_inputs(inputs))
        _require(
            analytical_content_hash(build_analysis(inputs, policy, families))
            == analytical_content_hash(current),
            "input_changed",
        )
    except AnalysisError:
        raise AnalysisError("input_changed") from None
    except Exception:  # noqa: BLE001 - callback and material diagnostics are private
        raise AnalysisError("input_changed") from None
