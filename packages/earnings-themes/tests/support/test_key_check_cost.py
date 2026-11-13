"""The key check reads each big constant text of one source once (plan 24, Tasks 2, 3).

A support-cache key holds three values that are the same in every key of one source:
``bundles``, ``source_claims`` and ``source_quotes``. The constructor, the binding
check and the kind read split the text at their fixed canonical markers, check each of
the three values once per SHA-256 of its text, and parse only the small rest. These
tests count the module-level bodies, over the invented ``assessed_case`` materials of
Task 1's corpus (GS13). They also hold the other side: the fast path only accepts, and
any text that is changed, that does not split, or that splits inside a value takes
today's path and gets today's outcome, with a cold memo or a warm one.
"""

import json
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

import pytest
from earnings_core import canonical_json, sha256_hex
from earnings_themes.support import cache as cache_module
from earnings_themes.support.cache import (
    SupportCache,
    SupportCacheKey,
    _material_kind,
    _validate_binding,
)

from .test_key_check_equivalence import (
    KINDS,
    OTHER,
    SURROGATE,
    _with_document_text,
    corpus,
    forget_memos,
    key_text_for,
    oracle_binding,
    oracle_key,
    oracle_kind,
    outcome,
    real_materials,
    warm_memos,
)

NAMES = ("bundles", "source_claims", "source_quotes")
MARKERS = {
    "bundles": ('{"bundles":', ',"claim":'),
    "source_claims": (',"source_claims":', ',"source_quotes":'),
    "source_quotes": (',"source_quotes":', ',"source_run":'),
}


@pytest.fixture(autouse=True)
def cold_memos():
    forget_memos()
    yield
    forget_memos()


def spy(monkeypatch):
    """Count calls to ``_check_fragment`` as ``(level, name)``, and keep no text."""
    calls = []
    real = cache_module._check_fragment

    def counting(level, name, fragment):
        calls.append((level, name))
        return real(level, name, fragment)

    monkeypatch.setattr(cache_module, "_check_fragment", counting)
    return calls


def key_outcome(material):
    """The digest text the constructor gives for ``material``, or its refusal."""
    return outcome(lambda: str(SupportCacheKey(material)))


def first_material(kind):
    return next(m for label, m in real_materials() if f"-{kind}-" in label)


def edited(material, change):
    """The canonical text of ``material`` after ``change`` edits its parse."""
    body = json.loads(material)
    change(body)
    return canonical_json(body).decode()


def dumped(body):
    """Canonical JSON text with no UTF-8 step, so a lone surrogate survives."""
    return json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def one_character_changed(name):
    """A change to the first record of one big value that keeps the text canonical."""

    def element_end(body):
        span = body["bundles"][0]["elements"][0]["span"]
        span["end"] += 1

    def claim_text(body):
        record = body["source_claims"][0]
        record["claim"] = "X" + record["claim"][1:]

    def quote_start(body):
        body["source_quotes"][0]["span"]["start"] += 1

    return {
        "bundles": element_end,
        "source_claims": claim_text,
        "source_quotes": quote_start,
    }[name]


def span_of(material, name):
    """The start and end of the text of one big value, read from the markers."""
    before, after = MARKERS[name]
    start = material.index(before) + len(before)
    return start, material.index(after, start)


def test_the_big_texts_of_one_source_are_checked_once_for_all_its_keys(monkeypatch):
    real = real_materials()
    assert {label.split("-")[1] for label, _ in real} == set(KINDS)
    calls = spy(monkeypatch)
    for _, material in real:
        SupportCacheKey(material)
    assert sorted(calls) == sorted(("canonical", name) for name in NAMES)
    for _ in range(2):
        for _, material in real:
            SupportCacheKey(material)
    assert len(calls) == 3


@pytest.mark.parametrize("name", NAMES)
def test_a_changed_fragment_is_checked_anew_and_refused(monkeypatch, name):
    material = first_material("scorer")
    SupportCacheKey(material)
    calls = spy(monkeypatch)
    # One changed character keeps the text canonical, so the oracle accepts it, with
    # another digest. Only the changed value is checked again.
    changed = edited(material, one_character_changed(name))
    assert changed != material
    assert key_outcome(changed) == outcome(oracle_key, changed)
    assert outcome(oracle_key, changed)[0] == "ok"
    assert str(SupportCacheKey(changed)) != str(SupportCacheKey(material))
    assert calls == [("canonical", name)]
    # The change that breaks canonical form is refused as the oracle refuses it, and
    # a refused value is not remembered: it is checked in full every time.
    start, end = span_of(material, name)
    comma = material.index(",", start)
    assert comma < end
    spaced = material[: comma + 1] + " " + material[comma + 1 :]
    expected = ("refused", "SupportError", "malformed_record")
    assert outcome(oracle_key, spaced) == expected
    calls.clear()
    for attempt in (1, 2, 3):
        assert key_outcome(spaced) == expected
        assert calls == [("canonical", name)] * attempt


def test_a_material_that_does_not_split_takes_todays_path(monkeypatch):
    calls = spy(monkeypatch)
    for text in (
        canonical_json({"a": 1}).decode(),
        "[]",
        "null",
        "",
        '{"bundles":[],"claim":"c"}',
        '{"bundles":[],"claim":"c","source_claims":[],"source_run":{}}',
        '{"bundles":[],"claim":"c","source_quotes":[],"source_run":{}}',
    ):
        assert cache_module._split_material(text) is None, text
        assert key_outcome(text) == outcome(oracle_key, text)
    assert calls == []
    assert cache_module._light_material("{}", "canonical") is None


def test_a_text_that_is_not_a_plain_str_takes_todays_path(monkeypatch):
    class Subclass(str):
        pass

    material = first_material("judge")
    calls = spy(monkeypatch)
    for text in (Subclass(material), material.encode(), None, 7):
        expected = outcome(oracle_key, text)
        assert expected == ("refused", "SupportError", "malformed_record")
        assert outcome(SupportCacheKey, text) == expected
    assert calls == []


def test_the_split_reads_the_three_values_and_the_rest():
    for _, material in real_materials():
        fragments, placeholder = cache_module._split_material(material)
        body = json.loads(material)
        assert fragments == tuple(canonical_json(body[n]).decode() for n in NAMES)
        for name in NAMES:
            body[name] = []
        assert placeholder == canonical_json(body).decode()
        assert len(placeholder) < 100_000
        assert len(placeholder) < len(material)
    # The first following marker ends a value, even when it lies inside the value.
    nested = edited(
        first_material("scorer"),
        lambda b: b["bundles"][0]["document"].__setitem__("claim", "nested"),
    )
    fragments, _ = cache_module._split_material(nested)
    with pytest.raises(ValueError):
        json.loads(fragments[0])


def test_the_fragment_memo_keeps_digests_only(monkeypatch):
    for _, material in real_materials():
        SupportCacheKey(material)
    memo = cache_module._checked_fragments
    assert len(memo) == 3
    for key, value in memo.items():
        assert value is None
        assert type(key) is tuple and len(key) == 2
        assert all(type(part) is str and len(part) <= 64 for part in key)
        assert len(key[1]) == 64
    texts = {f for _, m in real_materials() for f in cache_module._split_material(m)[0]}
    assert {key[1] for key in memo} == {sha256_hex(t.encode()) for t in texts}
    # The memo is bounded and drops the oldest entry first.
    assert cache_module._FRAGMENT_MEMO_SIZE == 64
    oldest = next(iter(memo))
    for number in range(80):
        cache_module._fragment_checked("canonical", "bundles", f"[{number}]")
        assert len(memo) <= 64
    assert len(memo) == 64
    assert oldest not in memo
    assert ("canonical:bundles", sha256_hex(b"[79]")) in memo
    assert ("canonical:bundles", sha256_hex(b"[0]")) not in memo
    # A fragment that fails is not remembered.
    calls = spy(monkeypatch)
    for attempt in (1, 2):
        before = list(memo)
        with pytest.raises(ValueError):
            cache_module._fragment_checked("canonical", "bundles", "[ 1]")
        assert len(calls) == attempt
        assert list(memo) == before


def test_concurrent_key_construction_agrees():
    material = first_material("scorer")
    expected = oracle_key(material)
    start = threading.Barrier(8)

    def build():
        start.wait()
        return [str(SupportCacheKey(material)) for _ in range(20)]

    with ThreadPoolExecutor(8) as pool:
        results = [f.result() for f in [pool.submit(build) for _ in range(8)]]
    assert all(digest == expected for digests in results for digest in digests)
    assert len(results) == 8
    assert len(cache_module._checked_fragments) == 3


def test_concurrent_construction_over_an_evicting_memo_agrees():
    materials = [m for _, m in real_materials()]
    changed = [
        edited(
            materials[0],
            lambda b, n=n: b["bundles"][0]["elements"][0]["span"].__setitem__(
                "end", 100 + n
            ),
        )
        for n in range(70)
    ]
    start = threading.Barrier(8)

    def build(offset):
        start.wait()
        return [
            (text, str(SupportCacheKey(text)))
            for text in (*changed[offset:], *changed[:offset], *materials)
        ]

    with ThreadPoolExecutor(8) as pool:
        results = [f.result() for f in [pool.submit(build, n * 8) for n in range(8)]]
    for pairs in results:
        for text, digest in pairs:
            assert digest == oracle_key(text)
    assert len(cache_module._checked_fragments) <= 64


@pytest.mark.parametrize(
    ("label", "material"), corpus(), ids=[label for label, _ in corpus()]
)
def test_every_mutation_gets_the_oracles_outcome_for_the_constructor(label, material):
    for warm in (False, True):
        forget_memos()
        if warm:
            warm_memos()
        expected = outcome(oracle_key, material)
        assert key_outcome(material) == expected
        if expected[0] == "ok":
            key = SupportCacheKey(material)
            assert key.material == material
            assert str(key) == expected[1]
            assert type(key) is SupportCacheKey


@pytest.mark.parametrize(
    ("label", "material"), corpus(), ids=[label for label, _ in corpus()]
)
def test_the_light_check_accepts_only_what_the_oracle_accepts(label, material):
    for level in ("canonical", "valid"):
        for warm in (False, True):
            forget_memos()
            if warm:
                warm_memos()
            parsed = cache_module._light_material(material, level)
            if parsed is None:
                continue
            expected = outcome(oracle_key, material)
            assert expected[0] == "ok", label
            assert sha256_hex(material.encode()) == expected[1]
            assert type(parsed) is dict
            assert all(parsed[name] == [] for name in NAMES)


def test_the_light_check_takes_the_real_materials_and_none_of_the_cut_ones():
    by_label = dict(corpus())
    for label, material in real_materials():
        assert cache_module._light_material(material, "canonical") is not None, label
    for kind in KINDS:
        # A marker text inside an escaped string is no marker: the key splits.
        escaped = by_label[f"{kind}-marker-text-in-escaped-document-string"]
        assert cache_module._light_material(escaped, "canonical") is not None
        # A marker, or an extra, dropped or duplicate key, inside a span cuts the
        # value short or holds two values: no check accepts it, and today's body
        # gives the outcome.
        for label in (
            "nested-claim-key-in-document",
            "nested-source-quotes-key-in-a-claim",
            "nested-source-run-key-in-a-quote",
            "extra-key-in-bundles-span",
            "extra-key-in-source-claims-span",
            "extra-key-in-source-quotes-span",
            "duplicate-key-bundles-first-empty",
            "duplicate-key-source-claims",
            "duplicate-key-source-quotes",
            "key-dropped-source-claims",
            "key-dropped-source-quotes",
            "key-dropped-source-run",
            "keys-swapped-source-claims-and-quotes",
        ):
            material = by_label[f"{kind}-{label}"]
            assert cache_module._light_material(material, "canonical") is None, label
            assert key_outcome(material) == outcome(oracle_key, material)


def test_markers_nested_in_the_rest_are_not_taken_for_the_big_values():
    """A nested key named as a marker, in a value that sorts before the top-level
    one, takes the split away from the top-level values. The top-level lists then
    stay in the rest, unchecked. No check accepts such a text: each marker must occur
    once in the rest."""
    material = edited(
        first_material("scorer"),
        lambda b: b["request"].__setitem__(
            "x", {"a": 0, "source_claims": [1], "source_quotes": [2], "source_run": 3}
        ),
    )
    assert material.count(',"source_claims":') == 2
    fragments, _ = cache_module._split_material(material)
    assert fragments[1:] == ("[1]", "[2]")
    for level in ("canonical", "valid"):
        assert cache_module._light_material(material, level) is None
    assert key_outcome(material) == outcome(oracle_key, material)


NESTED_PLACES = {
    # ``reply_schema`` of a judge request holds any JSON, so the oracle accepts it.
    ("judge", "reply_schema"): lambda body: body["request"]["reply_schema"],
    # No model has a free key here: the oracle accepts the key text and then refuses
    # the binding, and the two must agree.
    ("judge", "request"): lambda body: body["request"],
    ("scorer", "request"): lambda body: body["request"],
}


def nested_triple(kind, place, *, top_level):
    """The real material of ``kind`` with a nested ``source_claims``, ``source_quotes``
    and ``source_run`` key in ``place``, which sorts before the top-level ones. Each
    nested list holds the first real record. The top-level lists are the empty ones
    (``top_level="empty"``) or are dropped (``top_level="dropped"``)."""
    body = json.loads(first_material(kind))
    claim, quote = body["source_claims"][0], body["source_quotes"][0]
    for name in ("source_claims", "source_quotes"):
        if top_level == "empty":
            body[name] = []
        else:
            del body[name]
    NESTED_PLACES[kind, place](body)["x"] = {
        "a": 0,
        "source_claims": [claim],
        "source_quotes": [quote],
        "source_run": 3,
    }
    return canonical_json(body).decode(), claim, quote


@pytest.mark.parametrize("top_level", ["empty", "dropped"])
@pytest.mark.parametrize(("kind", "place"), list(NESTED_PLACES))
def test_nested_markers_before_the_top_level_ones_are_never_taken(
    kind, place, top_level
):
    """The split takes the nested text when no top-level list is there to stop it, and
    the parse of the rest would then hold ``[]`` where the key holds a record. Task 3
    builds the request and the identity from that parse. Each marker must occur once
    in the rest, and the top-level key must be there, or no check accepts the text."""
    material, claim, quote = nested_triple(kind, place, top_level=top_level)
    fragments, placeholder = cache_module._split_material(material)
    assert fragments[1] == canonical_json([claim]).decode()
    assert fragments[2] == canonical_json([quote]).decode()
    nested = json.loads(placeholder)["request"]
    nested = nested["reply_schema"] if place == "reply_schema" else nested
    assert nested["x"]["source_claims"] == []
    assert json.loads(material)["request"] != json.loads(placeholder)["request"]
    assert placeholder.count(',"source_claims":') == (2 if top_level == "empty" else 1)
    for level in ("canonical", "valid"):
        for warm in (False, True):
            forget_memos()
            if warm:
                warm_memos()
            assert cache_module._light_material(material, level) is None
    # Today's body gives today's outcome for the key, the binding and the kind.
    expected = outcome(oracle_key, material)
    assert expected[0] == "ok"
    for warm in (False, True):
        forget_memos()
        if warm:
            warm_memos()
        assert key_outcome(material) == expected
        text = expected[1]
        assert outcome(cache_module._material_kind, material) == outcome(
            oracle_kind, material
        )
        assert outcome(cache_module._validate_binding, text, material, kind) == outcome(
            oracle_binding, text, material, kind
        )
    if (kind, place) == ("judge", "reply_schema") and top_level == "empty":
        assert outcome(oracle_binding, expected[1], material, kind)[0] == "ok"


@pytest.mark.parametrize("name", NAMES)
def test_a_lone_surrogate_in_any_part_is_refused_as_today(name):
    material = first_material("judge")

    def change(body):
        if name == "bundles":
            body["bundles"][0]["document"]["canonical_text"] += SURROGATE
        elif name == "source_claims":
            body["source_claims"][0]["claim"] += SURROGATE
        else:
            body["source_quotes"][0]["span"]["suffix"] += SURROGATE

    body = json.loads(material)
    change(body)
    broken = dumped(body)
    rest = dumped({**json.loads(material), "claim": "a" + SURROGATE})
    expected = ("refused", "SupportError", "malformed_record")
    for text in (broken, rest):
        assert outcome(oracle_key, text) == expected
        for warm in (False, True):
            forget_memos()
            if warm:
                warm_memos()
            assert key_outcome(text) == expected
            assert cache_module._light_material(text, "canonical") is None


def test_a_valid_fragment_passes_only_when_every_record_does(monkeypatch):
    for _, material in real_materials():
        for level in ("canonical", "valid"):
            assert cache_module._light_material(material, level) is not None
        fragments, _ = cache_module._split_material(material)
        for name, fragment in zip(NAMES, fragments, strict=True):
            assert cache_module._check_fragment("valid", name, fragment) is None
            assert cache_module._check_fragment("canonical", name, fragment) is None
    # One bad record fails its list, and a failure is not remembered.
    material = first_material("scorer")
    bad = {
        "bundles": lambda b: b["bundles"][0]["elements"][0].__setitem__(
            "type", "invented"
        ),
        "source_claims": lambda b: b["source_claims"][0].__setitem__("claim_id", 7),
        "source_quotes": lambda b: b["source_quotes"][0].__setitem__("mask_ids", "m"),
    }
    memo = cache_module._checked_fragments
    forget_memos()
    calls = spy(monkeypatch)
    for name in NAMES:
        text = edited(material, bad[name])
        fragment = cache_module._split_material(text)[0][NAMES.index(name)]
        # The text is canonical, so the canonical level accepts it.
        cache_module._fragment_checked("canonical", name, fragment)
        before = list(memo)
        for attempt in (1, 2):
            with pytest.raises(ValueError):
                cache_module._fragment_checked("valid", name, fragment)
            assert list(memo) == before
        assert calls.count(("valid", name)) == 2
        assert cache_module._light_material(text, "valid") is None
        assert cache_module._light_material(text, "canonical") is not None
    # A fragment that is not a list, or not a canonical text, fails at each level.
    for text in ("{}", "5", "null", '"s"', "[]x", "[ ]", "[1,2", ""):
        for name in NAMES:
            with pytest.raises(ValueError):
                cache_module._check_fragment("valid", name, text)
    for name in NAMES:
        cache_module._check_fragment("canonical", name, "{}")
        with pytest.raises(ValueError):
            cache_module._check_fragment("canonical", name, "[ ]")
        with pytest.raises(ValueError):
            cache_module._check_fragment("canonical", name, "[1]x")


def test_a_valid_pass_under_one_name_is_not_a_pass_under_another():
    """The valid check depends on the name, so the memo key does too."""
    material = first_material("scorer")
    fragments, _ = cache_module._split_material(material)
    for name, fragment in zip(NAMES, fragments, strict=True):
        cache_module._fragment_checked("valid", name, fragment)
    for name in NAMES:
        for other, fragment in zip(NAMES, fragments, strict=True):
            if other != name and fragment != "[]":
                with pytest.raises(ValueError):
                    cache_module._fragment_checked("valid", name, fragment)
    # The same text passes at the canonical level under any name.
    for name in NAMES:
        for fragment in fragments:
            cache_module._fragment_checked("canonical", name, fragment)


def test_a_canonical_pass_is_not_a_valid_pass():
    material = first_material("scorer")
    body = json.loads(material)
    body["source_claims"][0]["claim_id"] = 7
    text = canonical_json(body).decode()
    fragments, _ = cache_module._split_material(text)
    cache_module._fragment_checked("canonical", "source_claims", fragments[1])
    with pytest.raises(ValueError):
        cache_module._fragment_checked("valid", "source_claims", fragments[1])


# --- Task 3: the binding and the kind ------------------------------------------------


def binding_outcome(material, kind, key_text=None):
    """``_validate_binding``'s outcome for ``material``, as ``outcome`` shapes it."""
    if key_text is None:
        key_text = sha256_hex(material.encode())
    return outcome(_validate_binding, key_text, material, kind)


def oracle_binding_outcome(material, kind, key_text=None):
    if key_text is None:
        key_text = sha256_hex(material.encode())
    return outcome(oracle_binding, key_text, material, kind)


def test_the_big_texts_are_validated_once_across_bindings(monkeypatch, tmp_path):
    keys = [(label.split("-")[1], SupportCacheKey(m)) for label, m in real_materials()]
    assert {kind for kind, _ in keys} == set(KINDS)
    calls = spy(monkeypatch)
    cache = SupportCache(tmp_path / "support-cache", "replay")
    for kind, key in keys:
        SupportCache._binding(key, kind)
        assert cache.raw_ref(key) == f"{key}.json"
    assert sorted(calls) == sorted(("valid", name) for name in NAMES)
    # A binding that its text does not memoize still finds each big value checked.
    for _ in range(2):
        for kind, key in keys:
            assert outcome(_validate_binding, str(key), key.material, kind)[0] == "ok"
    assert len(calls) == 3


def rest_broken(material):
    """Materials that keep the three big values and break the rest, labeled."""
    return [
        ("kind-invalid", edited(material, lambda b: b.__setitem__("kind", "x"))),
        ("extra-key", edited(material, lambda b: b.__setitem__("zzz", 1))),
        ("dropped-key", edited(material, lambda b: b.pop("policy"))),
        ("claim-blank", edited(material, lambda b: b.__setitem__("claim", "   "))),
        (
            "provenance-bad",
            edited(material, lambda b: b.__setitem__("provenance_hash", "A" * 64)),
        ),
    ]


@pytest.mark.parametrize("kind", KINDS)
def test_a_good_fragment_with_a_bad_rest_is_refused(monkeypatch, kind):
    material = first_material(kind)
    SupportCacheKey(material)
    assert binding_outcome(material, kind)[0] == "ok"
    memo = sorted(cache_module._checked_fragments)
    assert len(memo) == 6
    calls = spy(monkeypatch)
    expected_refused = ("refused", "SupportError", "malformed_record")
    base_fragments = cache_module._split_material(material)[0]
    broken = [
        *rest_broken(material),
        # The kind of the other valid kind: the request and identity are of this one.
        ("kind-other", edited(material, lambda b: b.__setitem__("kind", OTHER[kind]))),
    ]
    assert len(broken) == 6
    for label, text in broken:
        split = cache_module._split_material(text)
        # Each keeps the three big values; the rest is what is broken.
        assert split is not None and split[0] == base_fragments, label
        for asked in KINDS:
            got = binding_outcome(text, asked)
            assert got == oracle_binding_outcome(text, asked), (label, asked)
            if label != "kind-other" or asked == kind:
                assert got == expected_refused, (label, asked)
        assert sorted(cache_module._checked_fragments) == memo, label
    assert calls == []


@pytest.mark.parametrize("kind", KINDS)
def test_a_rest_that_does_not_split_is_refused_as_today(monkeypatch, kind):
    """A key sorted first, or a dropped ``claim``, takes today's body: no marker
    matches, so no fragment is looked at, and the outcome is today's."""
    material = first_material(kind)
    SupportCacheKey(material)
    calls = spy(monkeypatch)
    for text in (
        edited(material, lambda b: b.__setitem__("a", 1)),
        edited(material, lambda b: b.pop("claim")),
    ):
        assert cache_module._split_material(text) is None
        assert binding_outcome(text, kind) == oracle_binding_outcome(text, kind)
        assert binding_outcome(text, kind)[0] == "refused"
    assert calls == []


CHANGES = {
    # One character changes and the text stays canonical JSON. The oracle accepts the
    # claim record and refuses the other two, whose derived values no longer fit.
    "bundles": ("element end", one_character_changed("bundles"), "refused"),
    "source_claims": ("claim text", one_character_changed("source_claims"), "ok"),
    "source_quotes": ("quote start", one_character_changed("source_quotes"), "refused"),
}
INVALID = {
    "bundles": lambda b: b["bundles"][0]["elements"][0].__setitem__("type", "x"),
    "source_claims": lambda b: b["source_claims"][0].__setitem__("claim_id", 7),
    "source_quotes": lambda b: b["source_quotes"][0].__setitem__("mask_ids", "m"),
}


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("name", NAMES)
def test_a_changed_fragment_is_validated_anew_and_refused(monkeypatch, name, kind):
    material = first_material(kind)
    SupportCacheKey(material)
    assert binding_outcome(material, kind)[0] == "ok"
    calls = spy(monkeypatch)
    _, change, accepted = CHANGES[name]
    for change_name, how, expected_tag in (
        ("one character", change, accepted),
        ("an invalid record", INVALID[name], "refused"),
    ):
        calls.clear()
        changed = edited(material, how)
        assert changed != material, change_name
        expected = oracle_binding_outcome(changed, kind)
        assert expected[0] == expected_tag, change_name
        before = sorted(cache_module._checked_fragments)
        # Only the changed value is looked at again, and the others are memoized.
        assert binding_outcome(changed, kind) == expected
        assert calls == [("valid", name)], change_name
        if expected_tag == "refused":
            # A refused value is not remembered: it is validated in full each time,
            # and the refusal is today's.
            assert sorted(cache_module._checked_fragments) == before
            for attempt in (2, 3):
                assert binding_outcome(changed, kind) == expected
                assert calls == [("valid", name)] * attempt, change_name
        else:
            assert len(cache_module._checked_fragments) == len(before) + 1
            assert binding_outcome(changed, kind) == expected
            assert calls == [("valid", name)], change_name
    # The unchanged key keeps its answer.
    assert binding_outcome(material, kind) == oracle_binding_outcome(material, kind)


class RecordingJson:
    """A stand-in for ``json`` in ``cache.py`` that records each text it is asked to
    parse, by length, and keeps no text."""

    def __init__(self):
        self.sizes = []

    def loads(self, text, *args, **kwargs):
        self.sizes.append(len(text))
        return json.loads(text, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(json, name)


def big_materials():
    """A scorer's and a judge's key of one invented source, with a document of about
    280 KB. They share the three big values and differ in the rest, as the keys of one
    source do."""
    document = "Lumen opened a new line today. " * 9000
    scorer = _with_document_text(first_material("scorer"), document)
    judge = _with_document_text(first_material("judge"), document)
    assert len(scorer) > 250_000 and len(judge) > 250_000
    assert (
        cache_module._split_material(scorer)[0]
        == cache_module._split_material(judge)[0]
    )
    assert (
        cache_module._split_material(scorer)[1]
        != cache_module._split_material(judge)[1]
    )
    return scorer, judge


def test_the_kind_of_a_material_is_read_without_parsing_the_big_texts(monkeypatch):
    scorer, judge = big_materials()
    SupportCacheKey(scorer)
    recording = RecordingJson()
    monkeypatch.setattr(cache_module, "json", recording)
    # The second key of the source: its big values are known, so only the rest is parsed.
    assert _material_kind(judge) == "judge"
    assert recording.sizes and max(recording.sizes) < 100_000
    assert _material_kind(scorer) == "scorer"
    assert max(recording.sizes) < 100_000
    # A source that has not been seen parses its big values once, and once only.
    recording.sizes.clear()
    forget_memos()
    assert _material_kind(judge) == "judge"
    assert max(recording.sizes) > 250_000
    recording.sizes.clear()
    forget_memos()
    SupportCacheKey(judge)
    recording.sizes.clear()
    assert _material_kind(scorer) == "scorer"
    assert max(recording.sizes) < 100_000


def test_the_binding_of_a_second_key_is_read_without_parsing_the_big_texts(
    monkeypatch,
):
    scorer, judge = big_materials()
    SupportCacheKey(scorer)
    assert binding_outcome(scorer, "scorer") == oracle_binding_outcome(scorer, "scorer")
    assert binding_outcome(scorer, "scorer")[0] == "ok"
    expected = oracle_binding_outcome(judge, "judge")
    assert expected[0] == "ok"
    recording = RecordingJson()
    monkeypatch.setattr(cache_module, "json", recording)
    # The big values of the source are known: only the rest of the second key is parsed.
    assert binding_outcome(judge, "judge") == expected
    assert recording.sizes and max(recording.sizes) < 100_000


def test_the_fast_and_the_slow_path_share_one_body_of_checks(monkeypatch):
    calls = []
    real = cache_module._check_material

    def counting(material, kind, fragments_checked):
        calls.append((kind, fragments_checked))
        return real(material, kind, fragments_checked)

    monkeypatch.setattr(cache_module, "_check_material", counting)
    for label, material in real_materials():
        kind = label.split("-")[1]
        calls.clear()
        assert binding_outcome(material, kind) == oracle_binding_outcome(material, kind)
        assert calls == [(kind, True)], label
    # A key that does not split, with a nested marker, takes today's path whole.
    nested, _, _ = nested_triple("judge", "reply_schema", top_level="empty")
    calls.clear()
    key_text = sha256_hex(nested.encode())
    assert outcome(oracle_binding, key_text, nested, "judge")[0] == "ok"
    assert binding_outcome(nested, "judge") == oracle_binding_outcome(nested, "judge")
    assert calls == [("judge", False)]


def test_a_material_without_a_kind_is_read_as_today():
    material = first_material("scorer")
    SupportCacheKey(material)
    text = edited(material, lambda b: b.pop("kind"))
    for warm in (False, True):
        forget_memos()
        if warm:
            warm_memos()
        expected = outcome(oracle_kind, text)
        assert expected[0] == "refused" and expected[1] == "KeyError"
        assert outcome(_material_kind, text) == expected


@pytest.mark.parametrize(
    ("label", "material"), corpus(), ids=[label for label, _ in corpus()]
)
def test_a_warm_memo_never_changes_the_binding_or_the_kind(label, material):
    """The memo holds what the real materials passed. A text that differs from them,
    in the big values or in the rest, is judged as the oracle judges it, with the key
    text right or wrong and for each kind."""
    try:
        bytes_hash = sha256_hex(material.encode("utf-8", "surrogatepass"))
    except (AttributeError, TypeError):
        bytes_hash = sha256_hex(b"")
    wrong = [sha256_hex(b"other"), bytes_hash.upper(), bytes_hash[:-1], ""]
    for warm in (False, True):
        forget_memos()
        if warm:
            warm_memos()
        assert outcome(_material_kind, material) == outcome(oracle_kind, material)
        for kind in KINDS:
            for key_text in (bytes_hash, key_text_for(material), *wrong):
                assert outcome(_validate_binding, key_text, material, kind) == outcome(
                    oracle_binding, key_text, material, kind
                ), (kind, key_text)


def test_clearing_the_record_memo_also_clears_the_fragment_memo():
    """The shim of ``tests/conftest.py``: a test's own ``forget_memos`` clears the
    record memo mid-test, and the valid-level fragment memo is a record-check memo."""
    material = first_material("scorer")
    SupportCacheKey(material)
    assert binding_outcome(material, "scorer")[0] == "ok"
    assert {key[0] for key in cache_module._checked_fragments} >= {
        f"valid:{name}" for name in NAMES
    }
    assert cache_module._checked_records
    cache_module._checked_records.clear()
    assert len(cache_module._checked_records) == 0
    assert len(cache_module._checked_fragments) == 0
    # Only a clear is shimmed: the record memo is the same dict and still works.
    assert type(cache_module._checked_records) is OrderedDict
    assert binding_outcome(material, "scorer")[0] == "ok"
    assert cache_module._checked_records
