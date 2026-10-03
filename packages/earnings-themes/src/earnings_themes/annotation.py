"""Drafts, origins, the build that anchors a working copy, and the validator (the
Stage 6 spec, §Anchoring and validation and §Drafting and tools; GS4, GS5).

- **Drafts.** A drafting session writes ``<name>.draft.toml``, which is kept
  unchanged, and the user edits ``<name>.working.toml`` beside it. Both name quotes
  by their text, with context when the text repeats.
- **The build.** Every working quote is anchored, every item's origin derived by
  comparing the working copy with the draft, and the result validated. Any refusal
  writes nothing, and names its item by ID, never by text.
- **The validator** rechecks a committed file against its local document: the pin,
  split, partition, and codebook, the signature, ``no_theme``, the IDs, every
  pointer, the origin counts, and the wording guard.
"""

from collections.abc import Callable, Hashable, Mapping, Sequence
from pathlib import Path
from typing import Annotated

from earnings_core import RejectionReason
from pydantic import BaseModel

from earnings_themes import tomlfile
from earnings_themes.anchoring import Bundle, SpanPointer, anchor, check_pointer
from earnings_themes.codebook import (
    UNMATCHED,
    Codebook,
    CodebookStatus,
    DraftingAid,
    ThemeId,
)
from earnings_themes.gold import (
    CodebookRef,
    DraftCounts,
    FixtureNegatives,
    Gold,
    GoldAssignment,
    GoldClaim,
    GoldQuote,
    HardNegative,
    HardNegativeSet,
    NegativeKind,
    Origin,
    ReleaseIdentification,
    Some,
    Support,
    no_theme_of,
)
from earnings_themes.problems import Problem, Refusal
from earnings_themes.records import IdPart, NonBlank, Part, Pin, parse
from earnings_themes.split import Partition, SplitManifest
from earnings_themes.wording import labelled_strings, shared


class QuoteDraft(Part):
    """A quote as a draft names it: its exact text, and context when it repeats."""

    quote_id: IdPart
    text: NonBlank
    prefix: str = ""
    suffix: str = ""


class ClaimDraft(Part):
    claim_id: IdPart
    quote_ids: Annotated[tuple[IdPart, ...], Some]
    claim: NonBlank


class AssignmentDraft(Part):
    claim_id: IdPart
    theme_id: ThemeId
    support: Support
    tie_group: IdPart | None = None


class HardNegativeDraft(Part):
    claim_id: IdPart
    quote_ids: Annotated[tuple[IdPart, ...], Some]
    claim: NonBlank
    negative_kind: NegativeKind
    theme_id: ThemeId | None = None


class GoldDraft(Part):
    """``<event>.draft.toml`` and its working copy (the gold brief)."""

    event_id: IdPart
    annotator: str = ""
    drafting_aid: DraftingAid
    no_theme: bool
    release_identification: ReleaseIdentification
    quotes: tuple[QuoteDraft, ...] = ()
    claims: tuple[ClaimDraft, ...] = ()
    assignments: tuple[AssignmentDraft, ...] = ()
    hard_negatives: tuple[HardNegativeDraft, ...] = ()


class FixtureDraft(Part):
    fixture_id: IdPart
    quotes: Annotated[tuple[QuoteDraft, ...], Some]
    hard_negatives: Annotated[tuple[HardNegativeDraft, ...], Some]


class CuratedDraft(Part):
    """``hard-negatives.draft.toml`` and its working copy (the gold brief)."""

    annotator: str = ""
    drafting_aid: DraftingAid
    documents: Annotated[tuple[FixtureDraft, ...], Some]


def signed(annotator: str) -> bool:
    """P9-18: a file is signed when its ``annotator`` is not blank."""
    return bool(annotator.strip())


def load_gold_draft(path: Path) -> GoldDraft:
    return parse(tomlfile.read(path), GoldDraft, path.name)


def load_curated_draft(path: Path) -> CuratedDraft:
    return parse(tomlfile.read(path), CuratedDraft, path.name)


class _Origins:
    """Each working item's origin against the draft, and the counts (GS5)."""

    def __init__(self) -> None:
        self.counts = {origin: 0 for origin in Origin}
        self.rejected = 0

    def compare[T: BaseModel](
        self, drafted: Sequence[T], working: Sequence[T], key: Callable[[T], Hashable]
    ) -> list[Origin]:
        before = {key(item): item for item in drafted}
        kept = {key(item) for item in working}
        self.rejected += sum(1 for k in before if k not in kept)
        origins = []
        for item in working:
            if key(item) not in before:
                origin = Origin.ANNOTATOR_ADDED
            elif before[key(item)] == item:
                origin = Origin.DRAFTED_ACCEPTED
            else:
                origin = Origin.DRAFTED_EDITED
            self.counts[origin] += 1
            origins.append(origin)
        return origins

    def tally(self) -> DraftCounts:
        return DraftCounts(
            accepted=self.counts[Origin.DRAFTED_ACCEPTED],
            edited=self.counts[Origin.DRAFTED_EDITED],
            rejected=self.rejected,
            added=self.counts[Origin.ANNOTATOR_ADDED],
        )


def _by_id(item: BaseModel) -> Hashable:
    return getattr(item, "quote_id", None) or item.claim_id


def _by_row(item: AssignmentDraft) -> Hashable:
    return (item.claim_id, item.theme_id)


def _items(
    drafted: GoldDraft | FixtureDraft,
    working: GoldDraft | FixtureDraft,
    bundle: Bundle,
    origins: _Origins,
    prefix: str,
) -> tuple[dict[str, tuple], list[Refusal]]:
    refusals: list[Refusal] = []
    quotes = []
    marks = origins.compare(drafted.quotes, working.quotes, _by_id)
    for quote, origin in zip(working.quotes, marks, strict=True):
        pointer = anchor(bundle, quote.text, quote.prefix, quote.suffix)
        if isinstance(pointer, str):
            refusals.append(Refusal(f"{prefix}quote {quote.quote_id}", pointer))
            continue
        quotes.append(
            GoldQuote(**pointer.model_dump(), quote_id=quote.quote_id, origin=origin)
        )
    made: dict[str, tuple] = {"quotes": tuple(quotes)}
    kinds = [("hard_negatives", HardNegative, _by_id)]
    if isinstance(working, GoldDraft) and isinstance(drafted, GoldDraft):
        kinds = [
            ("claims", GoldClaim, _by_id),
            ("assignments", GoldAssignment, _by_row),
            *kinds,
        ]
    for field, model, key in kinds:
        items = getattr(working, field)
        marks = origins.compare(getattr(drafted, field), items, key)
        made[field] = tuple(
            model(**item.model_dump(), origin=origin)
            for item, origin in zip(items, marks, strict=True)
        )
    return made, refusals


def _codebook_ref(codebook: Codebook) -> CodebookRef:
    return CodebookRef(
        codebook_id=codebook.codebook_id,
        codebook_version=codebook.codebook_version,
        content_hash=codebook.content_hash,
    )


def build_gold(
    drafted: GoldDraft,
    working: GoldDraft,
    *,
    bundle: Bundle,
    pin: Pin,
    split: SplitManifest,
    codebook: Codebook,
) -> Gold | list[Refusal]:
    """The gold ``working`` defines over ``bundle``, or every reason it cannot be."""
    if {drafted.event_id, working.event_id} != {bundle.name}:
        return [Refusal("event_id", Problem.UNKNOWN_DOCUMENT)]
    origins = _Origins()
    made, refusals = _items(drafted, working, bundle, origins, "")
    if refusals:
        return refusals
    try:
        partition = split.partition_of(bundle.name)
    except KeyError:
        return [Refusal("event_id", Problem.UNKNOWN_DOCUMENT)]
    gold = Gold(
        event_id=bundle.name,
        document_id=f"{bundle.name}:release",
        doc_id=bundle.document.doc_id,
        canonical_hash=bundle.document.canonical_hash,
        pin=pin,
        split_hash=split.content_hash,
        partition=partition,
        codebook=_codebook_ref(codebook),
        annotator=working.annotator,
        drafting_aid=working.drafting_aid,
        counts=origins.tally(),
        no_theme=working.no_theme,
        release_identification=working.release_identification,
        **made,
    )
    refusals = validate_gold(
        gold,
        bundle=bundle,
        pin=pin,
        split=split,
        codebook=codebook,
        require_signature=False,
    )
    return refusals or gold


def _ids(
    quotes: Sequence[GoldQuote],
    claims: Sequence[GoldClaim],
    assignments: Sequence[GoldAssignment],
    negatives: Sequence[HardNegative],
    themes: frozenset[str],
    prefix: str,
) -> list[Refusal]:
    refusals = []
    quote_ids = [q.quote_id for q in quotes]
    claim_ids = [c.claim_id for c in (*claims, *negatives)]
    for name, ids in (("quote", quote_ids), ("claim", claim_ids)):
        for repeated in sorted({i for i in ids if ids.count(i) > 1}):
            refusals.append(Refusal(f"{prefix}{name} {repeated}", Problem.DUPLICATE_ID))
    for claim in (*claims, *negatives):
        for quote_id in claim.quote_ids:
            if quote_id not in quote_ids:
                subject = f"{prefix}claim {claim.claim_id}"
                refusals.append(Refusal(subject, Problem.UNKNOWN_QUOTE))
    cited = {q for claim in (*claims, *negatives) for q in claim.quote_ids}
    for quote_id in dict.fromkeys(quote_ids):
        if quote_id not in cited:
            refusals.append(Refusal(f"{prefix}quote {quote_id}", Problem.UNREFERENCED))
    rows = [(a.claim_id, a.theme_id) for a in assignments]
    for row in sorted({r for r in rows if rows.count(r) > 1}):
        refusals.append(Refusal(f"assignment {row[0]}/{row[1]}", Problem.DUPLICATE_ID))
    plain = {c.claim_id for c in claims}
    for a in assignments:
        subject = f"assignment {a.claim_id}/{a.theme_id}"
        if a.claim_id not in plain:
            refusals.append(Refusal(subject, Problem.UNKNOWN_CLAIM))
        if a.theme_id != UNMATCHED and a.theme_id not in themes:
            refusals.append(Refusal(subject, Problem.UNKNOWN_THEME))
    coded = {a.claim_id for a in assignments}
    for claim_id in dict.fromkeys(c.claim_id for c in claims):
        if claim_id not in coded:
            refusals.append(Refusal(f"{prefix}claim {claim_id}", Problem.UNREFERENCED))
    groups: dict[str, list[GoldAssignment]] = {}
    for a in assignments:
        if a.tie_group is not None:
            groups.setdefault(a.tie_group, []).append(a)
    for group, members in sorted(groups.items()):
        if len(members) == 1 or len({a.claim_id for a in members}) > 1:
            refusals.append(Refusal(f"tie_group {group}", Problem.TIE_GROUP))
    for negative in negatives:
        if negative.theme_id is not None and negative.theme_id not in themes:
            subject = f"{prefix}claim {negative.claim_id}"
            refusals.append(Refusal(subject, Problem.UNKNOWN_THEME))
    return refusals


def _pointers(
    quotes: Sequence[GoldQuote], bundle: Bundle, prefix: str
) -> list[Refusal]:
    return [
        Refusal(f"{prefix}quote {quote.quote_id}", reason)
        for quote in quotes
        for reason in check_pointer(
            bundle, SpanPointer(**quote.model_dump(exclude={"quote_id", "origin"}))
        )
    ]


def _counts(counts: DraftCounts, items: Sequence[BaseModel]) -> list[Refusal]:
    tally = {origin: 0 for origin in Origin}
    for item in items:
        tally[item.origin] += 1
    if (counts.accepted, counts.edited, counts.added) != (
        tally[Origin.DRAFTED_ACCEPTED],
        tally[Origin.DRAFTED_EDITED],
        tally[Origin.ANNOTATOR_ADDED],
    ):
        return [Refusal("counts", Problem.COUNTS_MISMATCH)]
    return []


def _wording(record: BaseModel, bundles: Mapping[str, Bundle]) -> list[Refusal]:
    found = shared(
        labelled_strings(record.model_dump(mode="json")),
        ((name, b.document.canonical_text) for name, b in bundles.items()),
    )
    return [
        Refusal(f"{label} ({name})", Problem.SOURCE_WORDING)
        for label, name in sorted(found)
    ]


def _codebook(ref: CodebookRef, codebook: Codebook) -> list[Refusal]:
    if ref != _codebook_ref(codebook):
        return [Refusal("codebook", Problem.WRONG_CODEBOOK)]
    if codebook.status is not CodebookStatus.APPROVED:
        return [Refusal("codebook", Problem.CODEBOOK_NOT_APPROVED)]
    return []


def validate_gold(
    gold: Gold,
    *,
    bundle: Bundle,
    pin: Pin,
    split: SplitManifest,
    codebook: Codebook,
    require_signature: bool = True,
) -> list[Refusal]:
    """Every reason a gold file does not hold over its bundle; empty when it does."""
    refusals = []
    document = bundle.document
    if (gold.event_id, gold.document_id) != (bundle.name, f"{bundle.name}:release"):
        refusals.append(Refusal("event_id", Problem.UNKNOWN_DOCUMENT))
    if gold.doc_id != document.doc_id:
        refusals.append(Refusal("doc_id", RejectionReason.WRONG_DOCUMENT))
    if gold.canonical_hash != document.canonical_hash:
        refusals.append(
            Refusal("canonical_hash", RejectionReason.CANONICAL_HASH_MISMATCH)
        )
    if gold.pin != pin:
        refusals.append(Refusal("pin", Problem.WRONG_PIN))
    if gold.split_hash != split.content_hash:
        refusals.append(Refusal("split_hash", Problem.WRONG_SPLIT))
    try:
        partition = split.partition_of(gold.event_id)
    except KeyError:
        partition = None
    if partition is Partition.EXCLUDED:
        refusals.append(Refusal("partition", Problem.EXCLUDED_EVENT))
    elif gold.partition != partition:
        refusals.append(Refusal("partition", Problem.WRONG_PARTITION))
    refusals += _codebook(gold.codebook, codebook)
    if require_signature and not signed(gold.annotator):
        refusals.append(Refusal("annotator", Problem.UNSIGNED))
    if gold.no_theme != no_theme_of(gold.assignments):
        refusals.append(Refusal("no_theme", Problem.NO_THEME_MISMATCH))
    refusals += _ids(
        gold.quotes,
        gold.claims,
        gold.assignments,
        gold.hard_negatives,
        codebook.theme_ids(),
        "",
    )
    refusals += _pointers(gold.quotes, bundle, "")
    items = [*gold.quotes, *gold.claims, *gold.assignments, *gold.hard_negatives]
    refusals += _counts(gold.counts, items)
    return refusals + _wording(gold, {bundle.name: bundle})


def build_curated(
    drafted: CuratedDraft,
    working: CuratedDraft,
    *,
    bundles: Mapping[str, Bundle],
    pin: Pin,
    codebook: Codebook,
) -> HardNegativeSet | list[Refusal]:
    """The curated hard negatives ``working`` defines over Stage 1's fixtures."""
    origins = _Origins()
    before = {d.fixture_id: d for d in drafted.documents}
    documents, refusals = [], []
    for document in working.documents:
        bundle = bundles.get(document.fixture_id)
        if bundle is None:
            refusals.append(
                Refusal(f"fixture {document.fixture_id}", Problem.UNKNOWN_DOCUMENT)
            )
            continue
        empty = FixtureDraft.model_construct(
            fixture_id=document.fixture_id, quotes=(), hard_negatives=()
        )
        made, found = _items(
            before.get(document.fixture_id, empty),
            document,
            bundle,
            origins,
            f"{document.fixture_id} ",
        )
        refusals += found
        if not found:
            documents.append(
                FixtureNegatives(
                    fixture_id=document.fixture_id,
                    doc_id=bundle.document.doc_id,
                    canonical_hash=bundle.document.canonical_hash,
                    **made,
                )
            )
    kept = {d.fixture_id for d in working.documents}
    for fixture_id, gone in before.items():
        if fixture_id not in kept:
            origins.rejected += len(gone.quotes) + len(gone.hard_negatives)
    if refusals:
        return refusals
    record = HardNegativeSet(
        pin=pin,
        annotator=working.annotator,
        drafting_aid=working.drafting_aid,
        counts=origins.tally(),
        codebook=_codebook_ref(codebook),
        documents=tuple(documents),
    )
    refusals = validate_curated(
        record, bundles=bundles, pin=pin, codebook=codebook, require_signature=False
    )
    return refusals or record


def validate_curated(
    record: HardNegativeSet,
    *,
    bundles: Mapping[str, Bundle],
    pin: Pin,
    codebook: Codebook,
    require_signature: bool = True,
) -> list[Refusal]:
    """Every reason the curated hard negatives do not hold; empty when they do.
    Their wording is checked against every fixture in ``bundles``, as the committed
    guard checks it, not only the fixtures they quote."""
    refusals = []
    if record.pin != pin:
        refusals.append(Refusal("pin", Problem.WRONG_PIN))
    refusals += _codebook(record.codebook, codebook)
    if require_signature and not signed(record.annotator):
        refusals.append(Refusal("annotator", Problem.UNSIGNED))
    kinds = {n.negative_kind for d in record.documents for n in d.hard_negatives}
    if kinds != set(NegativeKind):
        refusals.append(Refusal("hard_negatives", Problem.NEGATIVE_KINDS))
    items: list[BaseModel] = []
    for document in record.documents:
        prefix = f"{document.fixture_id} "
        bundle = bundles.get(document.fixture_id)
        if bundle is None:
            refusals.append(Refusal(prefix.strip(), Problem.UNKNOWN_DOCUMENT))
            continue
        if (document.doc_id, document.canonical_hash) != (
            bundle.document.doc_id,
            bundle.document.canonical_hash,
        ):
            refusals.append(Refusal(f"{prefix}doc_id", RejectionReason.WRONG_DOCUMENT))
            continue
        refusals += _ids(
            document.quotes,
            (),
            (),
            document.hard_negatives,
            codebook.theme_ids(),
            prefix,
        )
        refusals += _pointers(document.quotes, bundle, prefix)
        items += [*document.quotes, *document.hard_negatives]
    refusals += _counts(record.counts, items)
    return refusals + _wording(record, bundles)
