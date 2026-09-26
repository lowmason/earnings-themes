"""Findings of the coverage and conflict report, and reviewed acknowledgements.

A finding's ``digest`` hashes what it says. An ``acknowledge`` override names a
finding and that digest, so it accepts exactly the finding a reviewer read: when the
evidence changes what a finding says, the acknowledgement no longer applies and the
finding holds the freeze again.
"""

from collections.abc import Iterable

from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.records import (
    Finding,
    FindingKind,
    Override,
    OverrideKind,
)

ACKNOWLEDGEABLE = frozenset({FindingKind.MEMBER_COUNT, FindingKind.DIFFERENCE})


def make_finding(
    kind: FindingKind,
    subject: str,
    detail: str,
    *,
    blocking: bool,
    security_id: str | None = None,
    evidence_ids: Iterable[str] = (),
    resolved_by: Iterable[str] = (),
) -> Finding:
    """A finding with id ``<kind>:<subject>`` and the digest of its content."""
    evidence = tuple(sorted(set(evidence_ids)))
    content = {
        "kind": kind.value,
        "subject": subject,
        "detail": detail,
        "blocking": blocking,
        "security_id": security_id,
        "evidence_ids": evidence,
    }
    return Finding(
        finding_id=f"{kind.value}:{subject}",
        kind=kind,
        blocking=blocking,
        security_id=security_id,
        detail=detail,
        evidence_ids=evidence,
        digest=digest(content),
        resolved_by=tuple(sorted(set(resolved_by))),
    )


def acknowledge(
    findings: Iterable[Finding], overrides: Iterable[Override]
) -> tuple[tuple[Finding, ...], tuple[str, ...]]:
    """The findings with current acknowledgements applied, and the ids of the
    acknowledgements that no longer match any finding's digest."""
    findings = tuple(findings)
    by_id = {finding.finding_id: finding for finding in findings}
    accepted: dict[str, list[str]] = {}
    stale: list[str] = []
    for override in overrides:
        if override.kind is not OverrideKind.ACKNOWLEDGE:
            continue
        finding = by_id.get(override.finding_id)
        if finding is not None and finding.kind not in ACKNOWLEDGEABLE:
            raise ValueError(
                f"{override.override_id}: a {finding.kind} finding is resolved by"
                " evidence or its own override kind, never acknowledged"
            )
        if finding is None or finding.digest != override.finding_digest:
            stale.append(override.override_id)
            continue
        accepted.setdefault(finding.finding_id, []).append(override.override_id)
    resolved = tuple(
        finding.model_copy(
            update={
                "resolved_by": tuple(
                    sorted({*finding.resolved_by, *accepted[finding.finding_id]})
                )
            }
        )
        if finding.finding_id in accepted
        else finding
        for finding in findings
    )
    return resolved, tuple(sorted(stale))
