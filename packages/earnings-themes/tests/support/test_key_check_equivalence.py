"""The support-cache key check, pinned against a frozen oracle (plan 24, Task 1).

The oracle is a test-only restatement of today's ``SupportCacheKey.__new__``,
``_validate_binding`` and ``_material_kind``, with no memo anywhere. The corpus holds
the real scorer and judge materials of the invented ``assessed_case`` and a labeled
mutation of them for each way a text can differ from them. A faster key check must
give the oracle's outcome on every one of these, accepted or refused, with a cold
memo or a warm one (plan 24, Global Constraints). Invented text only (GS13).

Tasks 2 and 3 import ``corpus``, ``outcome`` and the three ``oracle_*`` functions
from this module.
"""

import json
import tempfile
from collections import OrderedDict
from datetime import date
from functools import cache
from importlib import import_module
from pathlib import Path

import pytest
from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    OverlayMask,
    TextSpan,
    canonical_json,
    digest,
    sha256_hex,
)
from earnings_themes.codebook import Approval, CodebookDraft, freeze_codebook
from earnings_themes.coding.records import CodingPolicy
from earnings_themes.extraction.prompt import parse_template
from earnings_themes.extraction.records import Claim, Parameters, Quote, RunRecord
from earnings_themes.records import parse
from earnings_themes.support import cache as cache_module
from earnings_themes.support.cache import (
    _BINDING_FIELDS,
    SupportCacheKey,
    _check_records,
    _material_kind,
    _validate_binding,
)
from earnings_themes.support.judges import JudgeRequest
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import (
    SUPPORT_SCHEMA_VERSION,
    SUPPORT_VERSION,
    ContextReference,
    EvidenceReference,
    JudgeIdentity,
    RuntimeIdentity,
    ScorerIdentity,
    SupportPolicy,
    TargetRecord,
)
from earnings_themes.support.scorers import ScoreRequest
from earnings_themes.synthetic import (
    DEV,
    LATER,
    PIN,
    TEST,
    TRAIN,
    build_synthetic,
    codebook_draft,
    synthetic_split,
)

from .test_cache_known_answer import SUPPORT_CACHE_NAMES

_cases = import_module("packages.earnings-themes.tests.coding.cases")

REPO = Path(__file__).resolve().parents[4]
KINDS = ("scorer", "judge")
OTHER = {"scorer": "judge", "judge": "scorer"}
ACUTE = chr(0xE9)
BACKSLASH = chr(92)
SURROGATE = chr(0xD800)


# --- The oracle: today's logic, frozen, with no memo ---------------------------------


def oracle_key(material: str) -> str:
    """Today's ``SupportCacheKey.__new__``: the digest text, or ``malformed_record``."""
    try:
        canonical = canonical_json(json.loads(material)).decode()
        if type(material) is not str or canonical != material:
            raise ValueError
        return digest(json.loads(material))
    except (ValueError, TypeError, AttributeError):
        raise SupportError("malformed_record") from None


def oracle_binding(key_text: str, material_text: str, kind: str) -> tuple:
    """Today's ``_validate_binding`` body, over the unmemoized ``_check_records``."""
    try:
        material = json.loads(material_text)
        if set(material) != _BINDING_FIELDS:
            raise ValueError
        canonical = canonical_json(material)
        if (
            canonical.decode() != material_text
            or sha256_hex(canonical) != key_text
            or material["kind"] != kind
            or material["schema_version"] != SUPPORT_SCHEMA_VERSION
            or material["support_version"] != SUPPORT_VERSION
        ):
            raise ValueError
        for name, model in (
            ("record", TargetRecord),
            ("policy", SupportPolicy),
            ("source_run", RunRecord),
        ):
            model.model_validate_json(canonical_json(material[name]))
        for name, model in (
            ("evidence", EvidenceReference),
            ("contexts", ContextReference),
            ("source_claims", Claim),
            ("source_quotes", Quote),
        ):
            if type(material[name]) is not list:
                raise ValueError
            _check_records(model, material[name])
        if type(material["claim"]) is not str or not material["claim"].strip():
            raise ValueError
        provenance = material["provenance_hash"]
        if (
            type(provenance) is not str
            or len(provenance) != 64
            or any(c not in "0123456789abcdef" for c in provenance)
        ):
            raise ValueError
        if type(material["bundles"]) is not list:
            raise ValueError
        for bundle in material["bundles"]:
            if set(bundle) != {"document", "elements", "masks"}:
                raise ValueError
            CanonicalDocument.model_validate_json(canonical_json(bundle["document"]))
            for name, model in (
                ("elements", DocumentElement),
                ("masks", OverlayMask),
            ):
                if type(bundle[name]) is not list:
                    raise ValueError
                _check_records(model, bundle[name])
        request = (
            ScoreRequest if kind == "scorer" else JudgeRequest
        ).model_validate_json(canonical_json(material["request"]))
        identity = (
            ScorerIdentity if kind == "scorer" else JudgeIdentity
        ).model_validate_json(canonical_json(material["identity"]))
        return request, identity
    except (ValueError, TypeError, KeyError, AttributeError):
        raise SupportError("malformed_record") from None


def oracle_kind(material: str) -> str:
    """Today's ``_material_kind``, without the ``lru_cache``."""
    return json.loads(material)["kind"]


def outcome(call, *args) -> tuple:
    """``("ok", value)``, or ``("refused", error type name, str(error))``."""
    try:
        return ("ok", call(*args))
    except Exception as error:  # noqa: BLE001 - the outcome is the exception itself
        return ("refused", type(error).__name__, str(error))


# --- The real materials: the invented ``assessed_case``, built without fixtures ------


def _real_materials() -> list[tuple[str, str]]:
    """The five support-cache entries of ``assessed_case``, as ``(label, material)``.

    The case is built as ``tests/coding/conftest.py`` builds it, and its entry names
    are pinned by ``test_cache_known_answer.py``, which this module checks again.
    """
    book = freeze_codebook(
        parse(codebook_draft(), CodebookDraft, "draft"),
        pin=PIN,
        split=synthetic_split(),
        bundles={e: build_synthetic(e).bundle for e in (TRAIN, DEV, TEST, LATER)},
        approval=Approval(
            approver="fixture",
            approved_on=date(2026, 10, 2),
            adr="docs/adr/0003-approve-pilot-codebook-v0.md",
        ),
    )
    template = parse_template(
        (REPO / "prompts/extraction/pointer-1.md").read_text(encoding="utf-8")
    )
    text = "Classify invented claims using only supplied frozen theme IDs."
    policy = CodingPolicy(
        prompt_text=text,
        prompt_hash=sha256_hex(text.encode("utf-8")),
        parameters=Parameters(max_tokens=64),
    )
    identity = JudgeIdentity(
        family="invented-classifier-family",
        runtime=RuntimeIdentity(
            model_id="invented-classifier",
            revision="fixture-1",
            files=(),
            runtime="scripted",
            runtime_version="1",
            device="cpu",
            precision="float32",
            encoding_version="fixture-1",
        ),
        input_limit=10000,
        output_limit=2048,
        hosting="scripted",
        weight_license=None,
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sources = _cases.make_sources(
            _cases.invented_codebook(book), _cases.invented_bundle(), template
        )
        job = _cases.make_proposal_job(sources, policy, identity, root)
        proposals, _ = job.run([{"theme_ids": ["capacity"], "attributes": {}}])
        _cases.make_assessed_case(proposals, sources, root)
        entries = [
            (path.name, json.loads(path.read_text(encoding="utf-8")))
            for path in sorted((root / "support-cache").rglob("*.json"))
        ]
    seen = {kind: 0 for kind in KINDS}
    real = []
    for name, entry in entries:
        assert name == f"{sha256_hex(entry['material'].encode())}.json"
        real.append((f"real-{entry['kind']}-{seen[entry['kind']]}", entry["material"]))
        seen[entry["kind"]] += 1
    return real


# --- The mutations -------------------------------------------------------------------


def _canonical(value) -> str:
    return canonical_json(value).decode()


def _dumps_in_order(body: dict) -> str:
    """Compact JSON that keeps each dict's own key order, instead of sorting."""
    return json.dumps(body, ensure_ascii=False, separators=(",", ":"))


def _edit(material: str, change) -> str:
    """The canonical text of ``material`` after ``change`` edits its parse."""
    body = json.loads(material)
    change(body)
    return _canonical(body)


def _head(material: str) -> str:
    """The canonical text up to the end of the top-level ``bundles`` value."""
    return '{"bundles":' + _canonical(json.loads(material)["bundles"])


def _swapped(material: str, first: str, second: str) -> str:
    body = json.loads(material)
    keys = list(body)
    i, j = keys.index(first), keys.index(second)
    keys[i], keys[j] = keys[j], keys[i]
    return _dumps_in_order({key: body[key] for key in keys})


def _reordered(material: str, name: str, inside=None) -> str:
    """``material`` with the keys of the first record under ``name`` reversed."""
    body = json.loads(material)
    record = body[name][0] if inside is None else inside(body[name][0])
    items = list(record.items())
    record.clear()
    record.update(reversed(items))
    return _dumps_in_order(body)


def _replaced(material: str, old: str, new: str) -> str:
    assert material.count(old) >= 1, old
    return material.replace(old, new, 1)


def _with_document_text(material: str, text: str) -> str:
    """The first bundle is replaced by a valid one that holds ``text``."""

    def change(body):
        bundle = body["bundles"][0]
        document = CanonicalDocument.create(
            source_document_id=bundle["document"]["source_document_id"],
            canonicalization_version=bundle["document"]["canonicalization_version"],
            canonical_text=text,
        )
        element = DocumentElement.create(
            document, ElementType.PARAGRAPH, TextSpan(start=0, end=len(text))
        )
        bundle["document"] = document.model_dump(mode="json")
        bundle["elements"] = [element.model_dump(mode="json")]

    return _edit(material, change)


def _drop_first_key(record: dict) -> None:
    del record[next(iter(record))]


def _mutations(base: str, kind: str) -> list[tuple[str, str]]:
    """Labeled mutations of the canonical ``base`` material, which is of ``kind``.
    Each is a text that a faster check must judge as today's code does.
    """
    head = _head(base)
    rest = base[len(head) :]
    assert rest.startswith(',"claim":')
    claim_json = _canonical(json.loads(base)["claim"])
    claim_piece = ',"claim":' + claim_json
    assert rest.startswith(claim_piece)
    first_comma = base.index(",")
    assert first_comma < len(head)

    def set_(name, value):
        return _edit(base, lambda b: b.__setitem__(name, value))

    def drop(name):
        return _edit(base, lambda b: b.pop(name))

    def in_bundle(change):
        return _edit(base, lambda b: change(b["bundles"][0]))

    def in_first(name, change):
        return _edit(base, lambda b: change(b[name][0]))

    def first_key_dropped(name):
        return _edit(base, lambda b: _drop_first_key(b[name]))

    claim_text = "An invented caf" + ACUTE + " claim."
    raw_accent = set_("claim", claim_text)
    accent_document = _with_document_text(base, "A caf" + ACUTE + " opened here.")
    marker_text = (
        'Lumen noted ,"claim": and ,"source_claims": and ,"source_quotes": '
        'and ,"source_run": in one invented sentence.'
    )
    escape_text = (
        'A "quoted" word, a backslash ' + BACKSLASH + " and a new" + chr(10) + "line."
    )

    labeled = [
        # The big values: one character, one number, one record, one list.
        (
            "document-char-changed",
            in_bundle(
                lambda x: x["document"].__setitem__(
                    "canonical_text", "X" + x["document"]["canonical_text"][1:]
                )
            ),
        ),
        (
            "element-end-changed",
            in_bundle(lambda x: x["elements"][0]["span"].__setitem__("end", 42)),
        ),
        (
            "element-type-invalid",
            in_bundle(lambda x: x["elements"][0].__setitem__("type", "invented")),
        ),
        ("mask-record-invalid", in_bundle(lambda x: x["masks"].append({}))),
        ("bundle-extra-key", in_bundle(lambda x: x.__setitem__("extra", 1))),
        ("bundle-masks-dropped", in_bundle(lambda x: x.pop("masks"))),
        ("bundle-elements-not-a-list", in_bundle(lambda x: x.update(elements={}))),
        ("bundle-not-an-object", set_("bundles", [5])),
        (
            "bundles-duplicated",
            _edit(base, lambda b: b["bundles"].append(b["bundles"][0])),
        ),
        ("bundles-empty", set_("bundles", [])),
        ("bundles-null", set_("bundles", None)),
        ("bundles-not-a-list", set_("bundles", {})),
        ("bundles-dropped", drop("bundles")),
        (
            "source-claims-record-changed",
            in_first(
                "source_claims", lambda x: x.__setitem__("claim", "A changed claim.")
            ),
        ),
        (
            "source-claims-record-invalid",
            in_first("source_claims", lambda x: x.__setitem__("claim_id", 7)),
        ),
        ("source-claims-empty", set_("source_claims", [])),
        (
            "source-quotes-record-changed",
            in_first("source_quotes", lambda x: x["span"].__setitem__("prefix", "p")),
        ),
        (
            "source-quotes-record-invalid",
            in_first("source_quotes", lambda x: x.__setitem__("mask_ids", "m")),
        ),
        ("source-quotes-empty", set_("source_quotes", [])),
        # The same texts, with the markers a split looks for inside a big value.
        (
            "nested-claim-key-in-first-element",
            in_bundle(lambda x: x["elements"][0].__setitem__("claim", "nested")),
        ),
        (
            "nested-claim-key-in-document",
            in_bundle(lambda x: x["document"].__setitem__("claim", "nested")),
        ),
        (
            "nested-source-quotes-key-in-a-claim",
            in_first("source_claims", lambda x: x.__setitem__("source_quotes", [])),
        ),
        (
            "nested-source-run-key-in-a-quote",
            in_first("source_quotes", lambda x: x.__setitem__("source_run", {})),
        ),
        (
            "marker-text-in-escaped-document-string",
            _with_document_text(base, marker_text),
        ),
        (
            "quote-and-backslash-in-escaped-document-string",
            _with_document_text(base, escape_text),
        ),
        ("non-ascii-in-document-text", accent_document),
        (
            "non-ascii-in-document-text-escaped",
            accent_document.replace(ACUTE, BACKSLASH + "u00e9"),
        ),
        # The rest of the key.
        ("claim-blank", set_("claim", "   ")),
        ("claim-not-a-string", set_("claim", 5)),
        ("claim-with-raw-non-ascii", raw_accent),
        (
            "claim-with-escaped-non-ascii",
            raw_accent.replace(ACUTE, BACKSLASH + "u00e9"),
        ),
        (
            "provenance-upper-case",
            _edit(
                base,
                lambda b: b.__setitem__(
                    "provenance_hash", b["provenance_hash"].upper()
                ),
            ),
        ),
        ("provenance-too-short", set_("provenance_hash", "a" * 63)),
        ("provenance-null", set_("provenance_hash", None)),
        ("kind-other-valid", set_("kind", OTHER[kind])),
        ("kind-invalid", set_("kind", "other")),
        ("kind-not-a-string", set_("kind", 5)),
        ("kind-dropped", drop("kind")),
        ("schema-version-changed", set_("schema_version", 2)),
        ("support-version-changed", set_("support_version", "semantic-support/2")),
        ("extra-key-sorted-first", set_("a", 1)),
        ("extra-key-sorted-last", set_("zzz", 1)),
        ("key-dropped-claim", drop("claim")),
        ("key-dropped-policy", drop("policy")),
        ("key-dropped-source-quotes", drop("source_quotes")),
        ("evidence-not-a-list", set_("evidence", {})),
        ("evidence-record-invalid", set_("evidence", [{}])),
        ("contexts-record-invalid", set_("contexts", [{}])),
        ("record-first-key-dropped", first_key_dropped("record")),
        ("policy-first-key-dropped", first_key_dropped("policy")),
        ("source-run-first-key-dropped", first_key_dropped("source_run")),
        ("request-first-key-dropped", first_key_dropped("request")),
        ("identity-first-key-dropped", first_key_dropped("identity")),
        # Not canonical: whitespace, escapes, number forms, key order, duplicates.
        (
            "space-after-comma-in-the-rest",
            base[: len(head) + 1] + " " + base[len(head) + 1 :],
        ),
        (
            "space-after-comma-in-bundles",
            base[: first_comma + 1] + " " + base[first_comma + 1 :],
        ),
        (
            "space-before-colon-in-source-quotes",
            _replaced(base, '"source_quotes":', '"source_quotes" :'),
        ),
        ("space-leading", " " + base),
        ("newline-trailing", base + "\n"),
        (
            "escaped-solidus-in-the-rest",
            _replaced(
                base, "semantic-support/1", "semantic-support" + BACKSLASH + "/1"
            ),
        ),
        (
            "float-for-integer-in-the-rest",
            _replaced(
                base,
                '"schema_version":1,"source_claims"',
                '"schema_version":1.0,"source_claims"',
            ),
        ),
        (
            "float-for-integer-in-bundles",
            _replaced(base, '"start":0}', '"start":0.0}'),
        ),
        (
            "float-for-integer-in-source-quotes",
            _replaced(base, '"start":0,"suffix"', '"start":0.0,"suffix"'),
        ),
        ("nan-for-integer-in-bundles", _replaced(base, '"start":0}', '"start":NaN}')),
        (
            "lone-surrogate-in-bundles",
            _replaced(base, "Lumen", "Lum" + SURROGATE + "n"),
        ),
        ("keys-swapped-kind-and-request", _swapped(base, "kind", "request")),
        ("keys-swapped-bundles-and-claim", _swapped(base, "bundles", "claim")),
        (
            "keys-swapped-source-claims-and-quotes",
            _swapped(base, "source_claims", "source_quotes"),
        ),
        (
            "keys-swapped-source-run-and-version",
            _swapped(base, "source_run", "support_version"),
        ),
        (
            "keys-reordered-in-bundles",
            _reordered(base, "bundles", lambda x: x["elements"][0]),
        ),
        ("keys-reordered-in-source-claims", _reordered(base, "source_claims")),
        (
            "duplicate-key-claim",
            base[: len(head)] + claim_piece + claim_piece + rest[len(claim_piece) :],
        ),
        ("duplicate-key-bundles-first-empty", '{"bundles":[],' + base[1:]),
        (
            "duplicate-key-in-a-claim",
            _replaced(base, '"attempt":1,', '"attempt":1,"attempt":1,'),
        ),
        # Not JSON, or not the whole text.
        ("trailing-text", base + "x"),
        ("trailing-object", base + "{}"),
        ("truncated-by-one", base[:-1]),
        ("truncated-in-bundles", base[: len(head) // 2]),
        ("empty-text", ""),
        ("stray-comma", _replaced(base, ',"claim":', ',,"claim":')),
        ("unbalanced-bracket", _replaced(base, "]", "")),
        ("unterminated-string", base[:-2]),
        ("top-level-object-empty", "{}"),
        ("top-level-list", "[" + base + "]"),
        ("top-level-null", "null"),
    ]
    return labeled


@cache
def _corpus() -> tuple[tuple[str, str], ...]:
    real = _real_materials()
    first = {
        kind: next(m for label, m in real if label.startswith(f"real-{kind}-"))
        for kind in KINDS
    }
    mutated = []
    for kind in KINDS:
        for label, material in _mutations(first[kind], kind):
            assert material != first[kind], label
            mutated.append((f"{kind}-{label}", material))
    return (*real, *mutated)


def corpus() -> list[tuple[str, str]]:
    """Labeled materials: the real ones first, then each mutation of one real
    scorer material and of one real judge material."""
    return list(_corpus())


def forget_memos() -> None:
    """Empty every process-wide memo of ``cache.py``: each ``lru_cache`` and each
    module-level ``OrderedDict``, so a memo that a later task adds is cleared too."""
    for value in vars(cache_module).values():
        if hasattr(value, "cache_clear"):
            value.cache_clear()
        elif isinstance(value, OrderedDict):
            value.clear()


def warm_memos() -> None:
    """Fill every memo from the real materials, as a run's earlier keys do."""
    for label, material in corpus():
        if label.startswith("real-"):
            kind = label.split("-")[1]
            key = SupportCacheKey(material)
            _validate_binding(str(key), material, kind)
            _material_kind(material)


def key_text_for(material: str) -> str:
    """The oracle's digest when it accepts the material, else the hash of its bytes."""
    accepted = outcome(oracle_key, material)
    # A lone surrogate has no UTF-8 form, so the stand-in hash keeps it as it is.
    return (
        accepted[1]
        if accepted[0] == "ok"
        else sha256_hex(material.encode("utf-8", "surrogatepass"))
    )


def assert_matches_oracle(material: str) -> None:
    """Today's three functions give the oracle's outcome, refused or accepted."""
    expected = outcome(oracle_key, material)
    assert outcome(lambda: str(SupportCacheKey(material))) == expected
    key_text = key_text_for(material)
    for kind in KINDS:
        assert outcome(_validate_binding, key_text, material, kind) == outcome(
            oracle_binding, key_text, material, kind
        )
    assert outcome(_material_kind, material) == outcome(oracle_kind, material)


@pytest.fixture(autouse=True)
def fresh_memos():
    forget_memos()
    yield
    forget_memos()


def real_materials() -> list[tuple[str, str]]:
    return [(label, m) for label, m in corpus() if label.startswith("real-")]


def test_the_oracle_accepts_the_real_materials():
    real = real_materials()
    assert len(real) == len(SUPPORT_CACHE_NAMES) == 5
    assert {label.split("-")[1] for label, _ in real} == set(KINDS)
    names = []
    for label, material in real:
        kind = label.split("-")[1]
        digest_text = oracle_key(material)
        names.append(f"{digest_text}.json")
        request, identity = oracle_binding(digest_text, material, kind)
        assert oracle_kind(material) == kind
        # Today's code returns the same values.
        key = SupportCacheKey(material)
        assert type(key) is SupportCacheKey
        assert str(key) == digest_text
        assert key.material == material
        assert _validate_binding(digest_text, material, kind) == (request, identity)
        assert _material_kind(material) == kind
    assert sorted(names) == SUPPORT_CACHE_NAMES


def test_the_corpus_covers_the_ways_a_text_can_differ():
    labeled = corpus()
    labels = [label for label, _ in labeled]
    assert len(labels) == len(set(labels))
    assert len(labeled) >= 25
    refused = {"key": 0, "binding": 0, "kind": 0}
    for _, material in labeled:
        if outcome(oracle_key, material)[0] == "refused":
            refused["key"] += 1
        text = key_text_for(material)
        if all(
            outcome(oracle_binding, text, material, k)[0] == "refused" for k in KINDS
        ):
            refused["binding"] += 1
        if outcome(oracle_kind, material)[0] == "refused":
            refused["kind"] += 1
    assert min(refused.values()) >= 5, refused
    # Both outcomes occur among the mutations, not only refusals.
    accepted = [
        label
        for label, material in labeled
        if not label.startswith("real-")
        and any(
            outcome(oracle_binding, key_text_for(material), material, k)[0] == "ok"
            for k in KINDS
        )
    ]
    assert len(accepted) >= 5, accepted


def test_the_corpus_holds_the_structural_traps():
    by_label = dict(corpus())
    for kind in KINDS:
        nested = by_label[f"{kind}-nested-claim-key-in-document"]
        # The text ,"claim": sits inside the bundles value, before the top-level one.
        assert ',"claim":' in _head(nested)
        assert nested.startswith(_head(nested) + ',"claim":')
        escaped = by_label[f"{kind}-marker-text-in-escaped-document-string"]
        # The same characters in a document string are escaped: no marker appears
        # in the bundles value, and the key is still accepted.
        assert ',"claim":' not in _head(escaped)
        assert BACKSLASH + '"claim' + BACKSLASH + '":' in _head(escaped)
        assert outcome(oracle_key, escaped)[0] == "ok"
        assert outcome(oracle_binding, key_text_for(escaped), escaped, kind)[0] == "ok"
        # A nested key named as a later marker sits inside a big value.
        claims = by_label[f"{kind}-nested-source-quotes-key-in-a-claim"]
        assert ',"source_quotes":' in _canonical(json.loads(claims)["source_claims"])
        quotes = by_label[f"{kind}-nested-source-run-key-in-a-quote"]
        assert ',"source_run":' in _canonical(json.loads(quotes)["source_quotes"])


@pytest.mark.parametrize(
    ("label", "material"), corpus(), ids=[label for label, _ in corpus()]
)
def test_every_mutation_gets_the_oracles_outcome(label, material):
    for warm in (False, True):
        forget_memos()
        if warm:
            warm_memos()
        assert_matches_oracle(material)


def test_a_key_text_that_is_not_the_hash_of_the_material_is_refused():
    for label, material in real_materials():
        kind = label.split("-")[1]
        right = oracle_key(material)
        for wrong in (right.upper(), right[:-1], "", sha256_hex(b"other")):
            expected = outcome(oracle_binding, wrong, material, kind)
            assert expected == ("refused", "SupportError", "malformed_record")
            assert outcome(_validate_binding, wrong, material, kind) == expected
