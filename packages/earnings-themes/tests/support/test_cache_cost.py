"""Support-cache lookups check each immutable key text once (plan 23, Task 3).

A cache key carries its whole binding as canonical text, so a lookup used to parse
and validate the same 13 MB of records again for every call. These tests count the
module-level check bodies, `_validate_binding` and `_check_records`, and the bytes
read, over invented sources only (GS13). They also hold the other side: changed or
edited text is validated anew, and a refusal is never remembered as success.
"""

import json
from importlib import import_module
from pathlib import Path

import pytest
from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    TextSpan,
    canonical_json,
    digest,
    sha256_hex,
)
from earnings_themes.anchoring import Bundle
from earnings_themes.support import cache as cache_module
from earnings_themes.support.cache import SupportCache, SupportCacheKey
from earnings_themes.support.problems import SupportError

_coding = import_module("packages.earnings-themes.tests.coding.conftest")
_cases = import_module("packages.earnings-themes.tests.coding.cases")

coding_case = _coding.coding_case
coding_policy = _coding.coding_policy
classifier_identity = _coding.classifier_identity
assignment_case_factory = _coding.assignment_case_factory

_LIST_MODELS = {
    "evidence": "EvidenceReference",
    "contexts": "ContextReference",
    "source_claims": "Claim",
    "source_quotes": "Quote",
}


def forget_memos():
    """The memos are process-wide, and building a case fills them."""
    cache_module._binding_once.cache_clear()
    cache_module._material_kind.cache_clear()
    cache_module._checked_records.clear()


@pytest.fixture(autouse=True)
def fresh_memos():
    forget_memos()
    yield
    forget_memos()


def cache_directory(tmp_path, number=1):
    return tmp_path / f"assignments-{number}" / "support-cache"


def stored(directory):
    """Each written entry as ``(kind, material)``, in file-name order."""
    found = []
    for path in sorted(directory.glob("*.json")):
        body = json.loads(path.read_text(encoding="utf-8"))
        found.append((body["kind"], body["material"]))
    return found


def record_lists(material):
    """Every record list in one material, as ``(model name, list)`` pairs."""
    body = json.loads(material)
    lists = [(model, body[name]) for name, model in _LIST_MODELS.items()]
    for bundle in body["bundles"]:
        lists.append(("DocumentElement", bundle["elements"]))
        lists.append(("OverlayMask", bundle["masks"]))
    return lists


def spy(monkeypatch, name):
    """Count calls to a module-level body, called through the module's globals."""
    calls = []
    real = getattr(cache_module, name)

    def counting(*args):
        calls.append(args)
        return real(*args)

    monkeypatch.setattr(cache_module, name, counting)
    return calls


def changed_bundle(source_id):
    text = "Lumen added two presses and served many more orders."
    document = CanonicalDocument.create(
        source_document_id=source_id,
        canonicalization_version="invented-1",
        canonical_text=text,
    )
    element = DocumentElement.create(
        document, ElementType.PARAGRAPH, TextSpan(start=0, end=len(text))
    )
    return Bundle(source_id, document, (element,), ())


def test_a_lookup_validates_its_binding_once(
    assignment_case_factory, tmp_path, monkeypatch
):
    assignment_case_factory(documents=2)
    directory = cache_directory(tmp_path)
    kind, material = next(e for e in stored(directory) if e[0] == "judge")
    cache = SupportCache(directory, "replay")
    forget_memos()
    calls = spy(monkeypatch, "_validate_binding")
    key = SupportCacheKey(material)
    assert cache.lookup(key, kind) is not None
    assert len(calls) == 1
    assert cache.lookup(key, kind) is not None
    assert len(calls) == 1
    # An equal key built again from the same text is still the same binding.
    assert cache.lookup(SupportCacheKey(material), kind) is not None
    assert len(calls) == 1


def test_bundle_records_are_validated_once_across_keys(
    assignment_case_factory, tmp_path, monkeypatch
):
    assignment_case_factory(documents=2)
    directory = cache_directory(tmp_path)
    entries = stored(directory)
    assert {kind for kind, _ in entries} == {"scorer", "judge"}
    assert len(entries) > 2
    forget_memos()
    calls = spy(monkeypatch, "_check_records")
    cache = SupportCache(directory, "replay")
    for kind, material in entries:
        assert cache.lookup(SupportCacheKey(material), kind) is not None
    seen = [(model.__name__, digest(records)) for model, records in calls]
    expected = {
        (model, digest(records))
        for _, material in entries
        for model, records in record_lists(material)
    }
    occurrences = sum(len(record_lists(material)) for _, material in entries)
    assert len(seen) == len(set(seen)) == len(expected)
    assert set(seen) == expected
    assert len(seen) < occurrences


def test_artifact_hash_reads_each_entry_once(
    assignment_case_factory, tmp_path, monkeypatch
):
    assignment_case_factory()
    directory = cache_directory(tmp_path)
    name = min(p.name for p in directory.glob("*.json"))
    expected = sha256_hex((directory / name).read_bytes())
    cache = SupportCache(directory, "replay")
    reads = []
    real = Path.read_bytes

    def counting(self):
        if self.parent == directory:
            reads.append(self.name)
        return real(self)

    monkeypatch.setattr(Path, "read_bytes", counting)
    assert cache.artifact_hash(name) == expected
    assert reads == [name]


def test_changed_bundle_text_is_validated_and_refused(
    assignment_case_factory, tmp_path, monkeypatch
):
    assignment_case_factory(documents=2)
    assignment_case_factory(documents=2, bundle=changed_bundle("invented-first"))
    first, second = (stored(cache_directory(tmp_path, n)) for n in (1, 2))
    first_directory = cache_directory(tmp_path, 1)
    second_directory = cache_directory(tmp_path, 2)
    forget_memos()
    calls = spy(monkeypatch, "_check_records")

    def run(directory, entries):
        calls.clear()
        cache = SupportCache(directory, "replay")
        for kind, material in entries:
            assert cache.lookup(SupportCacheKey(material), kind) is not None
        return {(model.__name__, digest(records)) for model, records in calls}

    validated_first = run(first_directory, first)
    validated_second = run(second_directory, second)
    # Only the lists the changed source does not share with the first are validated.
    lists_first = {
        (model, digest(records))
        for _, material in first
        for model, records in record_lists(material)
    }
    lists_second = {
        (model, digest(records))
        for _, material in second
        for model, records in record_lists(material)
    }
    assert validated_first == lists_first
    assert validated_second == lists_second - lists_first
    first_elements = {
        digest(bundle["elements"])
        for _, material in first
        for bundle in json.loads(material)["bundles"]
    }
    second_elements = {
        digest(bundle["elements"])
        for _, material in second
        for bundle in json.loads(material)["bundles"]
    }
    changed = second_elements - first_elements
    assert len(changed) == 1
    assert ("DocumentElement", next(iter(changed))) in validated_second
    # The unchanged document's list is not validated again.
    for shared in first_elements & second_elements:
        assert ("DocumentElement", shared) not in validated_second

    # An edited key that follows a memoized valid one is refused every time.
    kind, material = first[0]
    edited = json.loads(material)
    edited["bundles"][0]["elements"][0]["type"] = "invented_type"
    key = SupportCacheKey(canonical_json(edited).decode())
    cache = SupportCache(first_directory, "replay")
    bindings = spy(monkeypatch, "_validate_binding")
    for attempt in (1, 2):
        with pytest.raises(SupportError, match="^malformed_record$"):
            cache.lookup(key, kind)
        assert len(bindings) == attempt
    # The valid key keeps working, and the edited document text is refused too.
    assert cache.lookup(SupportCacheKey(material), kind) is not None
    edited = json.loads(material)
    edited["bundles"][0]["document"]["canonical_text"] += " Edited."
    key = SupportCacheKey(canonical_json(edited).decode())
    with pytest.raises(SupportError, match="^malformed_record$"):
        cache.lookup(key, kind)


def test_a_refused_binding_is_never_remembered(
    assignment_case_factory, tmp_path, monkeypatch
):
    assignment_case_factory()
    directory = cache_directory(tmp_path)
    kind, material = stored(directory)[0]
    edited = json.loads(material)
    edited["claim"] = "   "
    key = SupportCacheKey(canonical_json(edited).decode())
    forget_memos()
    calls = spy(monkeypatch, "_validate_binding")
    for attempt in (1, 2, 3):
        with pytest.raises(SupportError, match="^malformed_record$"):
            SupportCache._binding(key, kind)
        assert len(calls) == attempt


def test_a_wrong_kind_is_refused_after_the_right_kind_was_remembered(
    assignment_case_factory, tmp_path
):
    assignment_case_factory()
    kind, material = stored(cache_directory(tmp_path))[0]
    other = "judge" if kind == "scorer" else "scorer"
    key = SupportCacheKey(material)
    SupportCache._binding(key, kind)
    with pytest.raises(SupportError, match="^malformed_record$"):
        SupportCache._binding(key, other)


def test_the_record_memo_holds_every_list_of_a_large_source(monkeypatch):
    """A source holds two lists per document, so a source of dozens of documents
    must not evict its own lists before the next key needs them."""
    lists = []
    for number in range(40):
        bundle = changed_bundle(f"invented-{number}")
        lists.append([e.model_dump(mode="json") for e in bundle.elements])
    calls = spy(monkeypatch, "_check_records")
    for _ in range(2):
        for records in lists:
            cache_module._check_records_once(DocumentElement, records)
    assert len(calls) == len({digest(r) for r in lists}) == 40


def test_a_returned_request_cannot_change_a_later_one(
    assignment_case_factory, tmp_path
):
    assignment_case_factory()
    directory = cache_directory(tmp_path)
    kind, material = next(e for e in stored(directory) if e[0] == "judge")
    key = SupportCacheKey(material)
    first, _ = SupportCache._binding(key, kind)
    original = json.loads(first.model_dump_json())
    first.reply_schema["invented"] = {"mutated": True}
    second, _ = SupportCache._binding(key, kind)
    assert second is not first
    assert json.loads(second.model_dump_json()) == original
    assert SupportCache(directory, "replay").lookup(key, kind) is not None
