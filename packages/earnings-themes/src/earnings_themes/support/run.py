"""Caller-ordered support assessment with run-level metadata preflight."""

from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime

from earnings_core import VALIDATOR_VERSION, digest, sha256_hex

from earnings_themes.support.allowance import Allowance
from earnings_themes.support.assess import _refused_result, assess_target
from earnings_themes.support.cache import SupportCache
from earnings_themes.support.judges import Judge, validate_panel
from earnings_themes.support.problems import SupportError, unexpected_error
from earnings_themes.support.records import (
    SUPPORT_VERSION,
    AssessmentResult,
    CodebookReference,
    ReasonCode,
    RefusedTarget,
    ScorerIdentity,
    SupportCeilings,
    SupportPolicy,
    SupportRunRecord,
    SupportRunResult,
    SupportSources,
    Target,
    UsageRecord,
)
from earnings_themes.support.resolve import _source_hash, _validated, resolve_target
from earnings_themes.support.scorers import EntailmentScorer


def accounting(
    assessments: Sequence[AssessmentResult], usage: Sequence[UsageRecord]
) -> dict:
    """Manifest totals retain cached usage apart from newly dispatched usage."""
    fresh = [u for u in usage if not u.cached]
    statuses = Counter(a.outcome.status for a in assessments)
    reason_codes = {code.value for code in ReasonCode}
    reasons = Counter(
        reason
        for a in assessments
        for reason in set(a.outcome.missing) | (set(a.outcome.flags) & reason_codes)
    )
    return {
        "counts_by_status": tuple(sorted(statuses.items())),
        "counts_by_reason": tuple(sorted(reasons.items())),
        "evaluations": sum(u.kind == "scorer" for u in fresh),
        "requests": sum(u.kind == "judge" for u in fresh),
        "prompt_tokens": sum(u.actual_prompt_tokens or 0 for u in fresh),
        "completion_tokens": sum(u.actual_completion_tokens or 0 for u in fresh),
        "reserved_tokens": sum(u.reserved_tokens for u in fresh),
        "unreported": sum(u.unreported for u in fresh),
        "cache_hits": sum(u.cached for u in usage),
    }


def assess_run(
    run_id: str,
    sources: SupportSources,
    targets: Sequence[Target],
    scorer: EntailmentScorer,
    judges: tuple[Judge, Judge],
    policy: SupportPolicy,
    ceilings: SupportCeilings,
    *,
    extractor_family: str,
    cache: SupportCache,
    started_at: datetime,
    software: Mapping[str, str],
) -> SupportRunResult:
    """Validate the entire run configuration, then resolve and assess in order.

    Unexpected mid-dispatch failures abort the run; completed cache entries and
    reservations remain intact. They never become zero-dispatch refused rows.
    """
    try:
        identities = validate_panel(extractor_family, tuple(j.identity for j in judges))
        policy = _validated(policy, SupportPolicy)
        ceilings = _validated(ceilings, SupportCeilings)
        identity = _validated(scorer.identity, ScorerIdentity)
        if sha256_hex(policy.prompt_text.encode()) != policy.prompt_hash:
            raise SupportError("input_changed")
        if type(sources) is not SupportSources or type(sources.bundles) is not tuple:
            raise SupportError("malformed_record")
        targets = tuple(_validated(t, Target) for t in targets)
        if len({digest(t.model_dump(mode="json")) for t in targets}) != len(targets):
            raise SupportError("invalid_references")
        reference = CodebookReference(
            codebook_id=sources.codebook.codebook_id,
            codebook_version=sources.codebook.codebook_version,
            content_hash=sources.codebook.content_hash,
        )
        if any(t.source_run_id != sources.stored_run.record.run_id for t in targets):
            raise SupportError("wrong_source_run")
        if any(t.codebook != reference for t in targets):
            raise SupportError("wrong_codebook")
        if any(type(k) is not str or type(v) is not str for k, v in software.items()):
            raise SupportError("malformed_record")
        documents = tuple(sorted(sources.stored_run.record.documents.items()))
        configuration = {
            "policy": policy.model_dump(mode="json"),
            "ceilings": ceilings.model_dump(mode="json"),
            "scorer": identity.model_dump(mode="json"),
            "judges": [j.model_dump(mode="json") for j in identities],
            "extractor_family": extractor_family,
            "cache_mode": cache.mode,
        }
        # Construct the strict manifest before resolving any target or dispatching.
        record = _validated(
            SupportRunRecord.model_construct(
                run_id=run_id,
                started_at=started_at,
                source_run_id=sources.stored_run.record.run_id,
                source_run_hash=_source_hash(
                    sources.stored_run, sources.provenance_hash
                ),
                documents=documents,
                codebook=reference,
                configuration_hash=digest(configuration),
                extractor_family=extractor_family,
                scorer_identity=identity,
                judge_identities=identities,
                support_version=SUPPORT_VERSION,
                validator_version=VALIDATOR_VERSION,
                software=tuple(sorted(software.items())),
                ceilings=ceilings,
                counts_by_status=(),
                counts_by_reason=(),
                evaluations=0,
                requests=0,
                prompt_tokens=0,
                completion_tokens=0,
                reserved_tokens=0,
                unreported=0,
                cache_hits=0,
                billable_cost="none, self-hosted",
                artifact_hashes=(),
            ),
            SupportRunRecord,
        )
        for judge in judges:
            preflight = getattr(judge, "_preflight", None)
            if preflight is not None:
                preflight()
        allowance = Allowance(ceilings)
        assessments = []
        for target in targets:
            resolved = resolve_target(
                sources.stored_run,
                sources.bundles,
                sources.codebook,
                target,
                provenance_hash=sources.provenance_hash,
            )
            assessment = (
                _refused_result(resolved)
                if isinstance(resolved, RefusedTarget)
                else assess_target(
                    resolved,
                    scorer,
                    judges,
                    policy,
                    allowance,
                    cache=cache,
                    extractor_family=extractor_family,
                )
            )
            assessments.append(assessment)
        usage = tuple(u for a in assessments for u in a.usage)
        hashes = {
            f"raw/{attempt.raw_ref}": cache.artifact_hash(attempt.raw_ref)
            for a in assessments
            for attempt in a.attempts
            if attempt.raw_ref is not None
        }
        record = _validated(
            record.model_copy(
                update={
                    **accounting(assessments, usage),
                    "artifact_hashes": tuple(sorted(hashes.items())),
                }
            ),
            SupportRunRecord,
        )
        return SupportRunResult(record, tuple(assessments))
    except SupportError:
        raise
    except Exception as error:  # noqa: BLE001 - redact arbitrary adapter diagnostics
        raise unexpected_error(error) from None
