"""Sequential replay composition with immutable publication and separate state receipts."""

import json
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, Self

from earnings_core import canonical_json, digest, sha256_hex
from earnings_ingestion.browser import BrowserRenderer
from earnings_ingestion.canonical.serialize import from_fixture_json
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.identity import operative_hash
from earnings_ingestion.events.freeze import load_event_manifest
from earnings_ingestion.events.pilot import load_pilot
from earnings_ingestion.events.state_table import read_runs, write_processing_run
from earnings_ingestion.events.states import (
    PROCESSING_PREDECESSOR_FIELDS,
    DocumentState,
    ProcessingTransition,
    check_histories,
    current_states,
    in_order,
)
from earnings_ingestion.fetch.client import ProcessLock
from earnings_ingestion.fetch.store import write_new
from earnings_themes.analysis import (
    AcquisitionStatus,
    AnalysisInputs,
    AnalysisPart,
    CanonicalSnapshot,
    DocumentMetadata,
    ExpectedEvent,
    FixtureAuthorization,
    RawCacheInputs,
    RawSnapshot,
    analysis_provenance_hash,
    build_analysis,
    document_completions,
    read_analysis_run,
    reverify_analysis_inputs,
    reverify_analysis_run,
    write_analysis_run,
)
from earnings_themes.anchoring import Bundle
from earnings_themes.codebook import load_codebook
from earnings_themes.coding.adapters import Classifier
from earnings_themes.coding.assignments import project_assignments
from earnings_themes.coding.cache import CodingCache
from earnings_themes.coding.decide import AssignmentPolicy, decide_assignments
from earnings_themes.coding.records import (
    CodingRun,
    CodingRunRecord,
    PolicyReference,
    PolicyVote,
)
from earnings_themes.coding.run import ProposalRun, propose_run
from earnings_themes.coding.store import (
    read_coding_run,
    reverify_coding_run,
    write_coding_run,
)
from earnings_themes.extraction.adapters import ModelAdapter
from earnings_themes.extraction.cache import CachedAdapter
from earnings_themes.extraction.prompt import parse_template
from earnings_themes.extraction.run import extract_run
from earnings_themes.extraction.store import StoredRun, read_run, write_run
from earnings_themes.support import (
    assess_run,
    read_support_run,
    reverify_support_run,
    write_support_run,
)
from earnings_themes.support.cache import SupportCache
from earnings_themes.support.judges import Judge, validate_panel
from earnings_themes.support.records import SupportSources
from earnings_themes.support.scorers import EntailmentScorer
from pydantic import AwareDatetime, Field, model_validator

from earnings_pipeline.evidence_views import make_evidence_view
from earnings_pipeline.theme_config import (
    CANONICAL_ID,
    SAFE_COMPONENT,
    WORKFLOW_REASONS,
    WorkflowConfig,
    WorkflowError,
    confined_path,
    read_selected,
    validate_paths,
)
from earnings_pipeline.theme_report import ReportManifest, write_theme_report

Phase = Literal[
    "preflight", "extraction", "coding", "support", "analysis", "publication", "state"
]
Status = Literal["state_pending", "state_recorded", "no_state_change", "failed"]


class WorkflowArtifact(AnalysisPart):
    artifact_id: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def _portable_id(self) -> Self:
        if Path(self.artifact_id).is_absolute() or any(
            SAFE_COMPONENT.fullmatch(part) is None or part in {".", ".."}
            for part in self.artifact_id.split("/")
        ):
            raise ValueError("malformed_record")
        return self


class WorkflowPart(AnalysisPart):
    """Closed workflow reasons include the separate ingestion state boundary."""

    @model_validator(mode="after")
    def _common_invariants(self) -> Self:
        for name in type(self).model_fields:
            value = getattr(self, name)
            if isinstance(value, datetime) and (
                value.tzinfo is None or value.utcoffset() != timedelta(0)
            ):
                raise ValueError("malformed_record")
            if name == "reason" and value is not None and value not in WORKFLOW_REASONS:
                raise ValueError("malformed_record")
            if name in {"event_ids", "doc_ids"} and any(
                (CANONICAL_ID if name == "doc_ids" else SAFE_COMPONENT).fullmatch(
                    identity
                )
                is None
                for identity in value
            ):
                raise ValueError("malformed_record")
            if name == "phase_counts" and any(
                type(count) is not int or count < 0 for _, count in value
            ):
                raise ValueError("malformed_record")
        if getattr(self, "state_count", 0) > 0 and getattr(self, "state", None) is None:
            raise ValueError("malformed_record")
        if SAFE_COMPONENT.fullmatch(self.run_id) is None or self.run_id in {".", ".."}:
            raise ValueError("malformed_record")
        return self


class WorkflowFailure(WorkflowPart):
    run_id: str
    phase: Phase
    event_ids: tuple[str, ...]
    doc_ids: tuple[str, ...]
    reason: str
    completed_stages: tuple[WorkflowArtifact, ...]
    usage_availability: Literal["known", "unreported"]
    created_at: AwareDatetime


class WorkflowReceipt(WorkflowPart):
    run_id: str
    created_at: AwareDatetime
    config_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    scope: Literal["fixture", "research"]
    status: Status
    analysis: WorkflowArtifact | None
    report: WorkflowArtifact | None
    failure: WorkflowArtifact | None
    state: WorkflowArtifact | None
    state_count: int = Field(ge=0)
    phase_counts: tuple[tuple[Phase, int], ...]
    reason: str | None
    limitations: tuple[
        Literal[
            "capture_not_supplied",
            "browser_observation_not_supplied",
            "capture_nondurable",
            "analysis_as_published",
        ],
        ...,
    ]


@dataclass(frozen=True, repr=False)
class WorkflowRuntime:
    extractor: ModelAdapter
    classifier: Classifier
    scorer: EntailmentScorer
    judges: tuple[Judge, Judge]
    assignment_policy: AssignmentPolicy | None
    renderer: BrowserRenderer | None


@dataclass(frozen=True, repr=False)
class WorkflowResult:
    run_id: str
    status: Status
    reason: str | None
    receipt_id: str
    receipt_hash: str
    analysis_id: str | None
    analysis_hash: str | None
    report_id: str | None
    report_hash: str | None
    failure_id: str | None
    failure_hash: str | None
    state_id: str | None
    state_hash: str | None
    state_count: int
    phase_counts: tuple[tuple[Phase, int], ...]
    scope: Literal["fixture", "research"]

    def __post_init__(self) -> None:
        _require(
            type(self.receipt_id) is str and type(self.receipt_hash) is str,
            "malformed_record",
        )
        _require(self.state_count == 0 or self.state_id is not None, "malformed_record")
        _require(SAFE_COMPONENT.fullmatch(self.run_id) is not None, "malformed_record")
        _require(
            self.status
            in {"state_pending", "state_recorded", "no_state_change", "failed"}
            and self.scope in {"fixture", "research"},
            "malformed_record",
        )
        _require(
            self.reason is None or self.reason in WORKFLOW_REASONS, "malformed_record"
        )
        _require(
            type(self.state_count) is int and self.state_count >= 0, "malformed_record"
        )
        for identity, hash_value in (
            (self.receipt_id, self.receipt_hash),
            (self.analysis_id, self.analysis_hash),
            (self.report_id, self.report_hash),
            (self.failure_id, self.failure_hash),
            (self.state_id, self.state_hash),
        ):
            _require((identity is None) == (hash_value is None), "malformed_record")
            if identity is not None:
                WorkflowArtifact(artifact_id=identity, sha256=hash_value)
        _require(
            all(
                phase
                in {
                    "preflight",
                    "extraction",
                    "coding",
                    "support",
                    "analysis",
                    "publication",
                    "state",
                }
                and type(count) is int
                and count >= 0
                for phase, count in self.phase_counts
            ),
            "malformed_record",
        )


class ReplayOnlyTransport:
    """Identity-only replay façade: every reached dispatch/tokenizer fails closed."""

    def __init__(self, identity) -> None:
        self._identity = identity
        self.dispatch_calls = 0
        self.count_calls = 0

    @property
    def identity(self):
        return self._identity

    def count_tokens(self, request) -> int:
        self.count_calls += 1
        raise WorkflowError("replay_dispatch_forbidden")

    def complete(self, request):
        self.dispatch_calls += 1
        raise WorkflowError("replay_dispatch_forbidden")

    def score(self, request):
        self.dispatch_calls += 1
        raise WorkflowError("replay_dispatch_forbidden")


class ReplayOnlyClassifier(ReplayOnlyTransport):
    pass


class ReplayOnlyExtractor(ReplayOnlyTransport):
    pass


class ReplayOnlyScorer(ReplayOnlyTransport):
    pass


class ReplayOnlyJudge(ReplayOnlyTransport):
    pass


def replay_runtime(config: WorkflowConfig) -> WorkflowRuntime:
    return WorkflowRuntime(
        ReplayOnlyExtractor(config.extraction_identity),
        ReplayOnlyClassifier(config.classifier_identity),
        ReplayOnlyScorer(config.scorer_identity),
        tuple(ReplayOnlyJudge(i) for i in config.judge_identities),
        None,
        None,
    )


class FixtureSupportingPolicy:
    """Fixture-scoped supporting IDs supplied by the current Stage9 eligibility gate."""

    def __init__(self, proposal, support):
        self.reference = PolicyReference(
            policy_id="fixture-supporting/1",
            policy_hash=digest("fixture-supporting/1"),
            kind="fixture",
            codebook=support.record.codebook,
            classifier_configuration_hash=proposal.record.configuration_hash,
            support_configuration_hash=support.record.configuration_hash,
            calibration_reference=None,
        )

    def evaluate(self, view):
        return PolicyVote(action="accept", supporting_quote_ids=view.eligible_quote_ids)


def _require(condition: bool, reason="input_changed") -> None:
    if not condition:
        raise WorkflowError(reason)


def _utc(stamp: datetime) -> datetime:
    _require(
        type(stamp) is datetime
        and stamp.tzinfo is not None
        and stamp.utcoffset() == timedelta(0),
        "malformed_record",
    )
    return stamp


def _reason(error: Exception) -> str:
    value = (
        str(error)
        if type(error).__module__.startswith(
            ("earnings_themes", "earnings_pipeline", "earnings_ingestion")
        )
        or type(error) is ValueError
        else None
    )
    return value if value in WORKFLOW_REASONS else "unexpected_error"


def _artifact(config, path):
    return WorkflowArtifact(
        artifact_id=path.relative_to(config.repo).as_posix(),
        sha256=sha256_hex(path.read_bytes()),
    )


def _publish_metadata(config, name, record):
    data = canonical_json(record.model_dump(mode="json"))
    path = confined_path(config.repo, config.output_dir) / (
        name + "-" + sha256_hex(data) + ".json"
    )
    if path.exists():
        _require(path.read_bytes() == data)
    else:
        write_new(path, data)
    return _artifact(config, path)


def _load_metadata(config, runtime):
    validate_paths(config, repo=config.repo)
    _require(
        runtime.extractor.identity == config.extraction_identity
        and runtime.classifier.identity == config.classifier_identity
        and runtime.scorer.identity == config.scorer_identity
        and tuple(j.identity for j in runtime.judges) == config.judge_identities,
        "model_mismatch",
    )
    validate_panel(config.extractor_family, config.judge_identities)
    if config.policy_reference is not None:
        _require(
            runtime.assignment_policy is not None
            and runtime.assignment_policy.reference == config.policy_reference,
            "policy_unavailable",
        )
    elif config.assignment_policy is None:
        _require(runtime.assignment_policy is None, "policy_mismatch")
    for selected in (
        config.universe,
        config.events,
        config.pilot,
        config.codebook,
        config.lockfile,
        *config.acquisition_files,
    ):
        read_selected(config, selected)
    _require(
        config.events.path.rsplit("/", 1)[0] == config.pilot.path.rsplit("/", 1)[0]
    )
    pilot_payload = json.loads(read_selected(config, config.pilot))
    _require(
        Path(config.events.path).name
        == f"events-v{pilot_payload['definition']['event_manifest_version']}.json"
    )
    universe = load_manifest(confined_path(config.repo, config.universe.path))
    events = load_event_manifest(confined_path(config.repo, config.events.path))
    # Corpus identity is checked before opening canonical source bytes.
    _require(
        config.scope != "fixture"
        or events.definition.corpus_id in {"djia-synthetic", "stage10-invented"},
        "malformed_record",
    )
    pilot = load_pilot(confined_path(config.repo, config.pilot.path), universe)
    _require(
        operative_hash(universe)
        == config.universe_hash
        == events.definition.universe_operative_hash
        == pilot.definition.universe_operative_hash
    )
    _require(
        events.definition.content_hash == config.event_hash
        and pilot.definition.content_hash == config.pilot_hash
    )
    _require(set(config.selected_event_ids) <= {r.event_id for r in pilot.rows})
    _require(config.analysis_policy.population_id == events.definition.corpus_id)
    rows = {r.event_id: r for r in events.rows}
    expected = tuple(
        ExpectedEvent(
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
            event_manifest_hash=config.event_hash,
            pilot_hash=config.pilot_hash,
        )
        for e in (rows[k] for k in config.selected_event_ids)
    )
    bundles, metadata, canonical, raw = [], [], [], []
    for selected in config.sources:
        data = read_selected(config, selected.canonical)
        parsed = from_fixture_json(data.decode("utf-8"))
        meta = DocumentMetadata.model_validate_json(
            read_selected(config, selected.metadata)
        )
        e = rows[selected.event_id]
        _require(
            meta.event_id == selected.event_id
            and meta.doc_id == selected.doc_id == parsed.document.doc_id
        )
        _require(
            meta.entity_id == e.issuer_id
            and meta.cik == e.cik
            and meta.period_end == e.period_end
            and meta.filing_at == e.filing_acceptance_time
            and meta.published_at == e.first_publication_time
        )
        _require(
            meta.fiscal_year == e.reported_fiscal_year
            and meta.fiscal_quarter
            == {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}.get(e.reported_fiscal_quarter)
        )
        bundles.append(
            Bundle(
                selected.event_id, parsed.document, parsed.elements, parsed.masked.masks
            )
        )
        metadata.append(meta)
        canonical.append(CanonicalSnapshot(meta.doc_id, data))
        if selected.raw is not None:
            _require(meta.raw_artifact is not None)
            raw.append(
                RawSnapshot(
                    meta.doc_id, meta.raw_artifact, read_selected(config, selected.raw)
                )
            )
    book = load_codebook(confined_path(config.repo, config.codebook.path))
    template = parse_template(read_selected(config, config.extraction_prompt).decode())
    _require(
        read_selected(config, config.coding_prompt).decode()
        == config.coding_policy.prompt_text
        and sha256_hex(config.coding_policy.prompt_text.encode())
        == config.coding_policy.prompt_hash
    )
    _require(
        read_selected(config, config.support_prompt).decode()
        == config.support_policy.prompt_text
        and sha256_hex(config.support_policy.prompt_text.encode())
        == config.support_policy.prompt_hash
    )
    return (
        expected,
        tuple(bundles),
        tuple(metadata),
        tuple(canonical),
        tuple(raw),
        book,
        template,
    )


def _baseline(config, history, existing_analysis):
    latest = current_states(history, config.pilot_hash)
    baseline, terminals = {}, {}
    for event_id in config.selected_event_ids:
        slot = event_id + ":release"
        _require(slot in latest)
        current = latest[slot]
        if isinstance(current, ProcessingTransition):
            _require(existing_analysis is not None, "state_not_processable")
            _require(
                current.processing_run_hash == existing_analysis.manifest_hash,
                "state_not_processable",
            )
            _require(
                config.stored_analysis is not None
                or current.processing_run_id == config.run_id,
                "state_not_processable",
            )
            chain = [
                r
                for r in in_order(history)
                if r.pilot_hash == config.pilot_hash and r.document_id == slot
            ]
            previous = chain[-2]
            _require(
                previous.to_state is DocumentState.PARSED
                and all(
                    getattr(previous, f) == getattr(current, f)
                    for f in PROCESSING_PREDECESSOR_FIELDS
                ),
                "state_not_processable",
            )
            baseline[slot], terminals[slot] = previous, current
        else:
            baseline[slot] = current
    return baseline, terminals


def _projections(config, baseline, metadata):
    meta_by_doc = {m.doc_id: m for m in metadata}
    _require(
        {s.doc_id for s in baseline.values() if s.to_state is DocumentState.PARSED}
        == set(meta_by_doc)
    )
    result = []
    for s in sorted(baseline.values(), key=lambda s: s.document_id):
        meta = meta_by_doc.get(s.doc_id)
        if meta is not None:
            _require(
                s.artifact_sha256 == meta.raw_hash
                and s.retrieved_at == meta.retrieved_at
            )
        result.append(
            AcquisitionStatus(
                event_id=s.event_id,
                document_id=s.document_id,
                state=s.to_state.value,
                missing_reason=s.missing_reason.value if s.missing_reason else None,
                failure_reason=s.failure_reason.value if s.failure_reason else None,
                doc_id=s.doc_id,
                source_document_id=meta.source_document_id if meta else None,
                raw_hash=s.artifact_sha256,
                accession=s.accession,
                exhibit=s.exhibit,
                retrieved_at=s.retrieved_at,
                state_run_id=s.run_id,
                state_schema_version=s.schema_version,
                pilot_hash=s.pilot_hash,
            )
        )
    return tuple(result)


def _stage_directory(config, kind, selected):
    if selected is not None:
        directory = confined_path(config.repo, selected.directory)
        _require(sha256_hex((directory / "run.json").read_bytes()) == selected.sha256)
        return directory
    return confined_path(config.repo, config.output_dir) / kind


def _extraction(config, runtime, bundles, template, started, directory):
    if directory.exists():
        result = read_run(directory)
    else:
        result = StoredRun.of(
            extract_run(
                bundles,
                CachedAdapter(
                    runtime.extractor,
                    confined_path(config.repo, config.extraction_cache),
                    "replay",
                ),
                config.extraction_policy,
                template,
                config.extraction_ceilings,
                run_id=config.extraction_run_id,
                started_at=started,
                software=config.software,
            )
        )
        write_run(directory, result, bundles)
        result = read_run(directory)
    record = result.record
    _require(
        record.run_id == config.extraction_run_id
        and record.configuration.identity == config.extraction_identity
        and record.configuration.policy == config.extraction_policy
        and record.configuration.ceilings == config.extraction_ceilings
        and record.configuration.prompt_sha256 == template.sha256
    )
    _require(
        record.documents
        == {b.document.doc_id: b.document.canonical_hash for b in bundles}
    )
    _require(dict(record.software) == config.software)
    _require(
        config.fixture_started_at is None
        or record.started_at == config.fixture_started_at
    )
    return result


def _coding(config, sources, support, proposal, policy):
    decisions = decide_assignments(proposal, support, sources, policy)
    assignments, links = project_assignments(decisions, support)
    record = CodingRunRecord(
        **proposal.record.model_dump(),
        proposal_hash=decisions.proposal_hash,
        support_run_id=support.record.run_id,
        support_run_hash=decisions.support_run_hash,
        support_configuration_hash=support.record.configuration_hash,
        policy=decisions.policy,
        counts_by_decision=tuple(
            sorted(Counter(r.status for r in decisions.decisions).items())
        ),
        counts_by_decision_reason=tuple(
            sorted(Counter(r.reason for r in decisions.decisions).items())
        ),
    )
    return CodingRun(
        record,
        proposal.classifications,
        proposal.attempts,
        proposal.proposals,
        proposal.attributes,
        decisions.decisions,
        assignments,
        links,
        proposal.novelty,
    )


def _transition(config, predecessor, completion, processing_hash, stamp, sequence):
    state = completion.processing_state
    reasons = completion.reasons
    reason = (
        None
        if state == "completed"
        else "explicit_no_theme"
        if state == "completed-no-theme"
        else next((r for r in reasons if r != "processing_failed"), "processing_failed")
    )
    missing = (
        "processing_failed"
        if state == "failed"
        else reason
        if state == "partial"
        else None
    )
    return ProcessingTransition.model_validate_json(
        canonical_json(
            predecessor.model_dump(mode="json")
            | {
                "schema_version": 2,
                "run_id": config.run_id,
                "sequence": sequence,
                "recorded_at": stamp,
                "from_state": "parsed",
                "to_state": state,
                "missing_reason": missing,
                "failure_reason": None,
                "attempts": [],
                "processing_run_id": config.run_id,
                "processing_run_hash": processing_hash,
                "completion_hash": digest(completion.model_dump(mode="json")),
                "processing_reason": reason,
            }
        )
    )


def _receipt(
    config, *, status, stamp, stages, state=None, count=0, reason=None, counts=()
):
    receipt = WorkflowReceipt(
        run_id=config.run_id,
        created_at=stamp,
        config_hash=digest(config.model_dump(mode="json")),
        scope=config.scope,
        status=status,
        analysis=stages.get("analysis"),
        report=stages.get("report"),
        failure=stages.get("failure"),
        state=state,
        state_count=count,
        phase_counts=tuple(counts),
        reason=reason,
        limitations=(
            "capture_not_supplied",
            "browser_observation_not_supplied",
            "analysis_as_published",
        )
        + (("capture_nondurable",) if config.capture else ()),
    )
    artifact = _publish_metadata(config, "receipt", receipt)

    def value(kind, field):
        item = stages.get(kind)
        return getattr(item, field) if item else None

    return WorkflowResult(
        config.run_id,
        status,
        reason,
        artifact.artifact_id,
        artifact.sha256,
        value("analysis", "artifact_id"),
        value("analysis", "sha256"),
        value("report", "artifact_id"),
        value("report", "sha256"),
        value("failure", "artifact_id"),
        value("failure", "sha256"),
        state.artifact_id if state else None,
        state.sha256 if state else None,
        count,
        tuple(counts),
        config.scope,
    )


def _checked_report(config, directory, stored, inputs, views):
    if not directory.exists():
        write_theme_report(
            directory,
            stored,
            inputs,
            config.analysis_policy,
            config.families,
            views,
            audience=config.audience,
        )
        return
    # Rebuild through the public publisher, then compare exact immutable bytes.
    import shutil
    import tempfile

    temporary = Path(tempfile.mkdtemp(prefix=".workflow-report-", dir=directory.parent))
    try:
        fresh = temporary / "report"
        write_theme_report(
            fresh,
            stored,
            inputs,
            config.analysis_policy,
            config.families,
            views,
            audience=config.audience,
        )
        manifest = ReportManifest.model_validate_json(
            (fresh / "report.json").read_bytes()
        )
        for name in ("report.json", *(name for name, _ in manifest.artifact_hashes)):
            selected = confined_path(
                config.repo, (directory / name).relative_to(config.repo).as_posix()
            )
            _require(selected.read_bytes() == (fresh / name).read_bytes())
    finally:
        shutil.rmtree(temporary)


def run_theme_workflow(
    config: WorkflowConfig, runtime: WorkflowRuntime, *, now: Callable[[], datetime]
) -> WorkflowResult:
    """Rebind frozen inputs, compose public stages, publish, then append under acquisition lock."""
    phase = "preflight"
    stages, counts, baseline = {}, [], {}
    try:
        _require(
            type(config) is WorkflowConfig and type(runtime) is WorkflowRuntime,
            "malformed_record",
        )
        root = config.repo
        config = WorkflowConfig.model_validate_json(config.model_dump_json())
        validate_paths(config, repo=root)
        stamp = _utc(now())
        expected, bundles, metadata, canonical, raw, book, template = _load_metadata(
            config, runtime
        )
        output = confined_path(config.repo, config.output_dir)
        config_bytes = canonical_json(config.model_dump(mode="json"))
        configuration_path = output / "configuration.json"
        if configuration_path.exists():
            _require(configuration_path.read_bytes() == config_bytes)
        analysis_dir = _stage_directory(config, "analysis", config.stored_analysis)
        existing = read_analysis_run(analysis_dir) if analysis_dir.exists() else None
        for selected in (
            config.stored_extraction,
            config.stored_support,
            config.stored_coding,
        ):
            if selected is not None:
                _stage_directory(config, "unused", selected)
    except Exception as error:  # noqa: BLE001 - checked closed-reason workflow boundary.
        raise WorkflowError(_reason(error)) from None
    states_dir = confined_path(config.repo, config.states_dir)
    try:
        with ProcessLock(states_dir / ".acquire.lock"):
            history = read_runs(states_dir)
            baseline, terminals = _baseline(config, history, existing)
            acquisition = _projections(config, baseline, metadata)
            provenance = analysis_provenance_hash(
                selected_universe_hash=config.universe_hash,
                expected=expected,
                acquisition=acquisition,
                metadata=metadata,
                canonical_snapshots=canonical,
            )
            if not configuration_path.exists():
                write_new(configuration_path, config_bytes)
            phase = "extraction"
            extraction_dir = _stage_directory(
                config, "extraction", config.stored_extraction
            )
            extraction = _extraction(
                config,
                runtime,
                bundles,
                template,
                config.fixture_started_at or stamp,
                extraction_dir,
            )
            stages["extraction"] = _artifact(config, extraction_dir / "run.json")
            counts.append(("extraction", len(extraction.documents)))
            started = config.fixture_started_at or extraction.record.started_at
            sources = SupportSources(extraction, bundles, book, provenance)
            coding_cache = CodingCache(
                confined_path(config.repo, config.coding_cache), "replay"
            )
            support_cache = SupportCache(
                confined_path(config.repo, config.support_cache), "replay"
            )
            phase = "coding"
            coding_dir = _stage_directory(config, "coding", config.stored_coding)
            previous_coding = (
                read_coding_run(coding_dir) if coding_dir.exists() else None
            )
            if previous_coding is None:
                proposal = propose_run(
                    config.coding_run_id,
                    sources,
                    tuple((c.doc_id, c.claim_id) for c in extraction.claims),
                    runtime.classifier,
                    config.coding_policy,
                    config.coding_ceilings,
                    cache=coding_cache,
                    started_at=started,
                    software=config.software,
                )
            else:
                record = previous_coding.record
                _require(
                    record.run_id == config.coding_run_id
                    and record.classifier_identity == config.classifier_identity
                    and record.coding_policy.model_dump()
                    == config.coding_policy.model_dump(exclude={"prompt_text"})
                    and record.ceilings == config.coding_ceilings
                    and record.cache_mode == "replay"
                    and dict(record.software) == config.software
                )
                _require(record.started_at == started)
                _require(
                    record.requested_claim_order
                    == tuple((c.doc_id, c.claim_id) for c in extraction.claims)
                )
                from earnings_themes.coding.records import ProposalRunRecord

                proposal = ProposalRun(
                    ProposalRunRecord.model_validate_json(
                        canonical_json(
                            record.model_dump(
                                mode="json",
                                exclude=set(CodingRunRecord.model_fields)
                                - set(ProposalRunRecord.model_fields),
                            )
                        )
                    ),
                    previous_coding.classifications,
                    previous_coding.attempts,
                    previous_coding.proposals,
                    previous_coding.attributes,
                    previous_coding.novelty,
                )
            counts.append(("coding", len(proposal.classifications)))
            phase = "support"
            support_dir = _stage_directory(config, "support", config.stored_support)
            if not support_dir.exists():
                result = assess_run(
                    config.support_run_id,
                    sources,
                    proposal.targets,
                    runtime.scorer,
                    runtime.judges,
                    config.support_policy,
                    config.support_ceilings,
                    extractor_family=config.extractor_family,
                    cache=support_cache,
                    started_at=started,
                    software=config.software,
                )
                write_support_run(support_dir, result, sources)
            support = read_support_run(support_dir)
            _require(
                support.record.run_id == config.support_run_id
                and support.record.scorer_identity == config.scorer_identity
                and support.record.judge_identities == config.judge_identities
                and support.record.ceilings == config.support_ceilings
                and dict(support.record.software) == config.software
            )
            _require(
                support.record.configuration_hash
                == digest(
                    {
                        "policy": config.support_policy.model_dump(mode="json"),
                        "ceilings": config.support_ceilings.model_dump(mode="json"),
                        "scorer": config.scorer_identity.model_dump(mode="json"),
                        "judges": [
                            i.model_dump(mode="json") for i in config.judge_identities
                        ],
                        "extractor_family": config.extractor_family,
                        "cache_mode": "replay",
                    }
                )
            )
            _require(tuple(t.target for t in support.targets) == proposal.targets)
            _require(support.record.started_at == started)
            reverify_support_run(support, sources)
            stages["support"] = _artifact(config, support_dir / "run.json")
            counts.append(("support", len(support.targets)))
            phase = "coding"
            policy = (
                FixtureSupportingPolicy(proposal, support)
                if config.assignment_policy
                else runtime.assignment_policy
            )
            if config.assignment_policy:
                _require(config.scope == "fixture", "policy_mismatch")
            if previous_coding is None:
                coding = _coding(config, sources, support, proposal, policy)
                write_coding_run(coding_dir, coding, sources, support, policy)
            coding = read_coding_run(coding_dir)
            reverify_coding_run(coding, sources, support, policy)
            stages["coding"] = _artifact(config, coding_dir / "run.json")
            phase = "analysis"
            inputs = AnalysisInputs(
                sources=sources,
                support=support,
                coding=coding,
                assignment_policy=policy,
                expected=expected,
                acquisition=acquisition,
                metadata=metadata,
                copies=config.copies,
                no_theme=config.no_theme,
                provenance_hash=provenance,
                selected_universe_hash=config.universe_hash,
                raw_verification=(),
                raw_caches=RawCacheInputs(coding_cache, support_cache),
                raw_snapshots=raw,
                analysis_policy=config.analysis_policy,
                canonical_snapshots=canonical,
                fixture_authorization=FixtureAuthorization(
                    config.analysis_policy.population_id,
                    config.event_hash,
                    config.pilot_hash,
                    provenance,
                )
                if config.scope == "fixture"
                else None,
            )
            bound = reverify_analysis_inputs(inputs)
            completions = document_completions(bound)
            if terminals:
                by_doc = {c.doc_id: c for c in completions}
                for current in terminals.values():
                    completion = by_doc[current.doc_id]
                    _require(
                        current.completion_hash
                        == digest(completion.model_dump(mode="json"))
                        and current.to_state.value == completion.processing_state,
                        "state_not_processable",
                    )
                    wanted = _transition(
                        config,
                        baseline[current.document_id],
                        completion,
                        existing.manifest_hash,
                        current.recorded_at,
                        current.sequence,
                    )
                    _require(
                        current.missing_reason == wanted.missing_reason
                        and current.processing_reason == wanted.processing_reason,
                        "state_not_processable",
                    )
            views = tuple(
                make_evidence_view(
                    bound,
                    q.span.doc_id,
                    q.quote_id,
                    audience=config.audience,
                    raw_snapshot=next(
                        (s for s in raw if s.doc_id == q.span.doc_id), None
                    ),
                )
                for q in extraction.quotes
            )
            if config.capture and runtime.renderer is not None:
                from dataclasses import asdict

                from earnings_ingestion.browser.policy import ISOLATED_1

                from earnings_pipeline.browser_evidence import capture_evidence_view

                _require(
                    config.capture_policy
                    == json.loads(canonical_json(asdict(ISOLATED_1)))
                )
                read_selected(config, config.installed_binary_reference)
                for view in views:
                    capture_evidence_view(view, runtime.renderer, ISOLATED_1)
            if existing is None:
                write_analysis_run(
                    analysis_dir,
                    build_analysis(inputs, config.analysis_policy, config.families),
                    inputs,
                    config.analysis_policy,
                    config.families,
                    tuple(v.reference for v in views),
                )
            stored = read_analysis_run(analysis_dir)
            reverify_analysis_run(
                stored, inputs, config.analysis_policy, config.families
            )
            stages["analysis"] = _artifact(config, analysis_dir / "run.json")
            counts.append(
                ("analysis", sum(f.height for f in stored.tables.frames.values()))
            )
            phase = "publication"
            report_dir = output / "report"
            _checked_report(config, report_dir, stored, inputs, views)
            stages["report"] = _artifact(config, report_dir / "report.json")
            phase = "state"
            # Recheck actual originals and combined history immediately before append.
            _load_metadata(config, runtime)
            _require(read_runs(states_dir) == history, "state_not_processable")
            if terminals:
                state_paths = {
                    states_dir / (r.run_id + ".parquet") for r in terminals.values()
                }
                _require(len(state_paths) == 1, "state_not_processable")
                return _receipt(
                    config,
                    status="no_state_change"
                    if config.stored_analysis
                    else "state_recorded",
                    stamp=stamp,
                    stages=stages,
                    state=_artifact(config, state_paths.pop()),
                    count=0,
                    counts=counts,
                )
            transitions = tuple(
                _transition(
                    config,
                    baseline[c.event_id + ":release"],
                    c,
                    stored.manifest_hash,
                    stamp,
                    i,
                )
                for i, c in enumerate(completions)
            )
            if not transitions:
                return _receipt(
                    config,
                    status="no_state_change",
                    stamp=stamp,
                    stages=stages,
                    counts=counts,
                )
            check_histories([*history, *transitions])
            try:
                path = write_processing_run(states_dir, transitions)
            except Exception as error:  # noqa: BLE001 - checked closed-reason workflow boundary.
                return _receipt(
                    config,
                    status="state_pending",
                    stamp=stamp,
                    stages=stages,
                    reason=_reason(error),
                    counts=counts,
                )
            return _receipt(
                config,
                status="state_recorded",
                stamp=stamp,
                stages=stages,
                state=_artifact(config, path),
                count=len(transitions),
                counts=counts,
            )
    except Exception as error:  # noqa: BLE001 - checked closed-reason workflow boundary.
        reason = _reason(error)
        failure = WorkflowFailure(
            run_id=config.run_id,
            phase=phase,
            event_ids=config.selected_event_ids,
            doc_ids=tuple(sorted(b.document.doc_id for b in bundles)),
            reason=reason,
            completed_stages=tuple(stages[k] for k in sorted(stages)),
            usage_availability="unreported",
            created_at=stamp,
        )
        stages["failure"] = _publish_metadata(config, "failure", failure)
        state = None
        count = 0
        try:
            with ProcessLock(states_dir / ".acquire.lock"):
                current = current_states(read_runs(states_dir), config.pilot_hash)
                affected = [
                    s for s in baseline.values() if s.to_state is DocumentState.PARSED
                ]
                _require(
                    all(current[s.document_id] == s for s in affected),
                    "state_not_processable",
                )
                # After analytical publication, failures remain state_pending.
                if "analysis" in stages:
                    return _receipt(
                        config,
                        status="state_pending",
                        stamp=stamp,
                        stages=stages,
                        reason=reason,
                        counts=counts,
                    )
                rows = tuple(
                    ProcessingTransition.model_validate_json(
                        canonical_json(
                            s.model_dump(mode="json")
                            | {
                                "schema_version": 2,
                                "run_id": config.run_id,
                                "sequence": i,
                                "recorded_at": stamp,
                                "from_state": "parsed",
                                "to_state": "failed",
                                "missing_reason": "processing_failed",
                                "failure_reason": None,
                                "attempts": [],
                                "processing_run_id": config.run_id,
                                "processing_run_hash": stages["failure"].sha256,
                                "completion_hash": digest(
                                    {
                                        "kind": "WorkflowFailure",
                                        "sha256": stages["failure"].sha256,
                                        "doc_id": s.doc_id,
                                    }
                                ),
                                "processing_reason": reason
                                if reason
                                in {
                                    "unexpected_error",
                                    "storage_corrupt",
                                    "input_changed",
                                }
                                else "unexpected_error",
                            }
                        )
                    )
                    for i, s in enumerate(affected)
                )
                if rows:
                    path = write_processing_run(states_dir, rows)
                    state, count = _artifact(config, path), len(rows)
        except Exception:  # noqa: BLE001 - failure recording must preserve the original closed refusal.
            reason = "state_not_processable"
        return _receipt(
            config,
            status="failed",
            stamp=stamp,
            stages=stages,
            state=state,
            count=count,
            reason=reason,
            counts=counts,
        )
