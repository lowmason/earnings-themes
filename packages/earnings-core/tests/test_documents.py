import pytest
from earnings_core.artifacts import ArtifactRef, RightsStatus
from earnings_core.documents import (
    CanonicalDocument,
    derive_doc_id,
    document_integrity_problem,
)
from earnings_core.hashing import hash_canonical_text
from pydantic import ValidationError

TEXT = "Acme reports third-quarter results.\nRevenue rose 5% to €2.1 billion."


def make_document(text: str = TEXT, **changes: object) -> CanonicalDocument:
    fields: dict[str, object] = {
        "source_document_id": "0000007332-09-000032_ex-99",
        "canonicalization_version": "walker-w16.norm-1",
        "canonical_text": text,
    }
    fields.update(changes)
    return CanonicalDocument.create(**fields)


def test_create_derives_the_hash_and_the_doc_id() -> None:
    document = make_document()
    assert document.canonical_hash == hash_canonical_text(TEXT)
    assert document.doc_id == (
        "0000007332-09-000032_ex-99@walker-w16.norm-1#" + hash_canonical_text(TEXT)[:16]
    )
    assert document_integrity_problem(document) is None


def test_changed_text_is_a_new_version() -> None:
    first = make_document()
    second = make_document(TEXT.replace("5%", "6%"))
    assert second.canonical_hash != first.canonical_hash
    assert second.doc_id != first.doc_id
    assert second.source_document_id == first.source_document_id


def test_text_cannot_be_mutated_in_place() -> None:
    document = make_document()
    with pytest.raises(ValidationError):
        document.canonical_text = "Revenue fell."


def test_new_text_under_an_old_doc_id_is_refused() -> None:
    first = make_document()
    changed = TEXT.replace("5%", "6%")
    with pytest.raises(ValidationError, match="is not the derived"):
        CanonicalDocument(
            doc_id=first.doc_id,
            source_document_id=first.source_document_id,
            canonicalization_version=first.canonicalization_version,
            canonical_text=changed,
            canonical_hash=hash_canonical_text(changed),
        )


def test_a_hash_that_is_not_the_texts_is_refused() -> None:
    first = make_document()
    with pytest.raises(ValidationError, match="is not the text's SHA-256"):
        CanonicalDocument(
            doc_id=first.doc_id,
            source_document_id=first.source_document_id,
            canonicalization_version=first.canonicalization_version,
            canonical_text=TEXT + " ",
            canonical_hash=first.canonical_hash,
        )


def test_a_copy_that_skips_validation_is_still_caught() -> None:
    tampered = make_document().model_copy(update={"canonical_text": "Revenue fell."})
    problem = document_integrity_problem(tampered)
    assert problem is not None
    assert "is not the text's SHA-256" in problem


@pytest.mark.parametrize("text", ["", "broken \ud800 text"], ids=["empty", "surrogate"])
def test_empty_or_unencodable_text_is_not_canonical(text: str) -> None:
    with pytest.raises(ValueError):
        make_document(text)


@pytest.mark.parametrize(
    "part", ["0000007332 09", "walker/w16", "a@b", "a#b", ""], ids=str
)
def test_id_parts_are_restricted_so_a_derived_id_reads_back(part: str) -> None:
    with pytest.raises(ValidationError):
        make_document(source_document_id=part)


def test_derive_doc_id_is_a_pure_function() -> None:
    digest = hash_canonical_text(TEXT)
    assert derive_doc_id("s", "v", digest) == derive_doc_id("s", "v", digest)
    assert derive_doc_id("s", "v", digest) == f"s@v#{digest[:16]}"


def test_a_text_artifact_must_hold_exactly_the_canonical_bytes() -> None:
    stored = ArtifactRef.for_bytes(
        TEXT.encode(),
        media_type="text/plain; charset=utf-8",
        storage_ref="data/canonical/example.txt",
        rights_status=RightsStatus.LOCAL_ONLY,
        rights_basis="docs/source-register.toml entry sec-edgar",
    )
    assert make_document(text_artifact=stored).text_artifact == stored
    stale = stored.model_copy(
        update={"content_sha256": hash_canonical_text(TEXT + ".")}
    )
    with pytest.raises(ValidationError, match="holds other bytes"):
        make_document(text_artifact=stale)


def test_a_document_round_trips_through_json() -> None:
    document = make_document()
    restored = CanonicalDocument.model_validate_json(document.model_dump_json())
    assert restored == document
    assert document_integrity_problem(restored) is None
