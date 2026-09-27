"""Security-to-issuer resolution to a zero-padded CIK (P §Issuer resolution).

A cited ticker only proposes candidates: SEC's ticker list maps it to a CIK. The
candidate is confirmed when SEC's own record for that CIK lists the same ticker and
a name, current or former, that covers the name cited beside the ticker (plan 6,
P6-8). One confirmed CIK resolves the security. None, or several, leave it
``unresolved`` or ``conflicting``; an in-scope security in that state holds the
freeze until a reviewer's ``set_issuer`` or ``retain_unresolved`` override decides
it. Nothing is guessed, and no ticker alone establishes identity (A §268).
"""

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from earnings_ingestion.cohort.findings import make_finding
from earnings_ingestion.cohort.locators import CitableArtifact
from earnings_ingestion.cohort.names import covered
from earnings_ingestion.cohort.records import (
    Finding,
    FindingKind,
    Issuer,
    IssuerCandidate,
    IssuerMapping,
    Override,
    OverrideKind,
    ResolutionMethod,
    ResolutionStatus,
    SecurityRecord,
)
from earnings_ingestion.sec.data import Registrant, TickerEntry


def issuer_id_for(cik: str) -> str:
    return f"cik-{cik}"


@dataclass(frozen=True)
class SecEvidence:
    """SEC's ticker list and the submissions of every CIK it proposed or a
    reviewer named, each with what is needed to cite it."""

    tickers: CitableArtifact
    ticker_entries: tuple[TickerEntry, ...]
    registrants: Mapping[str, tuple[Registrant, CitableArtifact]]

    def registrant(self, cik: str) -> tuple[Registrant, CitableArtifact]:
        try:
            return self.registrants[cik]
        except KeyError:
            raise ValueError(
                f"no saved submissions for CIK {cik}; run the SEC fetch first"
            ) from None


@dataclass(frozen=True)
class Resolution:
    mappings: tuple[IssuerMapping, ...]
    issuers: tuple[Issuer, ...]
    findings: tuple[Finding, ...]


def _candidates(security: SecurityRecord, sec: SecEvidence) -> list[IssuerCandidate]:
    by_ticker: dict[str, list[TickerEntry]] = defaultdict(list)
    for entry in sec.ticker_entries:
        by_ticker[entry.ticker].append(entry)
    candidates = []
    for identity in security.identities:
        for entry in by_ticker.get(identity.ticker, []):
            registrant, submissions = sec.registrant(entry.cik)
            names = [(registrant.name, "/name")] + [
                (former.name, former.pointer) for former in registrant.former_names
            ]
            matched = next(
                (
                    (name, pointer)
                    for name, pointer in names
                    if covered(identity.name, name)
                ),
                None,
            )
            pointers = ["/name", "/tickers"]
            if matched is not None and matched[1] != "/name":
                pointers.append(matched[1])
            listed = identity.ticker in registrant.tickers
            candidates.append(
                IssuerCandidate(
                    evidence_id=identity.evidence_id,
                    cited_name=identity.name,
                    ticker=identity.ticker,
                    cik=entry.cik,
                    sec_name=registrant.name,
                    ticker_listed=listed,
                    matched_name=None if matched is None else matched[0],
                    confirmed=listed and matched is not None,
                    citations=(
                        sec.tickers.cite(sec.tickers.text.pointer(entry.pointer)),
                        submissions.cite(
                            *(submissions.text.pointer(p) for p in pointers)
                        ),
                    ),
                )
            )
    return candidates


def resolve(
    securities: Iterable[SecurityRecord],
    sec: SecEvidence,
    overrides: Iterable[Override],
    in_scope: frozenset[str],
) -> Resolution:
    """A mapping for every security; a blocking finding for each in-scope security
    that SEC's evidence does not resolve, settled when an override decides it."""
    decided: dict[str, Override] = {}
    for override in overrides:
        if override.kind in (OverrideKind.SET_ISSUER, OverrideKind.RETAIN_UNRESOLVED):
            if override.security_id in decided:
                raise ValueError(f"{override.security_id} has two identity overrides")
            decided[override.security_id] = override
    securities = tuple(securities)
    unknown = set(decided) - {security.security_id for security in securities}
    if unknown:
        raise ValueError(f"identity overrides name no security: {sorted(unknown)}")

    mappings, findings = [], []
    for security in sorted(securities, key=lambda s: s.security_id):
        candidates = tuple(_candidates(security, sec))
        confirmed = sorted({c.cik for c in candidates if c.confirmed})
        if not security.identities:
            status = ResolutionStatus.UNRESOLVED
            reason = "no name or ticker was published for it by the cutoff"
        elif len(confirmed) == 1:
            status, reason = ResolutionStatus.RESOLVED, None
        elif confirmed:
            status = ResolutionStatus.CONFLICTING
            reason = f"SEC confirms several CIKs: {', '.join(confirmed)}"
        elif candidates:
            status = ResolutionStatus.UNRESOLVED
            reason = "no candidate lists the cited ticker under a covering name"
        else:
            status = ResolutionStatus.UNRESOLVED
            tickers = sorted({i.ticker for i in security.identities})
            reason = f"SEC's ticker list has none of {', '.join(tickers)}"
        override = decided.get(security.security_id)
        if status is not ResolutionStatus.RESOLVED and security.security_id in in_scope:
            findings.append(
                make_finding(
                    FindingKind.IDENTITY,
                    security.security_id,
                    f"{security.security_id}: {status}: {reason}",
                    blocking=True,
                    security_id=security.security_id,
                    evidence_ids=[i.evidence_id for i in security.identities],
                    resolved_by=() if override is None else (override.override_id,),
                )
            )
        mappings.append(
            _mapping(security, candidates, confirmed, status, reason, override)
        )

    issuers = _issuers(mappings, sec)
    return Resolution(tuple(mappings), issuers, tuple(findings))


def _mapping(
    security, candidates, confirmed, status, reason, override
) -> IssuerMapping:
    common = {"security_id": security.security_id, "candidates": candidates}
    if override is not None and override.kind is OverrideKind.SET_ISSUER:
        return IssuerMapping(
            **common,
            status=ResolutionStatus.RESOLVED,
            method=ResolutionMethod.OVERRIDE,
            issuer_id=issuer_id_for(override.cik),
            cik=override.cik,
            override_id=override.override_id,
            reason=override.rationale,
        )
    if override is not None:
        return IssuerMapping(
            **common,
            status=ResolutionStatus.RETAINED_UNRESOLVED,
            method=None,
            issuer_id=None,
            cik=None,
            override_id=override.override_id,
            reason=override.rationale,
        )
    resolved = status is ResolutionStatus.RESOLVED
    return IssuerMapping(
        **common,
        status=status,
        method=ResolutionMethod.SEC_TICKER_AND_NAME if resolved else None,
        issuer_id=issuer_id_for(confirmed[0]) if resolved else None,
        cik=confirmed[0] if resolved else None,
        override_id=None,
        reason=reason,
    )


def _issuers(mappings: list[IssuerMapping], sec: SecEvidence) -> tuple[Issuer, ...]:
    securities: dict[str, list[str]] = defaultdict(list)
    for mapping in mappings:
        if mapping.cik is not None:
            securities[mapping.cik].append(mapping.security_id)
    issuers = []
    for cik in sorted(securities):
        registrant, _ = sec.registrant(cik)
        issuers.append(
            Issuer(
                issuer_id=issuer_id_for(cik),
                cik=cik,
                sec_name=registrant.name,
                former_names=tuple(former.name for former in registrant.former_names),
                security_ids=tuple(sorted(securities[cik])),
            )
        )
    return tuple(issuers)
