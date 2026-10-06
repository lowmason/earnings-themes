"""Complete frozen coding inputs resolved through Stage 8's public source gate."""

from dataclasses import dataclass

from earnings_core import digest

from earnings_themes.anchoring import Bundle
from earnings_themes.codebook import Codebook
from earnings_themes.coding.records import CODING_VERSION, REASONS, CodingError
from earnings_themes.extraction.store import StoredRun
from earnings_themes.support import resolve_target, reverify_input
from earnings_themes.support.records import (
    CodebookReference,
    RefusedTarget,
    ResolvedInput,
    SupportSources,
    Target,
)


@dataclass(frozen=True, repr=False)
class CodingInput:
    """Transient integrity probes for every approved theme, with safe diagnostics."""

    sources: SupportSources
    doc_id: str
    claim_id: str
    probes: tuple[ResolvedInput, ...]
    input_hash: str


def _check_sources(sources: SupportSources) -> None:
    if (
        type(sources) is not SupportSources
        or type(sources.stored_run) is not StoredRun
        or type(sources.bundles) is not tuple
        or type(sources.codebook) is not Codebook
        or type(sources.codebook.themes) is not tuple
        or any(
            type(getattr(sources.stored_run, name)) is not tuple
            for name in (
                "documents",
                "windows",
                "visits",
                "quotes",
                "claims",
                "rejections",
            )
        )
        or any(
            type(bundle) is not Bundle
            or type(bundle.elements) is not tuple
            or type(bundle.masks) is not tuple
            for bundle in sources.bundles
        )
    ):
        raise CodingError("malformed_record")


def _resolved(probe: ResolvedInput | RefusedTarget) -> ResolvedInput:
    if type(probe) is RefusedTarget:
        reasons = probe.outcome.flags + probe.outcome.missing
        reason = next(
            (reason for reason in reasons if type(reason) is str and reason in REASONS),
            "invalid_references",
        )
        raise CodingError(reason)
    if type(probe) is not ResolvedInput:
        raise CodingError("malformed_record")
    return probe


def resolve_coding_input(
    sources: SupportSources, doc_id: str, claim_id: str
) -> CodingInput:
    """Resolve the unchanged claim and all original links for every frozen theme."""
    try:
        _check_sources(sources)
        if type(doc_id) is not str or type(claim_id) is not str:
            raise CodingError("malformed_record")
        reference = CodebookReference(
            codebook_id=sources.codebook.codebook_id,
            codebook_version=sources.codebook.codebook_version,
            content_hash=sources.codebook.content_hash,
        )
        probes = []
        for theme in sorted(sources.codebook.themes, key=lambda theme: theme.theme_id):
            target = Target(
                source_run_id=sources.stored_run.record.run_id,
                doc_id=doc_id,
                claim_id=claim_id,
                theme_id=theme.theme_id,
                codebook=reference,
            )
            probe = resolve_target(
                sources.stored_run,
                sources.bundles,
                sources.codebook,
                target,
                provenance_hash=sources.provenance_hash,
            )
            probes.append(_resolved(probe))
        if not probes:
            raise CodingError("wrong_codebook")
        material = {
            "coding_version": CODING_VERSION,
            "doc_id": doc_id,
            "claim_id": claim_id,
            "inputs": [probe.record.input_hash for probe in probes],
        }
        return CodingInput(sources, doc_id, claim_id, tuple(probes), digest(material))
    except CodingError:
        raise
    except Exception:  # noqa: BLE001 - boundary failures must not print source data
        raise CodingError("malformed_record") from None


def reverify_coding_input(input: CodingInput) -> CodingInput:
    """Revalidate retained probes and compare against complete current resolution."""
    try:
        if (
            type(input) is not CodingInput
            or type(input.probes) is not tuple
            or type(input.input_hash) is not str
        ):
            raise CodingError("malformed_record")
        for probe in input.probes:
            if type(probe) is not ResolvedInput:
                raise CodingError("malformed_record")
            _resolved(reverify_input(probe))
        again = resolve_coding_input(input.sources, input.doc_id, input.claim_id)
        if (
            again.input_hash != input.input_hash
            or tuple(probe.record for probe in again.probes)
            != tuple(probe.record for probe in input.probes)
            or tuple(
                (probe.evidence, probe.contexts, probe.claim) for probe in again.probes
            )
            != tuple(
                (probe.evidence, probe.contexts, probe.claim) for probe in input.probes
            )
        ):
            raise CodingError("input_changed")
        return again
    except CodingError:
        raise
    except Exception:  # noqa: BLE001 - boundary failures must not print source data
        raise CodingError("malformed_record") from None
