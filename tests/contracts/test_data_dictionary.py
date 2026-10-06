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
from earnings_themes.anchoring import SpanPointer
from earnings_themes.coding import records as coding
from earnings_themes.coding.cache import CodingCacheEntry
from earnings_themes.coding.decide import DecisionInput, DecisionSet
from earnings_themes.coding.input import CodingInput
from earnings_themes.coding.run import ProposalRun
from earnings_themes.coding.store import SCHEMAS
from earnings_themes.extraction import adapters, cache, local
from earnings_themes.extraction import records as extraction
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
