"""Shared inputs for earnings-themes' tests: Stage 1's committed canonical fixtures,
read through earnings-core's contracts, the synthetic document, and the synthetic
codebook; and for the extractor, the prompt template, a socket guard, and scripted
replies. Tests hold only synthetic text and Stage 1's fixtures (GS13)."""

import json
import socket
from collections import Counter
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path

import pytest
from earnings_core import CanonicalDocument, DocumentElement, OverlayMask
from earnings_themes.anchoring import Bundle
from earnings_themes.codebook import Approval, Codebook, CodebookDraft, freeze_codebook
from earnings_themes.extraction.adapters import AdapterError, ModelReply, ModelRequest
from earnings_themes.extraction.prompt import PromptTemplate, parse_template
from earnings_themes.extraction.records import ExtractionProblem
from earnings_themes.extraction.windows import plan_windows
from earnings_themes.records import parse
from earnings_themes.synthetic import (
    DEV,
    LATER,
    PIN,
    TEST,
    TRAIN,
    Synthetic,
    build_synthetic,
    codebook_draft,
    synthetic_split,
)

REPO = Path(__file__).resolve().parents[3]
CANONICAL = REPO / "tests" / "fixtures" / "canonical"
TEMPLATE = REPO / "prompts" / "extraction" / "pointer-1.md"
FIXTURE_IDS = sorted(path.stem for path in CANONICAL.glob("*.json"))


def fixture_bundle(fixture_id: str) -> Bundle:
    """A Stage 1 canonical fixture, read record by record through the contracts."""
    data = json.loads((CANONICAL / f"{fixture_id}.json").read_text(encoding="utf-8"))

    def read(model, record):
        return model.model_validate_json(json.dumps(record))

    return Bundle(
        name=fixture_id,
        document=read(CanonicalDocument, data["document"]),
        elements=tuple(read(DocumentElement, r) for r in data["elements"]),
        masks=tuple(read(OverlayMask, r) for r in data["masks"]),
    )


@pytest.fixture
def synthetic() -> Synthetic:
    return build_synthetic()


@pytest.fixture(scope="session")
def fixtures() -> dict[str, Bundle]:
    return {fixture_id: fixture_bundle(fixture_id) for fixture_id in FIXTURE_IDS}


@pytest.fixture(scope="module")
def codebook() -> Codebook:
    """``codebook_draft``, frozen over the synthetic pilot's bundles and approved."""
    approval = Approval(
        approver="Lowell Mason",
        approved_on=date(2026, 10, 2),
        adr="docs/adr/0003-approve-pilot-codebook-v0.md",
    )
    made = freeze_codebook(
        parse(codebook_draft(), CodebookDraft, "draft"),
        pin=PIN,
        split=synthetic_split(),
        bundles={e: build_synthetic(e).bundle for e in (TRAIN, DEV, TEST, LATER)},
        approval=approval,
    )
    assert isinstance(made, Codebook)
    return made


@pytest.fixture(scope="session")
def template() -> PromptTemplate:
    """The committed prompt, read by the caller and passed in (ES17)."""
    return parse_template(TEMPLATE.read_text(encoding="utf-8"))


GUARDED = (
    (socket.socket, "connect"),
    (socket.socket, "connect_ex"),
    (socket, "create_connection"),
    (socket, "getaddrinfo"),
    (socket, "gethostbyname"),
    (socket, "gethostbyname_ex"),
)


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Each of ``GUARDED``'s socket connections and forward name lookups raises, and
    is recorded first, since a library may swallow the error: a test asserts the
    list is empty (R14.1). A send without a connection, a reverse lookup, a name
    imported from ``socket`` before the patch, and a socket opened in C or in
    another process all pass unguarded."""
    trips: list[str] = []

    def blocked(name: str) -> Callable[..., object]:
        def refuse(*args: object, **kwargs: object) -> object:
            trips.append(name)
            raise ConnectionRefusedError(f"the network is blocked here: {name}")

        return refuse

    for owner, name in GUARDED:
        monkeypatch.setattr(owner, name, blocked(f"{owner.__name__}.{name}"))
    return trips


def labels_of(request: ModelRequest) -> list[str]:
    """The labels code rendered for the request's window: U1 to Un."""
    return [f"U{n}" for n in range(1, len(request.subject.unit_ids) + 1)]


Script = Callable[[ModelRequest], ModelReply]


def cited(request: ModelRequest, **fields: object) -> ModelReply:
    """A reply that cites each label of the request's window alone, with an invented
    claim; ``fields`` are the reply's other fields."""
    candidates = [
        {"quote_labels": [label], "claim": f"An invented claim about {label}."}
        for label in labels_of(request)
    ]
    return ModelReply(text=json.dumps({"candidates": candidates}), **fields)


@pytest.fixture
def cite() -> Callable[..., ModelReply]:
    return cited


def mixed_script(bundles: Sequence[Bundle], budget: int | None) -> Script:
    """Replies of six kinds, by the window's place in the run, mod 6: 0 cites every
    label; 1 adds a candidate with an unknown label and one with a blank claim, then
    sends their corrections only; 2 is malformed, then valid; 3 never arrives, then
    is valid; 4 carries tool calls twice; and 5 states no claim."""
    windows = (
        (bundle.document.doc_id, window.window_id)
        for bundle in bundles
        for window in plan_windows(bundle, budget)
    )
    order = {key: index for index, key in enumerate(windows)}
    sent: Counter[tuple[str, str]] = Counter()

    def script(request: ModelRequest) -> ModelReply:
        key = (request.subject.doc_id, request.subject.window_id)
        sent[key] += 1
        kind, attempt = order[key] % 6, sent[key]
        if kind == 1:
            fixes = [
                {"quote_labels": ["U999" if attempt == 1 else "U1"], "claim": "Fix."},
                {"quote_labels": ["U1"], "claim": " " if attempt == 1 else "Fix 2."},
            ]
            body = json.loads(cited(request).text) if attempt == 1 else {}
            body["candidates"] = [*body.get("candidates", []), *fixes]
            return ModelReply(text=json.dumps(body), model="scripted")
        if kind == 2 and attempt == 1:
            return ModelReply(text="{", model="scripted")
        if kind == 3 and attempt == 1:
            raise AdapterError(ExtractionProblem.TRANSPORT_ERROR)
        if kind == 4:
            return ModelReply(text="", model="scripted", tool_calls=True)
        if kind == 5:
            return ModelReply(text='{"candidates": []}', model="scripted")
        return cited(request, model="scripted")

    return script


@pytest.fixture
def mixed() -> Callable[[Sequence[Bundle], int | None], Script]:
    return mixed_script
