"""Audience-specific cited HTML bundles, separate from immutable analysis runs."""

import html
import json
from pathlib import Path
from typing import Literal

from earnings_core import canonical_json, digest, sha256_hex
from earnings_themes.analysis import (
    AnalysisError,
    AnalysisInputs,
    AnalysisPolicy,
    EvidenceView,
    StoredAnalysisRun,
    ThemeFamilyMap,
    reverify_analysis_inputs,
    reverify_analysis_run,
)
from earnings_themes.analysis.records import AnalysisPart
from earnings_themes.analysis.store import new_run_directory
from earnings_themes.coding.records import PolicyReference
from earnings_themes.records import NonBlank, Sha256Hex
from earnings_themes.support.records import CodebookReference
from pydantic import AwareDatetime, model_validator

from .evidence_views import make_evidence_view

Limit = Literal[
    "rights_restricted",
    "snapshot_withheld",
    "capture_not_supplied",
    "browser_observation_not_supplied",
    "raw_cache_not_supplied",
    "raw_cache_not_bound",
]


class ReportManifest(AnalysisPart):
    report_id: NonBlank
    created_at: AwareDatetime
    audience: Literal["local", "export"]
    scope: Literal["fixture", "research"]
    analysis_manifest_hash: Sha256Hex
    binding_hash: Sha256Hex
    codebook: CodebookReference
    assignment_policy: PolicyReference | None
    analysis_policy: AnalysisPolicy
    family_map: ThemeFamilyMap | None
    artifact_hashes: tuple[tuple[NonBlank, Sha256Hex], ...]
    evidence_ids: tuple[NonBlank, ...]
    limitations: tuple[Limit, ...]

    @model_validator(mode="after")
    def _bindings(self):
        if (
            self.scope != self.analysis_policy.scope
            or (
                self.assignment_policy is not None
                and (
                    self.assignment_policy.codebook != self.codebook
                    or self.assignment_policy.kind == "fixture"
                    and self.scope != "fixture"
                )
            )
            or (
                self.family_map is not None
                and self.family_map.codebook != self.codebook
            )
        ):
            raise ValueError("policy_mismatch")
        for value in (
            self.analysis_manifest_hash,
            self.binding_hash,
            *(h for _, h in self.artifact_hashes),
        ):
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("invalid_hash")
        names = tuple(n for n, _ in self.artifact_hashes)
        if names != tuple(sorted(set(names))) or "report.html" not in names:
            raise ValueError("invalid_artifacts")
        for name in names:
            if name == "report.html":
                continue
            parts = name.split("/")
            if (
                len(parts) != 2
                or parts[0] != "artifacts"
                or not parts[1].startswith(dict(self.artifact_hashes)[name] + ".")
            ):
                raise ValueError("invalid_artifacts")
        if self.limitations != tuple(sorted(set(self.limitations))):
            raise ValueError("invalid_limitations")
        if self.evidence_ids != tuple(sorted(set(self.evidence_ids))):
            raise ValueError("invalid_evidence")
        return self


def _escape(value):
    if value is None:
        value = "unknown"
    if isinstance(value, (list, tuple)):
        value = ", ".join(str(v) for v in value)
    return html.escape(str(value), quote=True)


def _table(rows, columns):
    return (
        "<table><thead><tr>"
        + "".join("<th>" + _escape(c) + "</th>" for c in columns)
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>"
            + "".join("<td>" + _escape(r[c]) + "</td>" for c in columns)
            + "</tr>"
            for r in rows
        )
        + "</tbody></table>"
    )


def _link(url, label):
    return '<a href="' + _escape(url) + '">' + _escape(label) + "</a>"


def _artifact_name(artifact, suffix):
    return "artifacts/" + artifact.content_sha256 + suffix


def _checked_views(views, stored, inputs, audience):
    if type(views) is not tuple or audience not in ("local", "export"):
        raise AnalysisError("input_changed")
    bound = reverify_analysis_inputs(inputs)
    snapshots = {s.doc_id: s for s in inputs.raw_snapshots}
    current = {}
    for view in views:
        if type(view) is not EvidenceView:
            raise AnalysisError("input_changed")
        ref = view.reference
        key = (ref.doc_id, ref.quote_id)
        if key in current or ref.audience != audience:
            raise AnalysisError("input_changed")
        fresh = make_evidence_view(
            bound, *key, audience=audience, raw_snapshot=snapshots.get(ref.doc_id)
        )
        reference = ref.model_dump(mode="json") | {"capture_reference": None}
        if reference != fresh.reference.model_dump(mode="json") or (
            view.html,
            view.canonical_bytes,
            view.raw_bytes,
            view.retain_capture,
        ) != (fresh.html, fresh.canonical_bytes, fresh.raw_bytes, fresh.retain_capture):
            raise AnalysisError("input_changed")
        if fresh.reference.reason == "raw_snapshot_missing":
            raise AnalysisError("raw_snapshot_missing")
        current[key] = fresh
    required = {
        (r["doc_id"], r["quote_id"])
        for r in stored.tables.frames["observations"].iter_rows(named=True)
    }
    if not required <= set(current):
        raise AnalysisError("input_changed")
    return bound, current


def _included_artifacts(views):
    artifacts = {}
    for view in views.values():
        for data, ref, suffix in (
            (view.html, view.reference.view_artifact, ".html"),
            (view.canonical_bytes, view.reference.canonical_artifact, ".json"),
            (view.raw_bytes, view.reference.raw_artifact, ".source"),
        ):
            if ref is None:
                if data is not None:
                    raise AnalysisError("input_changed")
                continue
            if data is None or not ref.matches(data):
                raise AnalysisError("input_changed")
            # Immutable canonical JSON may contain source pointers. Never export
            # a local absolute path embedded in that otherwise permitted payload.
            if suffix == ".json":
                payload = json.loads(data)
                nested = payload["document"].get("text_artifact")
                if nested and (
                    Path(nested["storage_ref"]).is_absolute()
                    or ".." in Path(nested["storage_ref"]).parts
                ):
                    raise AnalysisError("input_changed")
            artifacts[_artifact_name(ref, suffix)] = data
    return artifacts


def _limitations(stored, views):
    limits = {"capture_not_supplied", "browser_observation_not_supplied"}
    limits.update(v.reference.reason for v in views.values() if v.reference.reason)
    limits.update(
        "raw_cache_" + v.status
        for v in stored.record.raw_verification
        if v.status != "verified"
    )
    return tuple(sorted(limits))


def _render(stored, bound, views, audience, limits):
    record, frames = stored.record, stored.tables.frames
    parts = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Evidence-linked themes</title><style>body{font-family:system-ui;margin:2rem;overflow-wrap:anywhere}table{border-collapse:collapse;margin:1rem 0}th,td{border:1px solid #bbb;padding:.4rem;text-align:left}blockquote{white-space:pre-wrap}</style></head><body><h1>Evidence-linked themes</h1>'
    ]
    parts.append(
        "<p>Population "
        + _escape(record.analysis_policy.population_id)
        + "; population hash "
        + _escape(record.population_hash)
        + "; scope "
        + _escape(record.scope)
        + "; audience "
        + _escape(audience)
        + "; codebook "
        + _escape(record.codebook.codebook_id)
        + " version "
        + _escape(record.codebook.codebook_version)
        + "; analysis policy "
        + _escape(record.analysis_policy.content_hash)
        + "; assignment policy "
        + _escape(
            record.assignment_policy.kind
            if record.assignment_policy
            else "calibration_required"
        )
        + ".</p>"
    )
    parts.append(
        "<p>Restricted selected population; release speaker role is not_applicable. Transcript coverage is separate and cannot support cross-document comparisons. Counts describe processing and disclosure presence; support precision, recall and configuration quality have not been evaluated.</p>"
    )
    parts.append(
        "<h2>Prevalence</h2>"
        + _table(
            frames["prevalence"].to_dicts(),
            (
                "period_end",
                "window_start",
                "window_end",
                "doc_type",
                "speaker_role",
                "view_kind",
                "view_id",
                "unit",
                "numerator",
                "denominator",
                "rate",
                "expected_count",
                "available_count",
                "parsed_count",
                "observable_count",
                "excluded_count",
                "missing_period_count",
                "restrictions",
                "reason",
                "policy_scope",
            ),
        )
    )
    parts.append(
        "<h2>Release and transcript coverage</h2>"
        + _table(
            frames["coverage"].to_dicts(),
            (
                "event_id",
                "entity_id",
                "cik",
                "period_end",
                "fiscal_year",
                "fiscal_quarter",
                "doc_type",
                "speaker_role",
                "availability",
                "available",
                "parsed",
                "observable",
                "latest_state",
                "missing_reasons",
                "accepted_count",
                "masked_count",
                "review_count",
                "rejected_count",
                "refused_count",
                "flagged_count",
                "incomplete_count",
                "unmatched_count",
                "policy_scope",
            ),
        )
    )
    parts.append(
        "<h2>Disclosure copies</h2>"
        + _table(
            frames["copies"].to_dicts(),
            ("doc_id", "disclosure_group", "representative_doc_id", "status"),
        )
    )
    parts.append(
        "<h2>Audit counts</h2><p>Classifications "
        + str(frames["classifications"].height)
        + "; decisions "
        + str(frames["decisions"].height)
        + "; novelty "
        + str(frames["novelty"].height)
        + "; rejections "
        + str(frames["rejections"].height)
        + ".</p>"
    )
    parts.append(
        "<h2>Limitations</h2><ul>"
        + "".join("<li>" + _escape(v) + "</li>" for v in limits)
        + "</ul><p>Withholding, missing cache material and unavailable browser observations are not negative theme observations. No capture bytes were supplied; no saved capture or browser highlight success is claimed. Screenshots remain local_only outside this bundle. Canonical views have static anchors and work offline without native text-fragment support.</p>"
    )
    documents = {b.document.doc_id: b.document for b in bound.inputs.sources.bundles}
    claims = {
        (r["doc_id"], r["claim_id"]): r for r in frames["claims"].iter_rows(named=True)
    }
    links = list(frames["assignment_claims"].iter_rows(named=True))
    parts.append(
        "<h2>Release state counts</h2>"
        + _table(
            [
                {"state": state, "count": count}
                for state, count in record.counts_by_state
            ],
            ("state", "count"),
        )
    )
    parts.append(
        "<h2>Release missing-reason counts</h2>"
        + _table(
            [
                {"reason": reason, "count": count}
                for reason, count in record.counts_by_reason
            ],
            ("reason", "count"),
        )
    )
    parts.append("<h2>Cited assignments</h2>")
    for row in frames["observations"].iter_rows(named=True):
        view = views[(row["doc_id"], row["quote_id"])]
        ref = view.reference
        parts.append(
            '<article id="'
            + _escape(ref.evidence_id + "-" + row["theme_id"])
            + '"><h3>'
            + _escape(row["theme_id"])
            + "</h3><p>"
            + _escape(row["doc_id"])
            + " / "
            + _escape(row["quote_id"])
            + "; hash "
            + _escape(ref.canonical_hash)
            + "; span ["
            + str(ref.start)
            + ","
            + str(ref.end)
            + "); masks "
            + _escape(ref.mask_ids)
            + ".</p>"
        )
        parts.append(
            "<p>Rights "
            + _escape(ref.rights_status.value)
            + "; basis "
            + _escape(ref.rights_basis)
            + "; published "
            + _escape(row["published_at"])
            + "; retrieved "
            + _escape(row["retrieved_at"])
            + "; extracted "
            + _escape(row["extracted_at"])
            + ".</p>"
        )
        if ref.status == "available":
            text = documents[row["doc_id"]].canonical_text[ref.start : ref.end]
            parts.append("<blockquote>" + _escape(text) + "</blockquote>")
            parts.append(
                "<p>"
                + _link(
                    _artifact_name(ref.view_artifact, ".html") + "#" + ref.anchor_id,
                    "Immutable canonical snapshot",
                )
                + " | "
                + _link(ref.source_fragment_url, "Source passage")
                + " | "
                + _link(
                    _artifact_name(ref.canonical_artifact, ".json"),
                    "Canonical artifact",
                )
            )
            if ref.raw_artifact:
                parts.append(
                    " | "
                    + _link(
                        _artifact_name(ref.raw_artifact, ".source"),
                        "Saved source snapshot",
                    )
                )
            parts.append("</p>")
            for link in links:
                if (
                    link["assignment_id"] == row["assignment_id"]
                    and link["doc_id"] == row["doc_id"]
                ):
                    claim = claims[(link["doc_id"], link["claim_id"])]
                    parts.append(
                        "<p>Model-derived interpretation ("
                        + _escape(claim["claim_id"])
                        + "): "
                        + _escape(claim["interpretation"])
                        + "; original quote links "
                        + _escape(claim["original_quote_ids"])
                        + ".</p>"
                    )
        else:
            parts.append(
                "<p>withheld / rights_restricted; quote and model-derived interpretation withheld. "
                + _link(ref.source_url, "Source")
                + "</p>"
            )
        parts.append("</article>")
    parts.append("</body></html>")
    return "".join(parts).encode("utf-8")


def write_theme_report(
    directory: Path,
    stored: StoredAnalysisRun,
    inputs: AnalysisInputs,
    policy: AnalysisPolicy,
    families: ThemeFamilyMap | None,
    views: tuple[EvidenceView, ...],
    *,
    audience: Literal["local", "export"],
) -> Path:
    """Reverify current analysis and regenerated evidence, then publish once."""
    try:
        reverify_analysis_run(stored, inputs, policy, families)
        bound, current = _checked_views(views, stored, inputs, audience)
        artifacts = _included_artifacts(current)
        limits = _limitations(stored, current)
        artifacts["report.html"] = _render(stored, bound, current, audience, limits)
        hashes = tuple(
            sorted((name, sha256_hex(data)) for name, data in artifacts.items())
        )
        record = stored.record
        manifest = ReportManifest.model_validate_json(
            canonical_json(
                {
                    "schema_version": 1,
                    "report_id": "report-"
                    + digest((stored.manifest_hash, audience, hashes)),
                    "created_at": record.created_at,
                    "audience": audience,
                    "scope": record.scope,
                    "analysis_manifest_hash": stored.manifest_hash,
                    "binding_hash": bound.binding_hash,
                    "codebook": record.codebook.model_dump(mode="json"),
                    "assignment_policy": record.assignment_policy.model_dump(
                        mode="json"
                    )
                    if record.assignment_policy
                    else None,
                    "analysis_policy": policy.model_dump(mode="json"),
                    "family_map": families.model_dump(mode="json")
                    if families
                    else None,
                    "artifact_hashes": hashes,
                    "evidence_ids": sorted(
                        v.reference.evidence_id for v in current.values()
                    ),
                    "limitations": limits,
                }
            )
        )
        reverify_analysis_run(stored, inputs, policy, families)
        if reverify_analysis_inputs(inputs).binding_hash != bound.binding_hash:
            raise AnalysisError("input_changed")
        with new_run_directory(
            directory, destination_reason="report_destination_exists"
        ) as temporary:
            for name, data in artifacts.items():
                path = temporary / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                if sha256_hex(path.read_bytes()) != dict(hashes)[name]:
                    raise AnalysisError("storage_corrupt")
            (temporary / "report.json").write_bytes(
                canonical_json(manifest.model_dump(mode="json"))
            )
        return directory
    except FileExistsError as error:
        if str(error) == "report_destination_exists":
            raise FileExistsError("report_destination_exists") from None
        raise AnalysisError("storage_corrupt") from None
    except AnalysisError as error:
        raise AnalysisError(error.reason) from None
    except Exception:  # noqa: BLE001 - no source-bearing exceptions enter diagnostics
        raise AnalysisError("storage_corrupt") from None
