"""Invented V8 harness with explicit synthetic saved-input and public replay bindings.

No helper discovers a research document, gold, or a codebook example. Test scratch
repositories are strictly temporary; source-bearing objects never leave safe_summary.
"""

import importlib
import json
import shutil
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.events.state_table import write_run
from earnings_ingestion.events.states import current_states
from earnings_pipeline.cli import app
from earnings_pipeline.theme_workflow import FixtureSupportingPolicy, replay_runtime
from earnings_themes.analysis import (
    AnalysisInputs,
    FixtureAuthorization,
    RawCacheInputs,
    read_analysis_run,
    reverify_analysis_inputs,
    reverify_analysis_run,
)
from earnings_themes.coding.cache import CodingCache
from earnings_themes.coding.store import read_coding_run, reverify_coding_run
from earnings_themes.extraction.store import read_run
from earnings_themes.support import read_support_run, reverify_support_run
from earnings_themes.support.cache import SupportCache
from earnings_themes.support.records import SupportSources
from typer.testing import CliRunner

config_cases = importlib.import_module("apps.earnings-pipeline.tests.test_theme_config")
analysis_cases = importlib.import_module(
    "packages.earnings-themes.tests.analysis.cases"
)
coding_cases = importlib.import_module("packages.earnings-themes.tests.coding.cases")
theme_fixtures = importlib.import_module("packages.earnings-themes.tests.conftest")


@pytest.fixture
def no_network(monkeypatch):
    trips = theme_fixtures.no_network.__wrapped__(monkeypatch)
    original_bytes, original_text = Path.read_bytes, Path.read_text

    def permitted(path):
        resolved = path.resolve()
        if any(resolved.is_relative_to(REPO / root) for root in ("data", "evaluation")):
            trips.append("protected_reader")
            raise AssertionError("protected_reader_forbidden")

    def read_bytes(path, *args, **kwargs):
        permitted(path)
        return original_bytes(path, *args, **kwargs)

    def read_text(path, *args, **kwargs):
        permitted(path)
        return original_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    monkeypatch.setattr(Path, "read_text", read_text)
    yield trips
    assert trips == []


REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "tests/fixtures/themes/stage10"
NOW = datetime(2026, 10, 7, 13, tzinfo=UTC)


def replay_acquisition(root):
    from earnings_ingestion.cohort.freeze import load_manifest
    from earnings_ingestion.events.acquire import acquire
    from earnings_ingestion.events.fixture import (
        ACQUIRED_AT,
        ACQUISITION_RUN,
        COHORT_MANIFEST,
        FIXTURE_DIR,
    )
    from earnings_ingestion.events.freeze import load_event_manifest
    from earnings_ingestion.events.pilot import load_pilot
    from earnings_ingestion.events.records import AcquisitionOverridesFile
    from earnings_ingestion.fetch.responses import UnexpectedResponse
    from earnings_ingestion.fetch.store import ArtifactStore

    universe = load_manifest(REPO / COHORT_MANIFEST)
    events = load_event_manifest(REPO / FIXTURE_DIR / "events-v1.json")
    pilot = load_pilot(REPO / FIXTURE_DIR / "pilot-v1.json", universe)
    scratch = root / "acquisition"
    shutil.copytree(REPO / FIXTURE_DIR / "raw", scratch / "raw")

    def refusing_fetch(url, types):
        raise UnexpectedResponse(f"HTTP 404 for {url}")

    result = acquire(
        events,
        pilot,
        universe,
        ArtifactStore(scratch / "raw", root),
        refusing_fetch,
        overrides=AcquisitionOverridesFile(schema_version=1),
        states_dir=scratch / "states",
        canonical_dir=scratch / "canonical",
        run_id=ACQUISITION_RUN,
        now=lambda: ACQUIRED_AT,
    )
    assert len(result.fetched) == 0
    return result.transitions


def seed_case(tmp_path, *, seed=True, review=False, empty=False, local_only=False):
    """Copy only permitted frozen synthetic metadata; every canonical/source is invented."""
    from earnings_ingestion.cohort.freeze import load_manifest
    from earnings_ingestion.cohort.identity import operative_hash
    from earnings_ingestion.events.fixture import (
        COHORT_MANIFEST,
        FIXTURE_DIR,
        load_transitions,
    )
    from earnings_ingestion.events.freeze import load_event_manifest
    from earnings_ingestion.events.pilot import load_pilot
    from earnings_pipeline.theme_config import load_workflow_config
    from earnings_themes.analysis import (
        AcquisitionStatus,
        AnalysisPolicy,
        ExpectedEvent,
        analysis_provenance_hash,
    )
    from earnings_themes.coding.adapters import ScriptedClassifier
    from earnings_themes.coding.cache import CodingCache
    from earnings_themes.coding.run import propose_run
    from earnings_themes.extraction.adapters import ModelReply, ScriptedAdapter
    from earnings_themes.extraction.cache import CachedAdapter
    from earnings_themes.extraction.prompt import parse_template
    from earnings_themes.extraction.run import extract_run
    from earnings_themes.extraction.store import StoredRun
    from earnings_themes.support.cache import SupportCache
    from earnings_themes.support.records import SupportSources
    from earnings_themes.support.run import assess_run

    payload = json.loads((FIXTURES / "replay-config.json").read_bytes())
    root = tmp_path / "inputs"
    root.mkdir()

    def save(relative, data):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return {"path": relative, "sha256": sha256_hex(data)}

    for field, path in (
        ("universe", REPO / COHORT_MANIFEST),
        ("events", REPO / FIXTURE_DIR / "events-v1.json"),
        ("pilot", REPO / FIXTURE_DIR / "pilot-v1.json"),
    ):
        payload[field] = save("inputs/" + path.name, path.read_bytes())
    universe = load_manifest(root / Path(payload["universe"]["path"]).name)
    events = load_event_manifest(root / "events-v1.json")
    pilot = load_pilot(root / "pilot-v1.json", universe)
    history = replay_acquisition(tmp_path)
    committed = load_transitions(REPO / FIXTURE_DIR / "acquisition.json")
    acquisition_unchanged = tuple(s.model_dump() for s in history) == tuple(
        s.model_dump() for s in committed
    )
    assert acquisition_unchanged, "acquisition_replay_changed"
    latest = current_states(history, pilot.definition.content_hash)
    chosen = next(s for s in latest.values() if s.to_state.value == "parsed")
    missing = tuple(
        s for s in latest.values() if s.to_state.value in {"unavailable", "failed"}
    )
    selected = tuple(sorted((chosen.event_id, *(s.event_id for s in missing))))
    e = next(e for e in events.rows if e.event_id == chosen.event_id)
    expected = ExpectedEvent(
        event_id=e.event_id,
        entity_id=e.issuer_id,
        cik=e.cik,
        period_end=e.period_end,
        fiscal_year=e.reported_fiscal_year,
        fiscal_quarter={"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}.get(
            e.reported_fiscal_quarter
        ),
        eligibility_status=e.eligibility_status.value,
        eligibility_reason=e.eligibility_reason.value,
        membership_assertion_id=e.membership_assertion_id,
        event_manifest_hash=events.definition.content_hash,
        pilot_hash=pilot.definition.content_hash,
    )
    from earnings_core import ArtifactRef, RightsStatus
    from earnings_ingestion.canonical.serialize import from_fixture_json
    from earnings_ingestion.fetch.store import ArtifactStore
    from earnings_themes.analysis import RawSnapshot
    from earnings_themes.anchoring import Bundle

    canonical_data = (
        tmp_path / "acquisition/canonical" / (chosen.doc_id + ".json")
    ).read_bytes()
    parsed = from_fixture_json(canonical_data.decode())
    bundle = Bundle(
        "stage10-invented", parsed.document, parsed.elements, parsed.masked.masks
    )
    saved = ArtifactStore(tmp_path / "acquisition/raw", tmp_path).get(
        "sec-edgar",
        chosen.artifact_sha256,
        rights_status=RightsStatus.REDISTRIBUTABLE,
        rights_basis="Invented synthetic fixture permission",
    )
    meta, _discarded = analysis_cases.metadata(bundle, expected)
    artifact = ArtifactRef.for_bytes(
        saved.body,
        media_type="text/html",
        storage_ref="inputs/raw.html",
        rights_status=RightsStatus.REDISTRIBUTABLE,
        rights_basis="Invented synthetic fixture permission",
    )
    raw = RawSnapshot(meta.doc_id, artifact, saved.body)
    manifest = parsed.manifest
    meta = meta.model_copy(
        update={
            "raw_artifact": artifact,
            "raw_hash": artifact.content_sha256,
            "rights_basis": artifact.rights_basis,
            "retrieved_at": chosen.retrieved_at,
            "parser_version": manifest.canonicalization_version,
            "mask_policy_id": manifest.mask_policy_id,
            "mask_policy_version": manifest.mask_policy_version,
        }
    )
    if local_only:
        from earnings_core import RightsStatus

        artifact = raw.artifact.model_copy(
            update={"rights_status": RightsStatus.LOCAL_ONLY}
        )
        raw = replace(raw, artifact=artifact)
        meta = meta.model_copy(
            update={
                "rights_status": RightsStatus.LOCAL_ONLY,
                "raw_artifact": artifact,
                "export_text": False,
                "export_raw": False,
                "retain_capture": True,
            }
        )
    from earnings_themes.analysis import CanonicalSnapshot

    snap = CanonicalSnapshot(bundle.document.doc_id, canonical_data)
    from earnings_core import digest

    parsed_json = json.loads(snap.data)
    meta = meta.model_copy(
        update={
            "canonical_manifest_hash": digest(parsed_json["manifest"]),
            "mask_manifest_hash": analysis_cases.mask_hash(parsed_json),
            "filing_at": e.filing_acceptance_time.astimezone(UTC)
            if e.filing_acceptance_time
            else None,
            "published_at": e.first_publication_time.astimezone(UTC)
            if e.first_publication_time
            else None,
        }
    )
    payload["sources"] = [
        {
            "event_id": e.event_id,
            "doc_id": bundle.document.doc_id,
            "canonical": save("inputs/canonical.json", snap.data),
            "metadata": save("inputs/metadata.json", meta.model_dump_json().encode()),
            "raw": save("inputs/raw.html", raw.data),
        }
    ]
    keep = {s.document_id for s in (chosen, *missing)}
    history = tuple(
        s.model_copy(
            update={
                "doc_id": bundle.document.doc_id,
                "artifact_sha256": meta.raw_hash,
                "retrieved_at": meta.retrieved_at,
            }
        )
        if s.document_id == chosen.document_id and s.to_state.value == "parsed"
        else s.model_copy(
            update={"artifact_sha256": meta.raw_hash, "retrieved_at": meta.retrieved_at}
        )
        if s.document_id == chosen.document_id and s.to_state.value == "acquired"
        else s
        for s in history
        if s.document_id in keep
    )
    path = write_run(tmp_path / payload["states_dir"], history)
    payload["acquisition_files"] = [
        {
            "path": path.relative_to(tmp_path).as_posix(),
            "sha256": sha256_hex(path.read_bytes()),
        }
    ]
    (path.parent / ".acquire.lock").touch()
    book = analysis_cases.make_book(theme_fixtures.codebook.__wrapped__())
    from earnings_themes.codebook import codebook_toml

    payload["codebook"] = save("inputs/book.toml", codebook_toml(book).encode())
    template_text = (REPO / "prompts/extraction/pointer-1.md").read_bytes()
    payload["extraction_prompt"] = save("inputs/extraction.md", template_text)
    payload["coding_prompt"] = save(
        "inputs/coding.md", payload["coding_policy"]["prompt_text"].encode()
    )
    payload["support_prompt"] = save(
        "inputs/support.md", payload["support_policy"]["prompt_text"].encode()
    )
    payload["lockfile"] = save("uv.lock", b"Invented lock identity")
    payload["software"]["lock_hash"] = payload["lockfile"]["sha256"]
    payload.update(
        universe_hash=operative_hash(universe),
        event_hash=events.definition.content_hash,
        pilot_hash=pilot.definition.content_hash,
        selected_event_ids=list(selected),
    )
    payload["analysis_policy"] = AnalysisPolicy(
        population_id="djia-synthetic",
        event_ids=selected,
        population_hash=pilot.definition.content_hash,
        mask_policy_id=meta.mask_policy_id,
        mask_policy_version=meta.mask_policy_version,
        include_family_view=False,
        scope="fixture",
    ).model_dump(mode="json")
    if review:
        payload["assignment_policy"] = None
    config = load_workflow_config(
        config_cases.write_config(tmp_path, payload), repo=tmp_path
    )
    if not seed:
        return config, payload
    started = config.fixture_started_at
    adapter = ScriptedAdapter(
        lambda request: ModelReply(
            model="scripted",
            text=json.dumps(
                {
                    "candidates": []
                    if empty
                    else [
                        {"quote_labels": ["U1"], "claim": claim}
                        for claim in (
                            "Invented expansion.",
                            "Invented second operating claim.",
                        )
                    ]
                }
            ),
        )
    )

    def extract(mode):
        return StoredRun.of(
            extract_run(
                (bundle,),
                CachedAdapter(adapter, tmp_path / config.extraction_cache, mode),
                config.extraction_policy,
                parse_template(template_text.decode()),
                config.extraction_ceilings,
                run_id=config.extraction_run_id,
                started_at=started,
                software=config.software,
            )
        )

    extract("live")
    stored = extract("replay")
    by_event = {e.event_id: e for e in events.rows}
    expected_rows = tuple(
        ExpectedEvent(
            **(
                expected.model_dump()
                | {
                    "event_id": k,
                    "entity_id": by_event[k].issuer_id,
                    "cik": by_event[k].cik,
                    "period_end": by_event[k].period_end,
                    "fiscal_year": by_event[k].reported_fiscal_year,
                    "fiscal_quarter": {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}.get(
                        by_event[k].reported_fiscal_quarter
                    ),
                    "membership_assertion_id": by_event[k].membership_assertion_id,
                }
            )
        )
        for k in selected
    )
    current = current_states(history, config.pilot_hash)
    acquisitions = tuple(
        AcquisitionStatus(
            event_id=s.event_id,
            document_id=s.document_id,
            state=s.to_state.value,
            missing_reason=s.missing_reason.value if s.missing_reason else None,
            failure_reason=s.failure_reason.value if s.failure_reason else None,
            doc_id=s.doc_id,
            source_document_id=bundle.document.source_document_id if s.doc_id else None,
            raw_hash=s.artifact_sha256,
            accession=s.accession,
            exhibit=s.exhibit,
            retrieved_at=s.retrieved_at,
            state_run_id=s.run_id,
            state_schema_version=s.schema_version,
            pilot_hash=s.pilot_hash,
        )
        for s in sorted(current.values(), key=lambda s: s.document_id)
    )
    provenance = analysis_provenance_hash(
        selected_universe_hash=config.universe_hash,
        expected=expected_rows,
        acquisition=acquisitions,
        metadata=(meta,),
        canonical_snapshots=(snap,),
    )
    sources = SupportSources(stored, (bundle,), book, provenance)
    classifier = ScriptedClassifier(
        lambda request: ModelReply(
            model=config.classifier_identity.runtime.model_id,
            text=json.dumps(
                {"theme_ids": ["capacity_expansion", "demand"], "attributes": {}}
            ),
        ),
        lambda request: 5,
        config.classifier_identity,
    )

    def propose(mode):
        return propose_run(
            config.coding_run_id,
            sources,
            tuple((c.doc_id, c.claim_id) for c in stored.claims),
            classifier,
            config.coding_policy,
            config.coding_ceilings,
            cache=CodingCache(tmp_path / config.coding_cache, mode),
            started_at=started,
            software=config.software,
        )

    propose("live")
    proposal = propose("replay")
    scorer, judges = coding_cases.make_support_parts()
    scorer_bound = scorer.identity == config.scorer_identity
    judges_bound = tuple(j.identity for j in judges) == config.judge_identities
    assert scorer_bound and judges_bound, "replay_identity_mismatch"
    assess_run(
        config.support_run_id,
        sources,
        proposal.targets,
        scorer,
        judges,
        config.support_policy,
        config.support_ceilings,
        extractor_family=config.extractor_family,
        cache=SupportCache(tmp_path / config.support_cache, "live"),
        started_at=started,
        software=config.software,
    )
    replay_scorer, replay_judges = coding_cases.make_support_parts(replay=True)
    replay_support = assess_run(
        config.support_run_id,
        sources,
        proposal.targets,
        replay_scorer,
        replay_judges,
        config.support_policy,
        config.support_ceilings,
        extractor_family=config.extractor_family,
        cache=SupportCache(tmp_path / config.support_cache, "replay"),
        started_at=started,
        software=config.software,
    )
    FixtureSupportingPolicy(proposal, replay_support)
    return (
        config,
        payload,
        {
            "expected": expected_rows,
            "acquisition": acquisitions,
            "metadata": (meta,),
            "canonical_snapshots": (snap,),
            "raw_snapshots": (raw,),
            "bundles": (bundle,),
            "book": book,
            "provenance": provenance,
            "proposal": proposal,
        },
    )


class VerticalCase:
    """Own one temporary fixture run; expose only metadata in assertion summaries."""

    def __init__(self, root, monkeypatch, **options):
        assert root.resolve() != REPO and REPO not in root.resolve().parents, (
            "fixture_root_not_temporary"
        )
        self.root = root
        self.monkeypatch = monkeypatch
        result = seed_case(root, **options)
        self.config, self.payload = result[:2]
        self.material = result[2] if len(result) == 3 else None
        self.path = config_cases.write_config(root, self.payload)
        self.before = self.input_hashes()
        self.transports = []
        import earnings_pipeline.extract_cli as command

        real_runtime = replay_runtime

        def counted_runtime(config):
            runtime = real_runtime(config)
            self.transports.extend(
                (runtime.extractor, runtime.classifier, runtime.scorer, *runtime.judges)
            )
            return runtime

        monkeypatch.setattr(command, "replay_runtime", counted_runtime)

    def input_hashes(self):
        paths = [
            self.config.universe,
            self.config.events,
            self.config.pilot,
            self.config.codebook,
            self.config.lockfile,
            *self.config.acquisition_files,
            self.config.extraction_prompt,
            self.config.coding_prompt,
            self.config.support_prompt,
        ]
        for source in self.config.sources:
            paths.extend([source.canonical, source.metadata])
            if source.raw is not None:
                paths.append(source.raw)
        return tuple(sha256_hex((self.root / pin.path).read_bytes()) for pin in paths)

    def invoke_replay_cli(self):
        self.monkeypatch.chdir(self.root)
        return CliRunner().invoke(app, ["extract", "run", "--config", str(self.path)])

    def current_inputs(self):
        m = self.material
        output = self.root / self.config.output_dir
        extraction = read_run(output / "extraction")
        support = read_support_run(output / "support")
        coding = read_coding_run(output / "coding")
        sources = SupportSources(extraction, m["bundles"], m["book"], m["provenance"])
        policy = (
            FixtureSupportingPolicy(m["proposal"], support)
            if self.config.assignment_policy
            else None
        )
        reverify_support_run(support, sources)
        reverify_coding_run(coding, sources, support, policy)
        return AnalysisInputs(
            sources=sources,
            support=support,
            coding=coding,
            assignment_policy=policy,
            expected=m["expected"],
            acquisition=m["acquisition"],
            metadata=m["metadata"],
            copies=self.config.copies,
            no_theme=self.config.no_theme,
            provenance_hash=m["provenance"],
            selected_universe_hash=self.config.universe_hash,
            raw_verification=(),
            raw_caches=RawCacheInputs(
                CodingCache(self.root / self.config.coding_cache, "replay"),
                SupportCache(self.root / self.config.support_cache, "replay"),
            ),
            raw_snapshots=m["raw_snapshots"],
            analysis_policy=self.config.analysis_policy,
            canonical_snapshots=m["canonical_snapshots"],
            fixture_authorization=FixtureAuthorization(
                "djia-synthetic",
                self.config.event_hash,
                self.config.pilot_hash,
                m["provenance"],
            ),
        )

    def safe_summary(self):
        from earnings_core import VerifiedSpan, parse_span_candidate, validate_span
        from earnings_ingestion.events.state_table import read_runs
        from earnings_pipeline.theme_report import ReportManifest
        from earnings_themes.analysis import TABLE_GRAINS

        inputs = self.current_inputs()
        bound = reverify_analysis_inputs(inputs)
        output = self.root / self.config.output_dir
        stored = read_analysis_run(output / "analysis")
        reverify_analysis_run(
            stored, inputs, self.config.analysis_policy, self.config.families
        )
        tables = stored.tables.frames
        exact = []
        by_doc = {b.document.doc_id: b for b in inputs.sources.bundles}
        for quote in inputs.sources.stored_run.quotes:
            bundle = by_doc[quote.span.doc_id]
            candidate = parse_span_candidate(
                quote.span.model_dump(exclude={"validator_version"})
            )
            exact.append(
                isinstance(
                    validate_span(bundle.document, bundle.elements, candidate),
                    VerifiedSpan,
                )
            )
        wanted = {
            (c.doc_id, c.claim_id, q)
            for c in inputs.sources.stored_run.claims
            for q in c.quote_ids
        }
        actual = set(
            tables["claim_evidence"].select("doc_id", "claim_id", "quote_id").rows()
        )
        refs = tables["evidence"].to_dicts()
        report = ReportManifest.model_validate_json(
            (output / "report/report.json").read_bytes()
        )
        artifacts = dict(report.artifact_hashes)
        report_bytes = (output / "report/report.html").read_bytes()
        citations = True
        highlighted = True
        for ref in refs:
            if ref["status"] == "withheld":
                citations = citations and ref["reason"] == "rights_restricted"
                continue
            citations = (
                citations
                and ref["source_fragment_url"] is not None
                and ref["raw_artifact"] is not None
            )
            name = "artifacts/" + ref["view_artifact"]["content_sha256"] + ".html"
            data = (output / "report" / name).read_bytes()
            import html

            bundle = by_doc[ref["doc_id"]]
            marked = (
                '<mark id="'
                + ref["anchor_id"]
                + '">'
                + html.escape(
                    bundle.document.canonical_text[ref["start"] : ref["end"]],
                    quote=True,
                )
                + "</mark>"
            ).encode()
            highlighted = (
                highlighted
                and data.count(marked) == 1
                and ref["anchor_id"].encode() in report_bytes
            )
            citations = citations and sha256_hex(data) == artifacts[name]
        states = current_states(
            read_runs(self.root / self.config.states_dir), self.config.pilot_hash
        )
        processing = [s for s in states.values() if s.schema_version == 2]
        return {
            "scope": stored.record.scope,
            "processing_schema": min(s.schema_version for s in processing),
            "observation_grain_unique": tables["observations"]
            .unique(subset=TABLE_GRAINS["observations"])
            .height
            == tables["observations"].height,
            "all_original_links_preserved": wanted == actual,
            "exact_spans_reverified": all(exact),
            "exact_span_rate": sum(exact) / len(exact) if exact else None,
            "source_and_snapshot_citations": citations,
            "highlight_occurrence": highlighted,
            "immutable_inputs_unchanged": self.before == self.input_hashes(),
            "dispatch_calls": sum(t.dispatch_calls for t in self.transports),
            "count_calls": sum(t.count_calls for t in self.transports),
            "quote_count": tables["quotes"].height,
            "theme_count": tables["observations"]["theme_id"].n_unique(),
            "claim_link_count": len(actual),
            "assignment_claim_count": tables["assignment_claims"].height,
            "transcript_claim_count": int(
                tables["coverage"]
                .filter(tables["coverage"]["doc_type"] == "transcript")["observable"]
                .sum()
            ),
            "binding_hash": bound.binding_hash,
            "analysis_hash": stored.manifest_hash,
            "fixture_policy": all(
                r["policy_scope"] == "fixture"
                for r in tables["observations"].iter_rows(named=True)
            ),
            "source_hash_bound": inputs.coding.record.source_run_hash
            == inputs.support.record.source_run_hash,
        }


@pytest.fixture
def vertical_case(tmp_path, monkeypatch, no_network):
    return VerticalCase(tmp_path, monkeypatch)
