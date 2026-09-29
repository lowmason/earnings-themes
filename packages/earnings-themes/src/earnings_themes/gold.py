"""The gold contract (the Stage 6 spec, §The gold and §Curated hard negatives; R9.9,
R12.5, R12.6, R13.1; GS3, GS4, GS5, GS10).

- **One file per annotated bundle,** ``gold/<event>.toml``: the document, the
  pin, the split and partition, the codebook version, the signature, the drafting
  aid, the origin counts, ``no_theme``, and the release-identification label.
- **Quotes** are pointers, never text (GS3). **Claims** are the user's words.
  **Assignments** are one row per claim and theme, or ``unmatched``, each with its
  support; rows sharing a ``tie_group`` are alternatives for one claim (R12.6).
  **Hard-negative claims** are expected ``does_not_support`` (D4).
- **Origins.** Each item is ``drafted_accepted``, ``drafted_edited``, or
  ``annotator_added``, derived from the kept draft (GS5).
- **No theme.** ``no_theme`` is true exactly when no assignment pairs a claim with a
  codebook theme under ``supports`` (R12.4; plan 9, the user's answer).
- **Curated hard negatives** point into Stage 1's canonical fixtures and belong to
  no partition (GS10).
"""

from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Self

from pydantic import Field, NonNegativeInt, StringConstraints, model_validator

from earnings_themes import tomlfile
from earnings_themes.anchoring import SpanPointer
from earnings_themes.codebook import UNMATCHED, DraftingAid, ThemeId
from earnings_themes.records import (
    IdPart,
    NonBlank,
    Part,
    Pin,
    Sha256Hex,
    ThemesRecord,
    parse,
)
from earnings_themes.split import Partition

Accession = Annotated[str, StringConstraints(pattern=r"^[0-9]{10}-[0-9]{2}-[0-9]{6}$")]
Some = Field(min_length=1)


class Origin(StrEnum):
    """Where a gold item came from, against the kept draft (GS5)."""

    DRAFTED_ACCEPTED = "drafted_accepted"
    DRAFTED_EDITED = "drafted_edited"
    ANNOTATOR_ADDED = "annotator_added"


class Support(StrEnum):
    """Whether a claim's quotes support it under a theme (R8.1)."""

    SUPPORTS = "supports"
    DOES_NOT_SUPPORT = "does_not_support"
    UNCERTAIN = "uncertain"


class ReleaseLabel(StrEnum):
    """R13.1's release-identification label."""

    RELEASE = "release"
    NOT_RELEASE = "not_release"
    AMBIGUOUS = "ambiguous"


class NegativeKind(StrEnum):
    """What makes a hard negative confusable (R12.5)."""

    PERIOD = "period"
    ISSUER = "issuer"
    SECTION = "section"


class GoldQuote(SpanPointer):
    """One quote: a pointer into the bundle's canonical text."""

    quote_id: IdPart
    origin: Origin


class GoldClaim(Part):
    """One claim, in the user's words, resting on quotes."""

    claim_id: IdPart
    quote_ids: Annotated[tuple[IdPart, ...], Some]
    claim: NonBlank
    origin: Origin


class GoldAssignment(Part):
    """One claim and one theme, or ``unmatched`` (R9.9)."""

    claim_id: IdPart
    theme_id: ThemeId
    support: Support
    tie_group: IdPart | None = None
    origin: Origin


class HardNegative(Part):
    """A claim its quotes do not support: from a confusable period, issuer, or
    section (R12.5, D4)."""

    claim_id: IdPart
    quote_ids: Annotated[tuple[IdPart, ...], Some]
    claim: NonBlank
    negative_kind: NegativeKind
    theme_id: ThemeId | None = None
    origin: Origin


class ReleaseIdentification(Part):
    """Whether the document is this event's earnings release, for its issuer and
    period; with ``not_release``, the true release may be given, as facts."""

    label: ReleaseLabel
    note: NonBlank
    true_accession: Accession | None = None
    true_exhibit: NonBlank | None = None

    @model_validator(mode="after")
    def _facts_only_for_not_release(self) -> Self:
        named = self.true_accession is not None or self.true_exhibit is not None
        if named and self.label is not ReleaseLabel.NOT_RELEASE:
            raise ValueError("only not_release names the true release")
        return self


class DraftCounts(Part):
    """The drafted items accepted, edited, and rejected, and the items added."""

    accepted: NonNegativeInt
    edited: NonNegativeInt
    rejected: NonNegativeInt
    added: NonNegativeInt


class CodebookRef(Part):
    """The codebook version an annotation codes against."""

    codebook_id: IdPart
    codebook_version: NonNegativeInt
    content_hash: Sha256Hex


class Gold(ThemesRecord):
    """``gold/<event>.toml``: one bundle's signed gold; ``<event>`` is the event
    ID with its colon as an underscore."""

    event_id: IdPart
    document_id: IdPart
    doc_id: NonBlank
    canonical_hash: Sha256Hex
    pin: Pin
    split_hash: Sha256Hex
    partition: Partition
    codebook: CodebookRef
    annotator: str
    drafting_aid: DraftingAid
    counts: DraftCounts
    no_theme: bool
    release_identification: ReleaseIdentification
    quotes: tuple[GoldQuote, ...] = ()
    claims: tuple[GoldClaim, ...] = ()
    assignments: tuple[GoldAssignment, ...] = ()
    hard_negatives: tuple[HardNegative, ...] = ()


class FixtureNegatives(Part):
    """The curated hard negatives over one Stage 1 fixture."""

    fixture_id: IdPart
    doc_id: NonBlank
    canonical_hash: Sha256Hex
    quotes: Annotated[tuple[GoldQuote, ...], Some]
    hard_negatives: Annotated[tuple[HardNegative, ...], Some]


class HardNegativeSet(ThemesRecord):
    """``tests/fixtures/gold/hard-negatives.toml``: outside the pilot and in no
    partition (D4, GS10), though it carries the pin, as every Stage 6 record does."""

    pin: Pin
    annotator: str
    drafting_aid: DraftingAid
    counts: DraftCounts
    codebook: CodebookRef
    documents: Annotated[tuple[FixtureNegatives, ...], Some]


def no_theme_of(assignments: Iterable[GoldAssignment]) -> bool:
    """True exactly when no row pairs a claim with a theme under ``supports``."""
    return not any(
        a.theme_id != UNMATCHED and a.support is Support.SUPPORTS for a in assignments
    )


HEADER = (
    "Stage 6 gold (the pilot codebook, split, and gold-set protocol). Written by"
    " `earnings-pipeline gold anchor`; quotes are pointers, and every other word is"
    " the annotator's."
)


def gold_toml(record: Gold | HardNegativeSet) -> str:
    """The committed file: pointers, hashes, and the user's words, never a quote."""
    return tomlfile.dumps(record.model_dump(mode="python"), header=HEADER)


def load_gold(path: Path) -> Gold:
    """One bundle's gold file, read through its contract."""
    return parse(tomlfile.read(path), Gold, path.name)


def load_hard_negatives(path: Path) -> HardNegativeSet:
    """The curated hard negatives, read through their contract."""
    return parse(tomlfile.read(path), HardNegativeSet, path.name)
