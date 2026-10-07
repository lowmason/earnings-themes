"""docs/data-dictionary.md documents every field and value of the core contracts
and of the ingestion records: the canonicalizer's, the capture's, layout-1's, the
retrieval metadata, the cohort's records and curated files, and Stage 5's event,
pilot, processing-state, and coverage records; and earnings-themes' Stage 6 records
and Stages 7–9's extraction, support, and coding records.

AGENTS.md §191: document public interfaces and update the data dictionary in the
same change. A contract that gains, loses, or renames a field fails here.
"""

import re
from dataclasses import fields
from enum import StrEnum
from pathlib import Path

import earnings_core as core
import earnings_ingestion.canonical as ingestion
import pytest
from earnings_ingestion import browser, layout
from earnings_ingestion.cohort import config as cohort_config
from earnings_ingestion.cohort import records as cohort
from earnings_ingestion.cohort import register as cohort_register
from earnings_ingestion.events import acceptance, coverage, states
from earnings_ingestion.events import records as events
from earnings_ingestion.fetch import records as fetch
from earnings_themes import annotation, codebook, gold, problems, split
from earnings_themes import records as themes
from earnings_themes.analysis import records as analysis
from earnings_themes.analysis.problems import ANALYSIS_REASONS
from earnings_themes.anchoring import SpanPointer
from earnings_themes.coding import records as coding
from earnings_themes.coding.cache import CodingCacheEntry
from earnings_themes.coding.decide import DecisionInput, DecisionSet
from earnings_themes.coding.input import CodingInput
from earnings_themes.coding.run import ProposalRun
from earnings_themes.coding.store import SCHEMAS
from earnings_themes.extraction import adapters, cache, local
from earnings_themes.extraction import records as extraction
from earnings_themes.extraction.store import StoredRun
from earnings_themes.support import judges, metrics, scorers
from earnings_themes.support import records as support
from earnings_themes.support.cache import SupportCacheEntry
from earnings_themes.support.nli import LocalScorerConfig
from earnings_themes.support.problems import SupportProblem
from pydantic import BaseModel

DICTIONARY = Path(__file__).resolve().parents[2] / "docs" / "data-dictionary.md"
MODELS = [
    core.TextSpan,
    core.ArtifactRef,
    core.CanonicalDocument,
    core.TableCellContext,
    core.DocumentElement,
    core.SpanLocator,
    core.TextChunk,
    core.SpanCandidate,
    core.VerifiedSpan,
    core.OverlayMask,
    core.MaskedDocument,
    core.Rejection,
    ingestion.CanonicalizationManifest,
    ingestion.CanonicalizationFailure,
    ingestion.Canonicalized,
    browser.RenderedCapture,
    browser.BlockedRequest,
    browser.LayoutMetadata,
    browser.LayoutBlock,
    browser.LayoutRun,
    browser.LayoutTable,
    browser.LayoutRow,
    browser.LayoutCell,
    layout.AlignmentFailure,
    layout.LayoutExtraction,
    fetch.Retrieval,
    cohort.EvidenceLocator,
    cohort.Citation,
    cohort.SourceRights,
    cohort.CitedIdentity,
    cohort.SecurityRecord,
    cohort.MembershipAssertion,
    cohort.MembershipInterval,
    cohort.IssuerCandidate,
    cohort.IssuerMapping,
    cohort.Issuer,
    cohort.OverrideCitation,
    cohort.Override,
    cohort.Finding,
    cohort.SnapshotReconciliation,
    cohort.CohortReport,
    cohort.UniverseDefinition,
    cohort.UniverseManifest,
    cohort.LiveCheck,
    cohort.LiveVerification,
    cohort_config.UniverseConfig,
    cohort_config.EtfProxy,
    cohort_config.EvidenceFile,
    cohort_config.SnapshotEvidence,
    cohort_config.ChangeEvidence,
    cohort_config.Row,
    cohort_config.ChangeRow,
    cohort_config.CheckList,
    cohort_config.CheckMember,
    cohort_config.OverridesFile,
    cohort_register.MembershipRegister,
    cohort_register.RegisterEntry,
    events.EventRow,
    events.EventFinding,
    events.EventOverride,
    events.EventOverridesFile,
    events.AcquisitionOverride,
    events.AcquisitionOverridesFile,
    events.EventManifestDefinition,
    events.EventManifest,
    events.FileEvidence,
    events.SkippedPage,
    events.EventCitations,
    events.EventEvidence,
    events.PilotRow,
    events.MembershipTransition,
    events.PilotDefinition,
    events.PilotManifest,
    states.ExhibitAttempt,
    states.StateTransition,
    states.ProcessingTransition,
    coverage.PilotPin,
    coverage.StateCount,
    coverage.CoverageGap,
    coverage.AppliedOverride,
    coverage.NoThemeCount,
    coverage.CoverageReport,
    themes.Pin,
    split.SplitWindow,
    split.SplitEvent,
    split.SplitRow,
    split.SplitManifest,
    SpanPointer,
    codebook.ExamplePointer,
    codebook.Example,
    codebook.Theme,
    codebook.DiscoveryCorpus,
    codebook.CodebookRules,
    codebook.Approval,
    codebook.DraftingAid,
    codebook.Codebook,
    codebook.ExampleDraft,
    codebook.ThemeDraft,
    codebook.CodebookDraft,
    gold.GoldQuote,
    gold.GoldClaim,
    gold.GoldAssignment,
    gold.HardNegative,
    gold.ReleaseIdentification,
    gold.DraftCounts,
    gold.CodebookRef,
    gold.Gold,
    gold.FixtureNegatives,
    gold.HardNegativeSet,
    annotation.QuoteDraft,
    annotation.ClaimDraft,
    annotation.AssignmentDraft,
    annotation.HardNegativeDraft,
    annotation.GoldDraft,
    annotation.FixtureDraft,
    annotation.CuratedDraft,
    extraction.Parameters,
    extraction.AdapterIdentity,
    extraction.ExtractionPolicy,
    extraction.Ceilings,
    extraction.RunConfiguration,
    extraction.Quote,
    extraction.Claim,
    extraction.ExtractionRejection,
    extraction.Visit,
    extraction.WindowRecord,
    extraction.DocumentRecord,
    extraction.RunRecord,
    adapters.Usage,
    adapters.ModelReply,
    cache.CacheKey,
    cache.CacheEntry,
    local.LocalModelConfig,
    judges.JudgeSubject,
    judges.JudgeRequest,
    scorers.ScoreRequest,
    scorers.ScoreReply,
    SupportCacheEntry,
    metrics.HumanLabel,
    metrics.ContinuousSignal,
    metrics.Acceptance,
    metrics.MetricReport,
    support.CodebookReference,
    support.Target,
    support.ThemeSnapshot,
    support.EvidenceReference,
    support.ContextReference,
    support.TargetRecord,
    support.FileHash,
    support.RuntimeIdentity,
    support.WeightLicense,
    support.ScorerIdentity,
    support.JudgeIdentity,
    support.EntailmentSignal,
    support.QuoteAssessment,
    support.JudgeAnswer,
    support.JudgeAttempt,
    support.JudgeTrial,
    support.ReviewOutcome,
    support.SupportCeilings,
    support.UsageRecord,
    support.SupportPolicy,
    support.SupportRunRecord,
    LocalScorerConfig,
    coding.CodingPart,
    coding.CodingRecord,
    coding.CodingAttributes,
    coding.CodingReply,
    coding.CodingSubject,
    coding.CodingRequest,
    coding.ProposalRecord,
    coding.AttributeRecord,
    coding.NoveltyItem,
    CodingCacheEntry,
    coding.CodingPolicy,
    coding.CodingPolicySnapshot,
    coding.CodingCeilings,
    coding.ClassificationRecord,
    coding.CodingAttempt,
    coding.ProposalRunRecord,
    coding.PolicyReference,
    coding.PolicyVote,
    coding.AssignmentDecision,
    coding.Assignment,
    coding.AssignmentClaimLink,
    coding.CodingRunRecord,
]
ENUMS = [
    core.RightsStatus,
    core.ElementType,
    core.TextOrigin,
    core.MaskCategory,
    core.RejectionReason,
    ingestion.FailureReason,
    browser.CaptureStatus,
    browser.CaptureReason,
    fetch.RetrievalMethod,
    cohort.EvidenceClass,
    cohort.SourceRole,
    cohort.LocatorKind,
    cohort.BoundTiming,
    cohort.BoundBasis,
    cohort.AssertedAction,
    cohort.AssertionStatus,
    cohort.ResolutionStatus,
    cohort.ResolutionMethod,
    cohort.OverrideKind,
    cohort.FindingKind,
    acceptance.Convention,
    events.EventStatus,
    events.EventReason,
    events.IdentificationMethod,
    events.EventFindingKind,
    events.EventOverrideKind,
    events.SelectionReason,
    events.TransitionKind,
    states.DocumentState,
    states.MissingReason,
    states.ProcessingMissingReason,
    states.ProcessingReason,
    states.ExhibitChoice,
    states.AttemptOutcome,
    problems.Problem,
    split.Partition,
    split.ExclusionReason,
    codebook.CodebookStatus,
    gold.Origin,
    gold.Support,
    gold.ReleaseLabel,
    gold.NegativeKind,
    extraction.ExtractionProblem,
    extraction.WindowOutcome,
    extraction.DocumentOutcome,
    SupportProblem,
    support.SignalStatus,
    support.Presentation,
    support.ReviewStatus,
    support.ReasonCode,
    coding.CodingProblem,
]
CODING_DATACLASSES = [
    support.SupportSources,
    CodingInput,
    ProposalRun,
    DecisionInput,
    DecisionSet,
    coding.CodingRun,
]


def documented(name: str) -> set[str]:
    """The first-column code spans of the table under the heading for ``name``."""
    text = DICTIONARY.read_text(encoding="utf-8")
    heading = f"### `{name}`\n"
    assert heading in text, f"docs/data-dictionary.md has no section for {name}"
    section = text.split(heading, 1)[1].split("\n#", 1)[0]
    return set(re.findall(r"^\| `([^`]+)` \|", section, flags=re.MULTILINE))


@pytest.mark.parametrize("model", MODELS, ids=lambda model: model.__name__)
def test_every_field_is_documented(model: type[BaseModel]) -> None:
    assert documented(model.__name__) == set(model.model_fields)


@pytest.mark.parametrize("enum", ENUMS, ids=lambda enum: enum.__name__)
def test_every_value_is_documented(enum: type[StrEnum]) -> None:
    assert documented(enum.__name__) == {member.value for member in enum}


def test_coding_registry_covers_every_defined_record_and_enum() -> None:
    models = {
        value
        for value in vars(coding).values()
        if isinstance(value, type)
        and issubclass(value, BaseModel)
        and value.__module__ == coding.__name__
    }
    enums = {
        value
        for value in vars(coding).values()
        if isinstance(value, type)
        and issubclass(value, StrEnum)
        and value.__module__ == coding.__name__
    }
    assert models == {model for model in MODELS if model.__module__ == coding.__name__}
    assert enums == {enum for enum in ENUMS if enum.__module__ == coding.__name__}
    assert CodingCacheEntry in MODELS


@pytest.mark.parametrize(
    "record", CODING_DATACLASSES, ids=lambda record: record.__name__
)
def test_coding_transient_fields_are_documented(record: type) -> None:
    assert documented(record.__name__) == {field.name for field in fields(record)}


def test_coding_table_registry_and_grains_are_documented() -> None:
    assert documented("Coding tables") == set(SCHEMAS)
    assert {field.name for field in fields(coding.CodingRun)} == {"record", *SCHEMAS}
    text = DICTIONARY.read_text(encoding="utf-8")
    grains = {
        "classifications": "(coding_run_id, doc_id, claim_id)",
        "attempts": "(classification_id, attempt)",
        "proposals": "(coding_run_id, doc_id, claim_id, theme_id)",
        "attributes": "(coding_run_id, doc_id, claim_id)",
        "decisions": "(coding_run_id, target_id)",
        "assignments": "(coding_run_id, codebook_id, codebook_version, doc_id, theme_id, quote_id)",
        "assignment_claims": "(assignment_id, doc_id, claim_id, decision_id)",
        "novelty": "(coding_run_id, classification_id)",
    }
    section = text.split("### `Coding tables`\n", 1)[1].split("\n#", 1)[0]
    for table, grain in grains.items():
        assert f"| `{table}` | `{grain}` |" in section


def test_the_documented_versions_are_the_packages() -> None:
    text = DICTIONARY.read_text(encoding="utf-8")
    assert f"schema version {core.SCHEMA_VERSION}\n" in text
    assert f'`"{core.VALIDATOR_VERSION}"` (`earnings_core.VALIDATOR_VERSION`)' in text
    assert (
        f"## earnings-ingestion records, schema version"
        f" {ingestion.INGESTION_SCHEMA_VERSION}\n" in text
    )
    assert (
        f"## earnings-themes records, schema version {themes.THEMES_SCHEMA_VERSION}\n"
        in text
    )
    assert (
        f"## earnings-themes extraction records, schema version"
        f" {extraction.EXTRACTION_SCHEMA_VERSION}\n" in text
    )


def test_the_documented_support_versions_are_the_package() -> None:
    text = DICTIONARY.read_text(encoding="utf-8")
    assert (
        f"## earnings-themes support records, schema version {support.SUPPORT_SCHEMA_VERSION}\n"
        in text
    )
    assert (
        f'`"{support.SUPPORT_VERSION}"` (`earnings_themes.support.records.SUPPORT_VERSION`)'
        in text
    )


def test_the_documented_coding_versions_are_the_package() -> None:
    text = DICTIONARY.read_text(encoding="utf-8")
    assert (
        f"## earnings-themes coding records, schema version {coding.CODING_SCHEMA_VERSION}\n"
        in text
    )
    assert (
        f'`"{coding.CODING_VERSION}"` (`earnings_themes.coding.records.CODING_VERSION`)'
        in text
    )


def test_extraction_stored_run_and_gate_are_documented() -> None:
    assert documented("StoredRun") == {field.name for field in fields(StoredRun)}
    text = DICTIONARY.read_text(encoding="utf-8")
    assert "validate_stored_run(run: StoredRun) -> StoredRun" in text
    assert "malformed_record" in text and "storage_corrupt" in text


ANALYSIS_MODELS = [
    analysis.AnalysisPart,
    analysis.ExpectedEvent,
    analysis.AcquisitionStatus,
    analysis.DocumentMetadata,
    analysis.CopyAssertion,
    analysis.AnalysisPolicy,
    analysis.ThemeFamilyMap,
    analysis.NoThemeDeclaration,
    analysis.DocumentCompletion,
    analysis.EvidenceViewReference,
    analysis.CaptureObservation,
    analysis.RawCacheVerification,
    analysis.AnalysisRunRecord,
    analysis.Observation,
    analysis.QuoteAudit,
    analysis.ClaimAudit,
    analysis.ClaimEvidence,
    analysis.ClassificationAudit,
    analysis.DecisionAudit,
    analysis.RejectionAudit,
    analysis.CoverageRow,
    analysis.PrevalenceRow,
    analysis.CopyRow,
]
ANALYSIS_DATACLASSES = [
    analysis.RawSnapshot,
    analysis.CanonicalSnapshot,
    analysis.FixtureAuthorization,
    analysis.RawCacheInputs,
    analysis.AnalysisInputs,
    analysis.BoundAnalysis,
    analysis.AnalysisTables,
    analysis.AnalysisRun,
    analysis.StoredAnalysisRun,
    analysis.EvidenceView,
]


@pytest.mark.parametrize("model", ANALYSIS_MODELS, ids=lambda model: model.__name__)
def test_analysis_fields_documented(model):
    assert documented(model.__name__) == set(model.model_fields)


@pytest.mark.parametrize(
    "model", ANALYSIS_DATACLASSES, ids=lambda model: model.__name__
)
def test_analysis_container_fields_documented(model):
    assert documented(model.__name__) == {field.name for field in fields(model)}


def test_analysis_registry_is_complete():
    models = {
        value
        for value in vars(analysis).values()
        if isinstance(value, type)
        and issubclass(value, BaseModel)
        and value.__module__ == analysis.__name__
    }
    assert models == set(ANALYSIS_MODELS)
    assert documented("Analysis tables") == set(analysis.TABLE_SCHEMAS)
    assert documented("Analysis reasons") == ANALYSIS_REASONS


@pytest.mark.parametrize(
    "table", tuple(analysis.TABLE_SCHEMAS), ids=tuple(analysis.TABLE_SCHEMAS)
)
def test_analysis_table_dtypes_and_foreign_keys_documented(table):
    text = DICTIONARY.read_text(encoding="utf-8")
    section = text.split(f"### `Analysis table {table}`\n", 1)[1].split("\n#", 1)[0]
    assert documented("Analysis table " + table) == set(analysis.TABLE_SCHEMAS[table])
    for field, dtype in analysis.TABLE_SCHEMAS[table].items():
        assert f"| `{field}` | `{dtype}` |" in section
    assert repr(analysis.TABLE_GRAINS[table]) in section
    assert repr(analysis.TABLE_FOREIGN_KEYS[table]) in section


def test_analysis_final_validation_gate_is_documented():
    text = DICTIONARY.read_text(encoding="utf-8")
    assert "validate_analysis_tables(tables: AnalysisTables) -> AnalysisTables" in text
    assert "AnalysisRun" in text and "StoredAnalysisRun" in text
    assert "Task 6 builds completion, coverage and prevalence" in text
    assert "Task 8 owns storage, serialization, reverification and publication" in text
    assert "Task 6 storage/serialization" not in text


def test_analysis_consuming_gate_and_c2_hashes_documented():
    text = DICTIONARY.read_text(encoding="utf-8")
    assert "reverify_analysis_inputs(inputs: AnalysisInputs) -> BoundAnalysis" in text
    assert "analysis_provenance_hash" in text
    assert "schema 1 binds judge cache files" in text
    assert "application validates original event/pilot/state derivation" in text


def test_processing_schema_two_is_additive_and_documented():
    from earnings_ingestion.events.state_table import PROCESSING_SCHEMA, SCHEMA

    text = DICTIONARY.read_text(encoding="utf-8")
    assert documented("Processing table") == set(PROCESSING_SCHEMA)
    section = text.split("### `Processing table`\n", 1)[1].split("\n#", 1)[0]
    for field, dtype in PROCESSING_SCHEMA.items():
        assert f"| `{field}` | `{dtype}` |" in section
    assert set(PROCESSING_SCHEMA) == set(SCHEMA) | {
        "processing_run_id",
        "processing_run_hash",
        "completion_hash",
        "processing_reason",
    }
    assert "write_processing_run" in text and "StateRecord" in text
    assert "schema-1 writer bytes" in text
    assert "WorkflowFailure" in text and "DocumentCompletion" in text
    assert "parsed_documents(transitions, pilot_hash)" in text
    assert "Schema-1 parse failure recovery" in text
    assert "canonical availability, not analytical" in text


def test_analysis_row_projection_interface_and_null_refusal_documented():
    import inspect

    import earnings_themes.analysis as public

    assert tuple(inspect.signature(public.build_observations).parameters) == ("bound",)
    text = DICTIONARY.read_text(encoding="utf-8")
    assert "build_observations(bound: BoundAnalysis) -> AnalysisTables" in text
    section = text.split("### `RejectionAudit`\n", 1)[1].split("\n### ", 1)[0]
    assert "| `window_id` | `string or null` |" in section
    assert "a-{window_id}-{attempt}" in section
    assert (
        "copy_processing_conflict" in text.split("### Analytical row projection", 1)[1]
    )


def test_task6_public_completion_and_selected_universe_documented():
    text = DICTIONARY.read_text(encoding="utf-8")
    for name in (
        "document_completions",
        "build_coverage",
        "prevalence",
        "build_analysis",
        "selected_universe_hash",
        "operative_hash",
        "equal_issuer_mean",
        "completed-no-theme",
    ):
        assert name in text


def test_evidence_preparation_and_capture_boundaries_documented():
    text = DICTIONARY.read_text(encoding="utf-8")
    assert "make_evidence_view(bound: BoundAnalysis" in text
    assert "raw_snapshot: RawSnapshot | None" in text
    assert "capture_evidence_view(view: EvidenceView" in text
    assert "canonical-evidence-html/1" in text
    assert "raw_snapshot_missing" in text
    assert "prepared capture" in text


def test_snapshot_withholding_and_nested_export_rights_documented():
    text = DICTIONARY.read_text(encoding="utf-8")
    section = text.split("### `EvidenceViewReference`", 1)[1].split(
        "### `CaptureObservation`", 1
    )[0]
    assert "snapshot_withheld" in section
    assert "forbidden nested artifact" in text
    reasons = text.split("### `Analysis reasons`", 1)[1].split(
        "### `Analysis tables`", 1
    )[0]
    assert "\n\n| `browser_unavailable`" not in reasons
