"""Invented V5 static artifacts and explicitly user-only real capture gate.

No browser SDK is imported during collection. Artifact helpers are also exercised
by default fake tests; only the marked test inspects installed binaries.
"""

import html
import importlib
import json
import os
import tempfile
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import ArtifactRef, RightsStatus, canonical_json, sha256_hex
from earnings_ingestion.browser import ISOLATED_1, CaptureEnvironment, FakeRenderer
from earnings_pipeline.browser_evidence import capture_evidence_view

pytestmark = pytest.mark.browser
ROOT = Path("/private/tmp/earnings-stage10-v5/v1")
NATIVE = (
    "highlighted",
    "page_top",
    "not_highlighted",
    "wrong_occurrence",
    "failed",
    "unavailable",
)
FALLBACK = ("span_visible", "failed", "withheld")
CASES = (
    ("unique", "Invented unique passage.", 0),
    ("repeated", None, -1),
    ("astral", "😀 Invented 🛠 prefix.", -1),
    ("long-page", "Invented padding\r" * 100, -1),
    ("drift", "Invented source drift passage.", 0),
    ("no-text-fragment", "Invented fragment control.", 0),
)


def build_artifacts(root, work, monkeypatch):
    """Publish only invented, content-addressed static pages; never overwrite."""
    helpers = importlib.import_module(
        "apps.earnings-pipeline.tests.test_evidence_views"
    )
    cases = helpers.cases
    rows, views, artifacts = [], [], {}
    original = cases.metadata
    for case_id, first_text, quote_index in CASES:
        with monkeypatch.context() as patch:

            def metadata(bundle, expected, case_id=case_id):
                row, raw = original(bundle, expected)
                text = (
                    bundle.document.canonical_text
                    if case_id != "drift"
                    else "Invented changed saved page."
                )
                data = (
                    '<!doctype html><html><head><meta charset="utf-8"><title>Invented saved source</title></head><body><pre style="white-space:pre-wrap;max-width:48rem">'
                    + html.escape(text)
                    + "</pre></body></html>"
                ).encode()
                artifact = ArtifactRef.for_bytes(
                    data,
                    media_type="text/html",
                    storage_ref="invented/" + sha256_hex(data) + ".html",
                    rights_status=RightsStatus.REDISTRIBUTABLE,
                    rights_basis="Invented V5 fixture permission",
                )
                return row.model_copy(
                    update={
                        "raw_artifact": artifact,
                        "raw_hash": artifact.content_sha256,
                        "rights_basis": artifact.rights_basis,
                    }
                ), replace(raw, artifact=artifact, data=data)

            patch.setattr(cases, "metadata", metadata)
            bound = helpers.make_case(
                work / case_id,
                patch,
                first_text=first_text,
                metadata_changes={"retain_capture": True},
            )
            view = helpers.prepare(bound, quote_index=quote_index)
        ref = view.reference
        text = bound.inputs.sources.bundles[0].document.canonical_text
        source = sha256_hex(view.raw_bytes) + ".html"
        fallback = sha256_hex(view.html) + ".html"
        canonical = sha256_hex(view.canonical_bytes) + ".json"
        artifacts.update(
            {
                source: view.raw_bytes,
                fallback: view.html,
                canonical: view.canonical_bytes,
            }
        )
        row = {
            "case_id": case_id,
            "canonical_hash": ref.canonical_hash,
            "start": ref.start,
            "end": ref.end,
            "utf16_start": len(text[: ref.start].encode("utf-16-le")) // 2,
            "utf16_end": len(text[: ref.end].encode("utf-16-le")) // 2,
            "anchor_id": ref.anchor_id,
            "source_file": source,
            "source_artifact_hash": sha256_hex(view.raw_bytes),
            "fallback_file": fallback,
            "canonical_file": canonical,
            "saved_source_link": source
            + "#"
            + ref.source_fragment_url.partition("#")[2],
            "fallback_link": fallback + "#" + ref.anchor_id,
            "external_source_url": ref.source_url,
            "control_link": source if case_id == "no-text-fragment" else None,
            "tested_transport": "local_file",
            "https_behavior": "unverified",
            "native": "pending",
            "fallback": "pending",
            "capture": "pending",
            "failure_reason": None,
            "observer": None,
            "observed_at": None,
            "screenshot_artifact_ids": [],
        }
        rows.append(row)
        views.append(view)
    inventory = json.dumps(rows, sort_keys=True, indent=2).encode()
    key = sha256_hex(inventory)
    directory = root / key
    index_rows = []
    for row in rows:
        links = (
            '<a href="'
            + html.escape(row["saved_source_link"], quote=True)
            + '">Invented saved-source passage</a> | '
        )
        links += (
            '<a href="'
            + html.escape(row["fallback_link"], quote=True)
            + '">Canonical fallback</a>'
        )
        if row["control_link"]:
            links += (
                ' | <a href="' + row["control_link"] + '">No text-fragment control</a>'
            )
        index_rows.append(
            "<tr><td>"
            + row["case_id"]
            + "</td><td>"
            + links
            + "</td><td>"
            + row["canonical_hash"]
            + "</td><td>["
            + str(row["start"])
            + ","
            + str(row["end"])
            + ")</td></tr>"
        )
    artifacts["index.html"] = (
        '<!doctype html><html><head><meta charset="utf-8"><title>Invented Stage 10 V5</title></head><body>'
        "<h1>Invented Stage 10 V5 — local_file only</h1><p>Disable network in the declared target. Native highlighting, canonical fallback and capture are independent. All manual observations are pending. External HTTPS is unverified.</p><table>"
        + "".join(index_rows)
        + "</table></body></html>"
    ).encode()
    artifacts["expected.json"] = inventory
    root.mkdir(parents=True, exist_ok=True)
    if directory.exists():
        assert all(
            (directory / name).read_bytes() == data for name, data in artifacts.items()
        )
    else:
        with tempfile.TemporaryDirectory(prefix=".v5-", dir=root) as temporary:
            staging = Path(temporary) / "bundle"
            staging.mkdir()
            for name, data in artifacts.items():
                (staging / name).write_bytes(data)
            os.rename(staging, directory)
    pointer = (
        '<!doctype html><html><head><meta charset="utf-8"><title>Invented V5 index</title></head><body><a href="'
        + key
        + '/index.html">Open the content-bound invented V5 index</a></body></html>'
    ).encode()
    pointer_path = root / "index.html"
    if pointer_path.exists():
        assert pointer_path.read_bytes() == pointer
    else:
        with pointer_path.open("xb") as out:
            out.write(pointer)
    return directory, rows, tuple(views)


def observed_row(
    row,
    capture,
    *,
    native="pending",
    fallback="pending",
    observer=None,
    observed_at=None,
):
    """Keep observer-supplied presentation outcomes separate from capture."""
    if native not in (*NATIVE, "pending") or fallback not in (*FALLBACK, "pending"):
        raise ValueError("invalid_observation")
    if native != "pending" or fallback != "pending":
        if not observer or not observed_at:
            raise ValueError("observer_required")
        timestamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        if timestamp.utcoffset() is None or timestamp.utcoffset().total_seconds() != 0:
            raise ValueError("observer_date_required")
    return row | {
        "native": native,
        "fallback": fallback,
        "capture": capture.status,
        "capture_reason": capture.reason,
        "capture_observation": capture.model_dump(mode="json"),
        "screenshots_rights": "local_only",
        "observer": observer,
        "observed_at": observed_at,
        "failure_reason": "browser_unavailable"
        if native == "unavailable"
        else "native_failed"
        if native == "failed"
        else "fallback_failed"
        if fallback == "failed"
        else "rights_restricted"
        if fallback == "withheld"
        else None,
    }


def capture_observations(
    rows, views, renderer, session, store, *, capture_observer="fixture-renderer"
):
    """Persist explicitly supplied invented views through an injected renderer."""
    captured = []

    class PersistingRenderer:
        environment = renderer.environment

        def capture(self, saved_html, policy, *, source_document_id):
            capture = renderer.capture(
                saved_html, policy, source_document_id=source_document_id
            )
            captured.append(capture)
            store.put(capture)
            data = canonical_json(capture)
            path = session / "prepared-captures" / (sha256_hex(data) + ".json")
            path.parent.mkdir(exist_ok=True)
            with path.open("xb") as out:
                out.write(data)
            return capture

    observations = []
    for row, view in zip(rows, views):
        captured.clear()
        observation = capture_evidence_view(view, PersistingRenderer(), ISOLATED_1)
        assert (observation.canonical_hash, observation.start, observation.end) == (
            row["canonical_hash"],
            row["start"],
            row["end"],
        )
        assert (observation.utf16_start, observation.utf16_end) == (
            row["utf16_start"],
            row["utf16_end"],
        )
        assert observation.screenshots_rights == "local_only"
        result_row = observed_row(row, observation)
        result_row["capture_observer"] = capture_observer
        result_row["capture_observed_at"] = datetime.now(UTC).isoformat()
        result_row["screenshot_artifact_ids"] = (
            [a.content_sha256 for a in captured[-1].screenshots] if captured else []
        )
        observations.append(result_row)
    return observations


def test_invented_v5_public_capture(tmp_path, monkeypatch):
    """USER ONLY: no setup/download; records failure/unavailability separately."""
    directory, rows, views = build_artifacts(ROOT, tmp_path, monkeypatch)
    # New immutable session outputs; the static index remains after pytest exits.
    session = directory / ("session-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"))
    session.mkdir()
    store_module = importlib.import_module("earnings_ingestion.browser.store")
    store = store_module.CaptureStore(session / "captures", session)
    try:
        adapter = importlib.import_module("earnings_ingestion.browser.selenium_capture")
        install = importlib.import_module("earnings_ingestion.browser.install")
        renderer = adapter.SeleniumRenderer(install.installed(), store.screenshot)
    except ImportError:
        renderer = FakeRenderer(
            {},
            CaptureEnvironment(
                "unavailable",
                "none",
                "none",
                "none",
                "unavailable",
                "none",
                "unavailable",
            ),
        )

    observations = capture_observations(
        rows, views, renderer, session, store, capture_observer="user-command"
    )
    (session / "observations.json").write_text(
        json.dumps(observations, sort_keys=True, indent=2)
    )
    # Native/manual outcomes remain pending regardless of successful capture.
    assert all(r["native"] == r["fallback"] == "pending" for r in observations)
    assert all(
        r["capture"] in {"completed", "partial", "failed", "unavailable"}
        for r in observations
    )

    if any(r["capture"] == "failed" for r in observations):
        pytest.fail("capture_failed")
    if all(r["capture"] == "unavailable" for r in observations):
        pytest.skip("browser_unavailable")
