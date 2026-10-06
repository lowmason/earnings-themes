"""Caller-ordered proposal runs, never automatic support or acceptance."""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from earnings_core import VALIDATOR_VERSION, digest

from earnings_themes.codebook import Codebook
from earnings_themes.coding.adapters import Classifier
from earnings_themes.coding.cache import CodingCache
from earnings_themes.coding.classify import (
    CodingAllowance,
    _classifier_identity,
    _current_identity,
    _policy,
    _verify_attempts,
    classification_id,
    classify_claim,
)
from earnings_themes.coding.input import (
    CodingInput,
    resolve_coding_input,
    reverify_coding_input,
)
from earnings_themes.coding.records import (
    CODING_VERSION,
    AttributeRecord,
    ClassificationRecord,
    CodingAttempt,
    CodingCeilings,
    CodingError,
    CodingPolicy,
    CodingPolicySnapshot,
    CodingReply,
    NoveltyItem,
    ProposalRecord,
    ProposalRunRecord,
    checked,
)
from earnings_themes.extraction.records import RunRecord
from earnings_themes.extraction.store import StoredRun
from earnings_themes.support.records import CodebookReference, SupportSources, Target


@dataclass(frozen=True, repr=False)
class ProposalRun:
    record: ProposalRunRecord
    classifications: tuple[ClassificationRecord, ...]
    attempts: tuple[CodingAttempt, ...]
    proposals: tuple[ProposalRecord, ...]
    attributes: tuple[AttributeRecord, ...]
    novelty: tuple[NoveltyItem, ...]

    @property
    def targets(self) -> tuple[Target, ...]:
        return tuple(proposal.target for proposal in self.proposals)


def _source_bindings(sources: SupportSources) -> dict:
    if (
        type(sources) is not SupportSources
        or type(sources.stored_run) is not StoredRun
        or type(sources.codebook) is not Codebook
    ):
        raise CodingError("malformed_record")
    source = checked(sources.stored_run.record, RunRecord)
    # Evidence/structure failures belong to each requested source refusal;
    # manifest metadata must still be strictly representable before dispatch.
    book = sources.codebook
    return {
        "source_run_id": source.run_id,
        "source_run_hash": digest(
            {
                "record": source.model_dump(mode="json"),
                "provenance_hash": sources.provenance_hash,
            }
        ),
        "documents": tuple(sorted(source.documents.items())),
        "codebook": CodebookReference(
            codebook_id=book.codebook_id,
            codebook_version=book.codebook_version,
            content_hash=book.content_hash,
        ),
    }


def refused_input_hash(
    source_hash: str, doc_id: str, claim_id: str, codebook: CodebookReference
) -> str:
    """Unresolved provenance fingerprint, never a successfully resolved input."""
    return digest(
        {
            "kind": "refused-coding-input/1",
            "coding_version": CODING_VERSION,
            "source_run_hash": source_hash,
            "doc_id": doc_id,
            "claim_id": claim_id,
            "codebook": codebook.model_dump(mode="json"),
        }
    )


def _refused(
    run_id: str, doc_id: str, claim_id: str, bindings: dict, reason: str
) -> ClassificationRecord:
    fingerprint = refused_input_hash(
        bindings["source_run_hash"], doc_id, claim_id, bindings["codebook"]
    )
    return ClassificationRecord(
        classification_id=classification_id(run_id, doc_id, claim_id, fingerprint),
        coding_run_id=run_id,
        doc_id=doc_id,
        claim_id=claim_id,
        input_hash=fingerprint,
        codebook=bindings["codebook"],
        status="refused",
        reason=reason,
        attempt_ids=(),
        theme_ids=(),
    )


def propose_run(
    run_id: str,
    sources: SupportSources,
    claim_order: Sequence[tuple[str, str]],
    classifier: Classifier,
    policy: CodingPolicy,
    ceilings: CodingCeilings,
    *,
    cache: CodingCache,
    started_at: datetime,
    software: Mapping[str, str],
) -> ProposalRun:
    """Preflight all claims, then dispatch sequentially under a shared allowance."""
    try:
        if type(cache) is not CodingCache or not isinstance(software, Mapping):
            raise CodingError("malformed_record")
        if any(type(k) is not str or type(v) is not str for k, v in software.items()):
            raise CodingError("malformed_record")
        if isinstance(claim_order, str | bytes) or not isinstance(
            claim_order, Sequence
        ):
            raise CodingError("malformed_record")
        order = tuple(claim_order)
        if any(type(pair) is not tuple or len(pair) != 2 for pair in order):
            raise CodingError("malformed_record")
        policy_value = _policy(policy)
        policy_hash = digest(policy_value.model_dump(mode="json"))
        snapshot = CodingPolicySnapshot(
            **policy_value.model_dump(exclude={"prompt_text"})
        )
        identity = _classifier_identity(classifier)
        ceiling_value = checked(ceilings, CodingCeilings)
        bindings = _source_bindings(sources)
        schema_hash = digest(CodingReply.model_json_schema())
        configuration = {
            **{
                k: v.model_dump(mode="json") if hasattr(v, "model_dump") else v
                for k, v in bindings.items()
            },
            "classifier_identity": identity.model_dump(mode="json"),
            "coding_policy": snapshot.model_dump(mode="json"),
            "ceilings": ceiling_value.model_dump(mode="json"),
            "requested_claim_order": order,
            "schema_hash": schema_hash,
            "coding_version": CODING_VERSION,
            "validator_version": VALIDATOR_VERSION,
            "cache_mode": cache.mode,
        }
        record = checked(
            ProposalRunRecord.model_construct(
                run_id=run_id,
                started_at=started_at,
                **bindings,
                classifier_identity=identity,
                coding_policy=snapshot,
                ceilings=ceiling_value,
                cache_mode=cache.mode,
                configuration_hash=digest(configuration),
                requested_claim_order=order,
                schema_hash=schema_hash,
                validator_version=VALIDATOR_VERSION,
                software=tuple(sorted(software.items())),
                counts_by_status=(),
                counts_by_reason=(),
                requests=0,
                prompt_tokens=0,
                completion_tokens=0,
                reserved_tokens=0,
                charged_tokens=0,
                unreported=0,
                cache_hits=0,
                latency_ms=0,
                billable_cost="none, self-hosted",
                artifact_hashes=(),
            ),
            ProposalRunRecord,
        )
        resolved: list[CodingInput | ClassificationRecord] = []
        for doc_id, claim_id in record.requested_claim_order:
            try:
                resolved.append(resolve_coding_input(sources, doc_id, claim_id))
            except CodingError as error:
                resolved.append(
                    _refused(run_id, doc_id, claim_id, bindings, str(error))
                )
        allowance = CodingAllowance(ceiling_value, run_id=run_id)
        classifications = []
        attempts = []
        proposals = []
        attributes = []
        novelty = []
        for input in resolved:
            if type(input) is ClassificationRecord:
                classifications.append(input)
                continue
            result = classify_claim(input, classifier, policy, allowance, cache=cache)
            classifications.append(result.record)
            attempts.extend(result.attempts)
            proposals.extend(result.proposals)
            if result.attribute is not None:
                attributes.append(result.attribute)
            if result.novelty is not None:
                novelty.append(result.novelty)
        fresh = [attempt for attempt in attempts if attempt.reserved_tokens > 0]
        statuses = Counter(row.status for row in classifications)
        reasons = Counter(
            row.reason for row in classifications if row.reason is not None
        )
        # Callback activity must finish before the final source/policy/raw audit.
        if _classifier_identity(classifier) != identity:
            raise CodingError("model_mismatch")
        hashes = {
            f"raw/{attempt.raw_ref}": cache.artifact_hash(attempt.raw_ref)
            for attempt in attempts
            if attempt.raw_ref is not None
        }
        record = checked(
            record.model_copy(
                update={
                    "counts_by_status": tuple(sorted(statuses.items())),
                    "counts_by_reason": tuple(sorted(reasons.items())),
                    "requests": allowance.requests,
                    "prompt_tokens": sum(
                        row.actual_prompt_tokens or 0 for row in fresh
                    ),
                    "completion_tokens": sum(
                        row.actual_completion_tokens or 0 for row in fresh
                    ),
                    "reserved_tokens": sum(row.reserved_tokens for row in fresh),
                    "charged_tokens": allowance.tokens,
                    "unreported": allowance.unreported,
                    "cache_hits": sum(row.cached for row in attempts),
                    "latency_ms": sum(row.latency_ms for row in fresh),
                    "artifact_hashes": tuple(sorted(hashes.items())),
                }
            ),
            ProposalRunRecord,
        )
        for input in resolved:
            if type(input) is CodingInput:
                identifier = classification_id(
                    run_id, input.doc_id, input.claim_id, input.input_hash
                )
                _verify_attempts(
                    input,
                    policy,
                    identity,
                    tuple(
                        row for row in attempts if row.classification_id == identifier
                    ),
                    cache,
                )
        # Audit callbacks and identity properties precede the final pure bindings.
        if _current_identity(classifier) != identity:
            raise CodingError("model_mismatch")
        if (
            _source_bindings(sources) != bindings
            or digest(_policy(policy).model_dump(mode="json")) != policy_hash
            or checked(ceilings, CodingCeilings) != ceiling_value
            or tuple(sorted(software.items())) != record.software
            or tuple(claim_order) != order
            or cache.mode != configuration["cache_mode"]
            or digest(CodingReply.model_json_schema()) != schema_hash
        ):
            raise CodingError("input_changed")
        for input in resolved:
            if type(input) is CodingInput:
                try:
                    reverify_coding_input(input)
                except CodingError:
                    raise CodingError("input_changed") from None
            else:
                try:
                    resolve_coding_input(sources, input.doc_id, input.claim_id)
                except CodingError as error:
                    if str(error) != input.reason:
                        raise CodingError("input_changed") from None
                else:
                    raise CodingError("input_changed")
        return ProposalRun(
            record,
            tuple(classifications),
            tuple(attempts),
            tuple(proposals),
            tuple(attributes),
            tuple(novelty),
        )
    except CodingError:
        raise
    except Exception:  # noqa: BLE001 - metadata and callback errors never expose text
        raise CodingError("unexpected_error") from None
