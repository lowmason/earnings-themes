"""The membership source register: A §242's fields for index-membership sources.

It is a second register beside docs/source-register.toml, which holds the release
sources and the ``sec-edgar`` entry that the shared SEC client implements. It quotes
no source. A published source's terms are tracked by ``terms_url`` and
``terms_sha256``, the hash of their canonical text when a person last read them: a
different hash asks for a new reading, never an automatic decision. A list the user
supplied has no terms page.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal, Self

import tomllib
from earnings_core import RightsStatus, digest
from earnings_core.artifacts import NonBlankStr
from earnings_core.hashing import Sha256Hex
from pydantic import BaseModel, ConfigDict, model_validator

from earnings_ingestion.cohort.records import EvidenceClass, SourceRights, SourceRole
from earnings_ingestion.fetch.records import SourceId

MEMBERSHIP_REGISTER = Path("docs") / "membership-source-register.toml"
SEC_REGISTER = Path("docs") / "source-register.toml"
SEC_SOURCE_ID = "sec-edgar"
SEC_RIGHTS = SourceRights(
    source_id=SEC_SOURCE_ID,
    evidence_class=None,
    rights_status=RightsStatus.LOCAL_ONLY,
    rights_basis=(
        "docs/source-register.toml entry sec-edgar;"
        " SEC records are kept local under data/raw/"
    ),
)


class RegisterEntry(BaseModel):
    """One membership source; shared field names follow docs/source-register.toml."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    owner: NonBlankStr
    url: NonBlankStr
    access_method: NonBlankStr
    cost: NonBlankStr
    license_terms: NonBlankStr
    terms_url: NonBlankStr | None = None
    terms_sha256: Sha256Hex | None = None
    redistribution_status: NonBlankStr
    coverage: NonBlankStr
    expected_update_pattern: NonBlankStr
    known_limitations: tuple[NonBlankStr, ...]
    last_verified: date
    evidence_class: EvidenceClass
    roles: tuple[SourceRole, ...]
    rights_status: RightsStatus
    rights_basis: NonBlankStr

    @model_validator(mode="after")
    def _terms(self) -> Self:
        user = self.evidence_class is EvidenceClass.USER_SUPPLIED
        if not user and (self.terms_url is None or self.terms_sha256 is None):
            raise ValueError("a published source records its terms' URL and hash")
        return self


class MembershipRegister(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    sources: dict[SourceId, RegisterEntry]


@dataclass(frozen=True)
class Registers:
    """The membership register and the ``sec-edgar`` entry of the release register."""

    membership: MembershipRegister
    sec_entry: dict[str, Any]

    def entry(self, source_id: str) -> RegisterEntry:
        try:
            return self.membership.sources[source_id]
        except KeyError:
            raise ValueError(
                f"source {source_id!r} is not in the membership source register"
            ) from None

    def rights(self, source_id: str) -> SourceRights:
        if source_id == SEC_SOURCE_ID:
            return SEC_RIGHTS
        entry = self.entry(source_id)
        return SourceRights(
            source_id=source_id,
            evidence_class=entry.evidence_class,
            rights_status=entry.rights_status,
            rights_basis=entry.rights_basis,
        )

    def version(self, source_ids: Iterable[str]) -> str:
        """SHA-256 of the canonical JSON of every register entry a manifest cites,
        ``sec-edgar`` always among them."""
        cited = {
            source_id: self.entry(source_id).model_dump(mode="json")
            for source_id in set(source_ids) - {SEC_SOURCE_ID}
        }
        return digest(cited | {SEC_SOURCE_ID: self.sec_entry})


def load_registers(
    repo: Path,
    membership: Path = MEMBERSHIP_REGISTER,
    sec: Path = SEC_REGISTER,
) -> Registers:
    """Both registers, from paths relative to ``repo``."""
    text = (repo / membership).read_text(encoding="utf-8")
    register = MembershipRegister.model_validate(tomllib.loads(text))
    sources = tomllib.loads((repo / sec).read_text(encoding="utf-8"))["sources"]
    if SEC_SOURCE_ID not in sources:
        raise ValueError(f"{sec} has no {SEC_SOURCE_ID} entry")
    return Registers(membership=register, sec_entry=sources[SEC_SOURCE_ID])
