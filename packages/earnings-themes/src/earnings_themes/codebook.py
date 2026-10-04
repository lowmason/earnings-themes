"""The codebook contract, and the freeze that approves a version (the Stage 6 spec,
§The codebook; A §608-611; R9.2, R9.3, R9.7; GS9, GS16).

- **Fields.** A version records its ID, version, status, content hash, discovery
  corpus, multi-label and boilerplate rules, approval, and drafting aid, and one
  entry per theme with R9.2's fields.
- **Examples.** An example points into a training bundle, in the form of a gold
  quote, or is synthetic, flagged, and in the user's words (A §611). None points
  outside the training partition (R12.3).
- **The hash.** The content hash covers everything but ``status``, ``approval``, and
  itself, so ADR 0003 can cite it before the approval is written (plan 9).
- **Frozen.** An approved version never changes. A claim no theme fits is recorded
  as ``unmatched``, never as a new theme (R9.3).
- ``sector_applicability`` is ``all`` or the codebook's own tags, mapped to no
  issuer (GS16).
"""

from collections.abc import Mapping, Sequence
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self

from earnings_core import RejectionReason, digest
from pydantic import Field, NonNegativeInt, StringConstraints, model_validator

from earnings_themes import tomlfile
from earnings_themes.anchoring import Bundle, SpanPointer, anchor, check_pointer
from earnings_themes.problems import Problem, Refusal
from earnings_themes.records import (
    IdPart,
    NonBlank,
    Part,
    Pin,
    Sha256Hex,
    ThemesRecord,
    parse,
)
from earnings_themes.split import Partition, SplitManifest
from earnings_themes.wording import labelled_strings, shared

CODEBOOK_ID = "djia-pilot"
CODEBOOK_VERSION = 0
UNMATCHED = "unmatched"
"""What an assignment names when no theme fits its claim (R9.3)."""

ThemeId = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_.-]*$")]
SectorTag = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]*$")]
Some = Field(min_length=1)


class CodebookStatus(StrEnum):
    """Whether a version is approved."""

    DRAFT = "draft"
    APPROVED = "approved"


class ExamplePointer(SpanPointer):
    """A training bundle's quote, as a gold quote points at one."""

    event_id: IdPart
    doc_id: NonBlank


class Example(Part):
    """A pointer into a training bundle, or a synthetic example in the user's words."""

    synthetic: bool = False
    text: NonBlank | None = None
    pointer: ExamplePointer | None = None

    @model_validator(mode="after")
    def _one_kind(self) -> Self:
        if self.synthetic != (self.text is not None) or self.synthetic == (
            self.pointer is not None
        ):
            raise ValueError("an example is a pointer, or synthetic with its text")
        return self


class Theme(Part):
    """One theme's definition (R9.2)."""

    theme_id: ThemeId
    parent_id: ThemeId | None = None
    label: NonBlank
    definition: NonBlank
    inclusion_rules: Annotated[tuple[NonBlank, ...], Some]
    exclusion_rules: Annotated[tuple[NonBlank, ...], Some]
    positive_examples: Annotated[tuple[Example, ...], Some]
    hard_negatives: Annotated[tuple[Example, ...], Some]
    sector_applicability: Literal["all"] | Annotated[tuple[SectorTag, ...], Some]


class DiscoveryCorpus(Part):
    """The training bundles the codebook was discovered from (R12.3)."""

    pin: Pin
    split_hash: Sha256Hex
    event_ids: tuple[IdPart, ...]
    doc_ids: tuple[NonBlank, ...]


class CodebookRules(Part):
    """The multi-label and boilerplate rules, in the user's words."""

    multi_label: NonBlank
    boilerplate: NonBlank


class Approval(Part):
    """Who approved the version, when, and the decision record that says so."""

    approver: NonBlank
    approved_on: date
    adr: NonBlank


class DraftingAid(Part):
    """The model that drafted, and when (GS4, GS9)."""

    model_id: NonBlank
    drafted_on: date


class Codebook(ThemesRecord):
    """``codebook-v<N>.toml``: one codebook version."""

    codebook_id: IdPart
    codebook_version: NonNegativeInt
    status: CodebookStatus
    content_hash: Sha256Hex
    discovery_corpus: DiscoveryCorpus
    rules: CodebookRules
    approval: Approval | None = None
    drafting_aid: DraftingAid
    themes: Annotated[tuple[Theme, ...], Some]

    @model_validator(mode="after")
    def _approved_with_its_approval(self) -> Self:
        if (self.status is CodebookStatus.APPROVED) != (self.approval is not None):
            raise ValueError("an approved version has its approval, and only it")
        return self

    def theme_ids(self) -> frozenset[str]:
        return frozenset(theme.theme_id for theme in self.themes)


class ExampleDraft(Part):
    """An example as a draft names it: by its text, in one training bundle."""

    event_id: IdPart | None = None
    text: NonBlank
    prefix: str = ""
    suffix: str = ""
    synthetic: bool = False


class ThemeDraft(Part):
    """A theme as a draft proposes it."""

    theme_id: ThemeId
    parent_id: ThemeId | None = None
    label: NonBlank
    definition: NonBlank
    inclusion_rules: Annotated[tuple[NonBlank, ...], Some]
    exclusion_rules: Annotated[tuple[NonBlank, ...], Some]
    sector_applicability: Literal["all"] | Annotated[tuple[SectorTag, ...], Some]
    positive_examples: Annotated[tuple[ExampleDraft, ...], Some]
    hard_negatives: Annotated[tuple[ExampleDraft, ...], Some]


class CodebookDraft(Part):
    """``codebook.draft.toml`` and its working copy (the codebook brief)."""

    codebook_id: IdPart
    codebook_version: NonNegativeInt
    drafting_aid: DraftingAid
    rules: CodebookRules
    themes: Annotated[tuple[ThemeDraft, ...], Some]


def codebook_hash(codebook: Codebook) -> str:
    """The content hash: every field but ``status``, ``approval``, and itself."""
    return digest(
        codebook.model_dump(mode="json", exclude={"status", "approval", "content_hash"})
    )


def _structure(themes: Sequence[ThemeDraft | Theme]) -> list[Refusal]:
    refusals = []
    ids = [theme.theme_id for theme in themes]
    for theme_id in sorted({i for i in ids if ids.count(i) > 1}):
        refusals.append(Refusal(f"theme {theme_id}", Problem.DUPLICATE_ID))
    if UNMATCHED in ids:
        refusals.append(Refusal(f"theme {UNMATCHED}", Problem.DUPLICATE_ID))
    parents = {theme.theme_id: theme.parent_id for theme in themes}
    for theme in themes:
        if theme.parent_id is not None and theme.parent_id not in parents:
            refusals.append(Refusal(f"theme {theme.theme_id}", Problem.UNKNOWN_THEME))
    for theme_id in parents:
        seen, current = set(), theme_id
        while current is not None and current in parents and current not in seen:
            seen.add(current)
            current = parents[current]
        if current is not None and current in seen:
            refusals.append(Refusal(f"theme {theme_id}", Problem.PARENT_CYCLE))
    return refusals


def _training(split: SplitManifest, bundles: Mapping[str, Bundle]) -> dict[str, Bundle]:
    """The discovery corpus: each training event with a parsed document. An event
    whose release is unavailable has no text to discover from (D4)."""
    return {e: bundles[e] for e in split.events_in(Partition.TRAIN) if e in bundles}


def _wording(record: object, bundles: Mapping[str, Bundle]) -> list[Refusal]:
    found = shared(
        labelled_strings(record),
        ((name, b.document.canonical_text) for name, b in bundles.items()),
    )
    return [
        Refusal(f"{label} ({name})", Problem.SOURCE_WORDING)
        for label, name in sorted(found)
    ]


def _example(
    draft: ExampleDraft, subject: str, train: set[str], bundles: Mapping[str, Bundle]
) -> Example | Refusal:
    if draft.synthetic:
        if draft.event_id is not None or draft.prefix or draft.suffix:
            return Refusal(subject, Problem.MALFORMED)
        return Example(synthetic=True, text=draft.text)
    if draft.event_id is None:
        return Refusal(subject, Problem.SYNTHETIC_UNFLAGGED)
    if draft.event_id not in train:
        return Refusal(subject, Problem.OUTSIDE_TRAINING)
    bundle = bundles.get(draft.event_id)
    if bundle is None:
        return Refusal(subject, Problem.UNKNOWN_DOCUMENT)
    pointer = anchor(bundle, draft.text, draft.prefix, draft.suffix)
    if isinstance(pointer, str):
        return Refusal(subject, pointer)
    return Example(
        pointer=ExamplePointer(
            **pointer.model_dump(),
            event_id=draft.event_id,
            doc_id=bundle.document.doc_id,
        )
    )


def _theme(
    draft: ThemeDraft, train: set[str], bundles: Mapping[str, Bundle]
) -> Theme | list[Refusal]:
    subject = f"theme {draft.theme_id}"
    lists: dict[str, list[Example]] = {"positive_examples": [], "hard_negatives": []}
    refusals = []
    for field, kept in lists.items():
        for index, example in enumerate(getattr(draft, field)):
            made = _example(example, f"{subject}.{field}[{index}]", train, bundles)
            if isinstance(made, Refusal):
                refusals.append(made)
            else:
                kept.append(made)
    if refusals:
        return refusals
    fields = draft.model_dump(exclude={"positive_examples", "hard_negatives"})
    return Theme(**fields, **{field: tuple(made) for field, made in lists.items()})


def freeze_codebook(
    draft: CodebookDraft,
    *,
    pin: Pin,
    split: SplitManifest,
    bundles: Mapping[str, Bundle],
    approval: Approval | None = None,
) -> Codebook | list[Refusal]:
    """The version ``draft`` defines, with its examples anchored in the training
    bundles, or every reason it cannot be frozen. ``bundles`` holds each pilot
    event with a parsed document; only the training partition's are read."""
    refusals = []
    if (draft.codebook_id, draft.codebook_version) != (CODEBOOK_ID, CODEBOOK_VERSION):
        refusals.append(Refusal("codebook", Problem.WRONG_CODEBOOK))
    if split.pin != pin:
        refusals.append(Refusal("split", Problem.WRONG_PIN))
    training = _training(split, bundles)
    if not training:
        refusals.append(Refusal("discovery_corpus", Problem.UNKNOWN_DOCUMENT))
    if refusals:
        return refusals
    refusals += _structure(draft.themes)
    themes = []
    for theme_draft in draft.themes:
        made = _theme(theme_draft, set(split.events_in(Partition.TRAIN)), training)
        if isinstance(made, list):
            refusals += made
        else:
            themes.append(made)
    if refusals:
        return refusals
    codebook = Codebook(
        codebook_id=draft.codebook_id,
        codebook_version=draft.codebook_version,
        status=CodebookStatus.APPROVED if approval else CodebookStatus.DRAFT,
        content_hash="0" * 64,
        discovery_corpus=DiscoveryCorpus(
            pin=pin,
            split_hash=split.content_hash,
            event_ids=tuple(training),
            doc_ids=tuple(bundle.document.doc_id for bundle in training.values()),
        ),
        rules=draft.rules,
        approval=approval,
        drafting_aid=draft.drafting_aid,
        themes=tuple(themes),
    )
    if refusals := _wording(codebook.model_dump(mode="json"), training):
        return refusals
    return codebook.model_copy(update={"content_hash": codebook_hash(codebook)})


def validate_codebook(
    codebook: Codebook,
    *,
    pin: Pin,
    split: SplitManifest,
    bundles: Mapping[str, Bundle],
    adr_text: str | None,
) -> list[Refusal]:
    """Every reason a frozen version does not hold; empty when it does."""
    refusals = []
    if (codebook.codebook_id, codebook.codebook_version) != (
        CODEBOOK_ID,
        CODEBOOK_VERSION,
    ):
        refusals.append(Refusal("codebook", Problem.WRONG_CODEBOOK))
    if codebook_hash(codebook) != codebook.content_hash:
        refusals.append(Refusal("codebook.content_hash", Problem.CONTENT_HASH_MISMATCH))
    if codebook.status is not CodebookStatus.APPROVED:
        refusals.append(Refusal("codebook.status", Problem.CODEBOOK_NOT_APPROVED))
    elif adr_text is None or codebook.content_hash not in adr_text:
        refusals.append(Refusal("codebook.approval.adr", Problem.ADR_NOT_CITED))
    corpus = codebook.discovery_corpus
    if corpus.pin != pin:
        refusals.append(Refusal("discovery_corpus.pin", Problem.WRONG_PIN))
    if corpus.split_hash != split.content_hash:
        refusals.append(Refusal("discovery_corpus.split_hash", Problem.WRONG_SPLIT))
    training = _training(split, bundles)
    doc_ids = tuple(bundle.document.doc_id for bundle in training.values())
    if (corpus.event_ids, corpus.doc_ids) != (tuple(training), doc_ids):
        refusals.append(Refusal("discovery_corpus", Problem.DISCOVERY_CORPUS))
    refusals += _structure(codebook.themes)
    train = set(split.events_in(Partition.TRAIN))
    for theme in codebook.themes:
        for field in ("positive_examples", "hard_negatives"):
            for index, example in enumerate(getattr(theme, field)):
                subject = f"theme {theme.theme_id}.{field}[{index}]"
                refusals += _pointer_refusals(example, subject, training, train)
    return refusals + _wording(codebook.model_dump(mode="json"), training)


def _pointer_refusals(
    example: Example, subject: str, bundles: Mapping[str, Bundle], train: set[str]
) -> list[Refusal]:
    pointer = example.pointer
    if pointer is None:
        return []
    if pointer.event_id not in train:
        return [Refusal(subject, Problem.OUTSIDE_TRAINING)]
    bundle = bundles.get(pointer.event_id)
    if bundle is None:
        return [Refusal(subject, Problem.UNKNOWN_DOCUMENT)]
    if pointer.doc_id != bundle.document.doc_id:
        return [Refusal(subject, RejectionReason.WRONG_DOCUMENT)]
    span = SpanPointer(**pointer.model_dump(exclude={"event_id", "doc_id"}))
    return [Refusal(subject, reason) for reason in check_pointer(bundle, span)]


def codebook_toml(codebook: Codebook) -> str:
    """The committed file: pointers, hashes, and the user's words, never a quote."""
    header = (
        f"Codebook {codebook.codebook_id} v{codebook.codebook_version}"
        " (Stage 6, GS9). Written by `earnings-pipeline codebook freeze`;"
        " never edited. Examples are pointers or synthetic."
    )
    return tomlfile.dumps(codebook.model_dump(mode="python"), header=header)


def load_codebook(path: Path) -> Codebook:
    """A committed codebook version, read through its contract."""
    return parse(tomlfile.read(path), Codebook, path.name)


def load_codebook_draft(path: Path) -> CodebookDraft:
    """A local codebook draft or working copy, read through its contract."""
    return parse(tomlfile.read(path), CodebookDraft, path.name)
