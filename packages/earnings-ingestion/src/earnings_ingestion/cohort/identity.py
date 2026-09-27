"""The universe's operative identity (plan 7; EV4 of the Stage 5 spec).

A manifest's ``content_hash`` covers everything it holds: withheld evidence, the SEC
records its identities cite, and the source register's version. So curating a notice
published after the cutoff, re-fetching an SEC record, or editing a register entry
makes a new version whose facts are unchanged.

``operative_hash`` covers only the cutoff-admissible facts that an event's
eligibility can read, and Stage 5's records key on it:

- the definition's window, cutoff, membership reference, and selection policy;
- every interval, with both bounds, their timing and basis, and its assertions;
- the mapping of each security that has an interval: its status, issuer, and CIK;
- each issuer's CIK and securities, and the candidate issuers.

A security named only by evidence the cutoff withholds has no interval, so its
mapping decides no event and is left out (plan 7, P7-4).
"""

from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.records import UniverseManifest

DEFINITION = (
    "universe_id",
    "universe_name",
    "period_end_start",
    "period_end_stop",
    "public_information_cutoff",
    "membership_reference",
    "selection_policy_version",
)


def operative_projection(manifest: UniverseManifest) -> dict:
    """The facts ``operative_hash`` covers, as canonical-JSON-ready data."""
    definition = manifest.definition.model_dump(mode="json", include=set(DEFINITION))
    intervals = sorted(
        manifest.intervals, key=lambda i: (i.security_id, i.effective_from)
    )
    with_interval = {interval.security_id for interval in intervals}
    return {
        "definition": definition,
        "intervals": [interval.model_dump(mode="json") for interval in intervals],
        "mappings": [
            mapping.model_dump(
                mode="json", include={"security_id", "status", "issuer_id", "cik"}
            )
            for mapping in sorted(manifest.mappings, key=lambda m: m.security_id)
            if mapping.security_id in with_interval
        ],
        "issuers": [
            issuer.model_dump(mode="json", include={"issuer_id", "cik", "security_ids"})
            for issuer in sorted(manifest.issuers, key=lambda i: i.issuer_id)
        ],
        "candidate_issuer_ids": sorted(manifest.candidate_issuer_ids),
    }


def operative_hash(manifest: UniverseManifest) -> str:
    """SHA-256 of the canonical JSON of ``operative_projection(manifest)``."""
    return digest(operative_projection(manifest))
