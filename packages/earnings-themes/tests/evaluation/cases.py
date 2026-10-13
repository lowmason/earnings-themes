"""Invented readings over an invented four-paragraph document: no release text, and
no pilot text (GS13). Each paragraph is one pointer unit."""

from earnings_core import CanonicalDocument, DocumentElement, ElementType, TextSpan
from earnings_themes.anchoring import Bundle
from earnings_themes.annotation import Reading
from earnings_themes.gold import (
    Gold,
    GoldAssignment,
    GoldClaim,
    GoldQuote,
    HardNegative,
    NegativeKind,
    Origin,
    ReleaseIdentification,
    ReleaseLabel,
    Support,
)

LINES = (
    "Alpha built a plant.",
    "Beta cut prices.",
    "Gamma hired staff.",
    "Delta paid debt.",
)
"""Spans: [0, 20), [21, 37), [38, 56) and [57, 73)."""
HASH = "0" * 64


def bundle(name: str = "invented-evaluation", lines: tuple[str, ...] = LINES) -> Bundle:
    text = "\n".join(lines)
    document = CanonicalDocument.create(
        source_document_id=name,
        canonicalization_version="test-1",
        canonical_text=text,
    )
    elements, start = [], 0
    for line in lines:
        span = TextSpan(start=start, end=start + len(line))
        elements.append(DocumentElement.create(document, ElementType.PARAGRAPH, span))
        start = span.end + 1
    return Bundle(name, document, tuple(elements), ())


def unit_ids(source: Bundle) -> tuple[str, ...]:
    return tuple(e.element_id for e in source.elements)


def quote(quote_id: str, start: int, end: int, element_id: str) -> GoldQuote:
    return GoldQuote(
        quote_id=quote_id,
        start=start,
        end=end,
        element_id=element_id,
        quote_sha256=HASH,
        origin=Origin.DRAFTED_ACCEPTED,
    )


def claim(claim_id: str, *quote_ids: str) -> GoldClaim:
    return GoldClaim(
        claim_id=claim_id,
        quote_ids=quote_ids,
        claim="An invented claim.",
        origin=Origin.DRAFTED_ACCEPTED,
    )


def row(
    claim_id: str,
    theme_id: str,
    support: Support = Support.SUPPORTS,
    tie_group: str | None = None,
) -> GoldAssignment:
    return GoldAssignment(
        claim_id=claim_id,
        theme_id=theme_id,
        support=support,
        tie_group=tie_group,
        origin=Origin.DRAFTED_ACCEPTED,
    )


def negative(
    claim_id: str, quote_id: str, kind: NegativeKind, theme_id: str | None
) -> HardNegative:
    return HardNegative(
        claim_id=claim_id,
        quote_ids=(quote_id,),
        claim="An invented claim its quote does not support.",
        negative_kind=kind,
        theme_id=theme_id,
        origin=Origin.DRAFTED_ACCEPTED,
    )


def reading(
    quotes=(),
    claims=(),
    assignments=(),
    negatives=(),
    label: ReleaseLabel = ReleaseLabel.RELEASE,
) -> Reading:
    return Reading(
        no_theme=False,
        release_identification=ReleaseIdentification(label=label, note="Invented."),
        quotes=tuple(quotes),
        claims=tuple(claims),
        assignments=tuple(assignments),
        hard_negatives=tuple(negatives),
    )


def example() -> tuple[Bundle, Reading]:
    """The known-answer reading: ``q1`` is part of P0, ``q2`` crosses P1 and P2,
    ``q3`` is P3. ``c1`` supports capacity; ``c2`` is tie group ``g1`` over demand
    and pricing; ``c3`` is only uncertain for labor and costs; ``c4`` does not
    support debt, and costs is also decided by ``c1``'s ``does_not_support``."""
    source = bundle()
    p0, p1, _, p3 = unit_ids(source)
    return source, reading(
        quotes=(
            quote("q1", 0, 5, p0),
            quote("q2", 30, 45, p1),
            quote("q3", 57, 73, p3),
        ),
        claims=(
            claim("c1", "q1"),
            claim("c2", "q2"),
            claim("c3", "q3"),
            claim("c4", "q1"),
        ),
        assignments=(
            row("c1", "capacity"),
            row("c1", "costs", Support.DOES_NOT_SUPPORT),
            row("c2", "demand", tie_group="g1"),
            row("c2", "pricing", tie_group="g1"),
            row("c3", "labor", Support.UNCERTAIN),
            row("c3", "costs", Support.UNCERTAIN),
            row("c4", "debt", Support.DOES_NOT_SUPPORT),
            row("c4", "unmatched"),
        ),
        negatives=(
            negative("n1", "q3", NegativeKind.PERIOD, "capacity"),
            negative("n2", "q1", NegativeKind.ISSUER, "demand"),
            negative("n3", "q2", NegativeKind.SECTION, None),
        ),
    )


def gold(event_id: str, base: Reading, partition: str = "dev", **changes) -> Gold:
    """``base`` as signed gold for ``event_id``, with invented bindings."""
    from datetime import date

    from earnings_themes.gold import CodebookRef, DraftCounts
    from earnings_themes.split import Partition
    from earnings_themes.synthetic import PIN

    fields = {
        "event_id": event_id,
        "document_id": f"{event_id}-doc",
        "doc_id": f"{event_id}@test-1#0000000000000000",
        "canonical_hash": HASH,
        "pin": PIN,
        "split_hash": HASH,
        "partition": Partition(partition),
        "codebook": CodebookRef(
            codebook_id="invented", codebook_version=0, content_hash=HASH
        ),
        "annotator": "Invented Annotator",
        "drafting_aid": {"model_id": "invented-aid", "drafted_on": date(2026, 10, 1)},
        "counts": DraftCounts(accepted=1, edited=0, rejected=0, added=0),
        "no_theme": False,
        **base.model_dump(exclude={"no_theme"}),
        **changes,
    }
    return Gold.model_validate(fields)


def trial(
    target_id: str,
    family: str,
    presentation: str,
    claim_support: str,
    theme_fit: str,
    quotes: tuple[str, ...] = (),
):
    """One available judge trial with invented identity and answer; each of
    ``quotes`` is assessed ``supporting``."""
    from earnings_themes.support.records import (
        JudgeAnswer,
        JudgeIdentity,
        JudgeTrial,
        Presentation,
        QuoteAssessment,
        RuntimeIdentity,
        SignalStatus,
    )

    return JudgeTrial(
        trial_id=f"{target_id}-{family}-{presentation}",
        target_id=target_id,
        identity=JudgeIdentity(
            family=family,
            runtime=RuntimeIdentity(
                model_id=f"{family}-model",
                revision="1",
                files=(),
                runtime="scripted",
                runtime_version="1",
                device="cpu",
                precision="float32",
                encoding_version="1",
            ),
            input_limit=1000,
            output_limit=100,
            hosting="scripted",
            weight_license=None,
        ),
        presentation=Presentation(presentation),
        attempt_ids=(f"{target_id}-{family}-{presentation}-1",),
        status=SignalStatus.AVAILABLE,
        answer=JudgeAnswer(
            claim_support=claim_support,
            theme_fit=theme_fit,
            joint_support_score=0.5,
            quote_assessments=tuple(
                QuoteAssessment(quote_id=q, contribution="supporting") for q in quotes
            ),
            reason_codes=(),
            summary="Invented summary.",
        ),
        reason=None,
    )


def panel(
    target_id: str,
    first: tuple[str, str],
    second: tuple[str, str],
    quotes: tuple[str, ...] = (),
):
    """Four trials: family ``f0`` answers ``first`` and ``f1`` answers ``second``,
    each under both presentations."""
    return tuple(
        trial(target_id, family, presentation, *answers, quotes)
        for family, answers in (("f0", first), ("f1", second))
        for presentation in ("evidence_first", "claim_theme_first")
    )


def decision_view(
    target_id: str, score: float, first: tuple[str, str], second: tuple[str, str]
):
    """An invented one-quote target's decision view, its outcome derived by Stage 8's
    ``derive_outcome`` and its eligible quotes by Stage 9's, never fabricated."""
    from earnings_core import digest
    from earnings_themes.coding.decide import DecisionInput, eligible_quote_ids
    from earnings_themes.support import derive_outcome
    from earnings_themes.support.records import (
        CodebookReference,
        EntailmentSignal,
        EvidenceReference,
        RuntimeIdentity,
        ScorerIdentity,
        SignalStatus,
        Target,
        TargetRecord,
    )

    quote_id = "q1"
    record = TargetRecord(
        target_id=target_id,
        target=Target(
            source_run_id="invented-run",
            doc_id="invented-doc",
            claim_id=f"{target_id}-claim",
            theme_id="capacity",
            codebook=CodebookReference(
                codebook_id="invented", codebook_version=0, content_hash=HASH
            ),
        ),
        source_run_hash=HASH,
        claim_hash=HASH,
        input_hash=digest(target_id),
        original_quote_ids=(quote_id,),
        evidence_ids=(f"{target_id}-{quote_id}",),
        theme=None,
    )
    evidence = (
        EvidenceReference(
            target_id=target_id,
            quote_id=quote_id,
            doc_id="invented-doc",
            canonical_hash=HASH,
            element_id="paragraph-0-20",
            start=0,
            end=20,
            text_hash=HASH,
            validator_version="3",
            mask_ids=(),
        ),
    )
    scorer = ScorerIdentity(
        kind="scripted",
        input_limit=1000,
        runtime=RuntimeIdentity(
            model_id="invented-scorer",
            revision="1",
            files=(),
            runtime="scripted",
            runtime_version="1",
            device="cpu",
            precision="float32",
            encoding_version="1",
        ),
    )
    entailment = tuple(
        EntailmentSignal(
            signal_id=f"{target_id}-{scope}",
            target_id=target_id,
            scope=scope,
            quote_id=quote,
            evaluation_id=f"{target_id}-{scope}",
            identity=scorer,
            input_hash=HASH,
            status=SignalStatus.AVAILABLE,
            score=score,
            reason=None,
            input_tokens=1,
            latency_ms=0,
            cached=False,
        )
        for scope, quote in (("quote", quote_id), ("joint", None))
    )
    trials = panel(target_id, first, second, (quote_id,))
    outcome = derive_outcome(target_id, entailment, trials, (quote_id,))
    eligible = (
        eligible_quote_ids(evidence, trials) if outcome.status == "assessed" else ()
    )
    return DecisionInput(record, evidence, entailment, trials, outcome, eligible)
