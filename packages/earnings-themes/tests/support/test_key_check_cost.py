"""The key check reads each big constant text of one source once (plan 24, Task 2).

A support-cache key holds three values that are the same in every key of one source:
``bundles``, ``source_claims`` and ``source_quotes``. The constructor splits the text
at their fixed canonical markers, checks each of them once per SHA-256 of its text,
and parses only the small rest. These tests count the module-level bodies, over the
invented ``assessed_case`` materials of Task 1's corpus (GS13). They also hold the
other side: the fast path only accepts, and any text that is changed, that does not
split, or that splits inside a value takes today's path and gets today's outcome.
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from earnings_core import canonical_json, sha256_hex
from earnings_themes.support import cache as cache_module
from earnings_themes.support.cache import SupportCacheKey

from .test_key_check_equivalence import (
    KINDS,
    SURROGATE,
    corpus,
    forget_memos,
    oracle_key,
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
    one, would take the split away from the top-level values. The top-level lists
    would then stay in the rest, unchecked. No check accepts such a text."""
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
