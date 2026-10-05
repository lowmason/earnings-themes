"""Pointer extraction over documents and a run (the Stage 7 spec, §Units, §Ceilings,
and §Records; ES21; T6-M4).

- **A document.** If ``bundle_problems`` reports anything, the document fails with
  one rejection per reason, and nothing is called: Stage 7 is that function's first
  production caller. Otherwise its windows are extracted in order, under what the
  document may spend. A document with no unit completes with zero windows; one whose
  every window failed fails, and one with some failed is partial (R1.4).
- **A run.** Every run passes its ceilings explicitly: requests per document,
  requests per run, and reported tokens per run. Each document may spend the lesser
  of its own ceiling and what the run has left, so exhaustion stops dispatch, and
  each window it leaves unsent fails as ``budget_exhausted`` (ES21; A §691).
- **The run record.** Its configuration and hash, its documents, its counts, the
  rejections by reason, its usage, whether a ceiling stopped a dispatch, and the
  software identity the caller passes. No quote retained means no exactness rate
  (R6.2, R12.8).
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from earnings_core import VALIDATOR_VERSION, Rejection, RejectionReason, digest

from earnings_themes.anchoring import Bundle, bundle_problems
from earnings_themes.extraction.adapters import ModelAdapter
from earnings_themes.extraction.extract import (
    Allowance,
    WindowJob,
    WindowResult,
    extract_window,
)
from earnings_themes.extraction.prompt import REPLY_SCHEMA, PromptTemplate
from earnings_themes.extraction.records import (
    EXTRACTOR_VERSION,
    Ceilings,
    Claim,
    DocumentOutcome,
    DocumentRecord,
    ExtractionPolicy,
    ExtractionRejection,
    Quote,
    RunConfiguration,
    RunRecord,
    Visit,
    WindowOutcome,
    WindowRecord,
)
from earnings_themes.extraction.windows import plan_windows

BUNDLE_PROBLEM = "reported by bundle_problems"


@dataclass(frozen=True)
class DocumentResult:
    record: DocumentRecord
    windows: tuple[WindowResult, ...] = ()
    rejections: tuple[ExtractionRejection, ...] = ()
    """The document's own: one per reason ``bundle_problems`` reported."""

    @property
    def requests(self) -> int:
        return sum(w.record.requests for w in self.windows)

    @property
    def tokens(self) -> int:
        return sum(
            w.record.prompt_tokens + w.record.completion_tokens for w in self.windows
        )


def extract_document(
    bundle: Bundle,
    adapter: ModelAdapter,
    policy: ExtractionPolicy,
    template: PromptTemplate,
    allowance: Allowance,
) -> DocumentResult:
    """One document, its windows in order, under ``allowance``."""
    document = bundle.document
    problems = bundle_problems(bundle)
    if problems:
        refused = tuple(
            ExtractionRejection(
                doc_id=document.doc_id,
                rejection=Rejection(
                    reason=RejectionReason(problem), detail=BUNDLE_PROBLEM
                ),
            )
            for problem in problems
        )
        record = DocumentRecord(
            doc_id=document.doc_id,
            canonical_hash=document.canonical_hash,
            outcome=DocumentOutcome.FAILED,
            units=0,
            windows=0,
            windows_failed=0,
            candidates=0,
            quotes=0,
            claims=0,
            rejections=len(refused),
        )
        return DocumentResult(record=record, rejections=refused)
    results: list[WindowResult] = []
    requests = tokens = 0
    for window in plan_windows(bundle, policy.window_budget):
        left = Allowance(allowance.requests - requests, allowance.tokens - tokens)
        result = extract_window(
            WindowJob(bundle, window, template, left), adapter, policy
        )
        requests += result.record.requests
        tokens += result.record.prompt_tokens + result.record.completion_tokens
        results.append(result)
    failed = sum(r.record.outcome is WindowOutcome.FAILED for r in results)
    if not failed:
        outcome = DocumentOutcome.COMPLETED
    elif failed == len(results):
        outcome = DocumentOutcome.FAILED
    else:
        outcome = DocumentOutcome.PARTIAL
    record = DocumentRecord(
        doc_id=document.doc_id,
        canonical_hash=document.canonical_hash,
        outcome=outcome,
        units=sum(len(r.record.unit_ids) for r in results),
        windows=len(results),
        windows_failed=failed,
        candidates=sum(r.candidates for r in results),
        quotes=sum(len(r.quotes) for r in results),
        claims=sum(len(r.claims) for r in results),
        rejections=sum(len(r.rejections) for r in results),
    )
    return DocumentResult(record=record, windows=tuple(results))


@dataclass(frozen=True)
class RunResult:
    """A run's record, and each kind of record it holds, in order."""

    record: RunRecord
    documents: tuple[DocumentResult, ...] = ()

    @property
    def document_records(self) -> tuple[DocumentRecord, ...]:
        return tuple(d.record for d in self.documents)

    @property
    def windows(self) -> tuple[WindowRecord, ...]:
        return tuple(w.record for d in self.documents for w in d.windows)

    @property
    def quotes(self) -> tuple[Quote, ...]:
        return tuple(q for d in self.documents for w in d.windows for q in w.quotes)

    @property
    def claims(self) -> tuple[Claim, ...]:
        return tuple(c for d in self.documents for w in d.windows for c in w.claims)

    @property
    def rejections(self) -> tuple[ExtractionRejection, ...]:
        return tuple(
            r
            for d in self.documents
            for r in (*d.rejections, *(r for w in d.windows for r in w.rejections))
        )

    @property
    def visits(self) -> tuple[Visit, ...]:
        return tuple(v for d in self.documents for w in d.windows for v in w.visits)


def extract_run(
    bundles: Sequence[Bundle],
    adapter: ModelAdapter,
    policy: ExtractionPolicy,
    template: PromptTemplate,
    ceilings: Ceilings,
    *,
    run_id: str,
    started_at: datetime,
    software: Mapping[str, str],
) -> RunResult:
    """Every document in order, under the run's ceilings, with its run record."""
    doc_ids = [bundle.document.doc_id for bundle in bundles]
    if len(set(doc_ids)) != len(doc_ids):
        raise ValueError("a run holds each document once")
    documents: list[DocumentResult] = []
    requests = tokens = 0
    for bundle in bundles:
        allowance = Allowance(
            requests=min(
                ceilings.requests_per_document, ceilings.requests_per_run - requests
            ),
            tokens=ceilings.tokens_per_run - tokens,
        )
        result = extract_document(bundle, adapter, policy, template, allowance)
        requests += result.requests
        tokens += result.tokens
        documents.append(result)
    configuration = RunConfiguration(
        identity=adapter.identity,
        policy=policy,
        ceilings=ceilings,
        prompt_sha256=template.sha256,
        reply_schema_sha256=digest(REPLY_SCHEMA),
        extractor_version=EXTRACTOR_VERSION,
        validator_version=VALIDATOR_VERSION,
        codebook_hash=None,
    )
    windows = [w.record for d in documents for w in d.windows]
    reasons = Counter(
        r.reason
        for d in documents
        for r in (*d.rejections, *(r for w in d.windows for r in w.rejections))
    )
    quotes = sum(d.record.quotes for d in documents)
    record = RunRecord(
        run_id=run_id,
        started_at=started_at,
        configuration=configuration,
        configuration_hash=digest(configuration),
        documents={d.record.doc_id: d.record.canonical_hash for d in documents},
        units=sum(d.record.units for d in documents),
        windows=len(windows),
        candidates=sum(d.record.candidates for d in documents),
        quotes=quotes,
        claims=sum(d.record.claims for d in documents),
        rejections_by_reason=dict(sorted(reasons.items())),
        requests=sum(w.requests for w in windows),
        cache_hits=sum(w.cache_hits for w in windows),
        prompt_tokens=sum(w.prompt_tokens for w in windows),
        completion_tokens=sum(w.completion_tokens for w in windows),
        unreported=sum(w.unreported for w in windows),
        exhausted=any(w.exhausted for w in windows),
        software=dict(software),
        exactness_rate=1.0 if quotes else None,
    )
    return RunResult(record=record, documents=tuple(documents))
