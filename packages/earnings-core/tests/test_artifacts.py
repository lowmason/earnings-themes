import pytest
from earnings_core.artifacts import ArtifactRef, RightsStatus
from earnings_core.hashing import sha256_hex
from pydantic import ValidationError

BASIS = "docs/source-register.toml entry sec-edgar"


def make_ref(**changes: object) -> ArtifactRef:
    fields: dict[str, object] = {
        "content_sha256": sha256_hex(b"<html></html>"),
        "media_type": "text/html",
        "storage_ref": "data/raw/example/source.html",
        "rights_status": RightsStatus.LOCAL_ONLY,
        "rights_basis": BASIS,
    }
    fields.update(changes)
    return ArtifactRef(**fields)


def test_for_bytes_records_the_sha256_of_the_content() -> None:
    data = "Revenue rose 5% to €2.1 billion.".encode()
    ref = ArtifactRef.for_bytes(
        data,
        media_type="text/plain; charset=utf-8",
        storage_ref="data/canonical/example.txt",
        rights_status=RightsStatus.REDISTRIBUTABLE,
        rights_basis=BASIS,
    )
    assert ref.content_sha256 == sha256_hex(data)
    assert ref.matches(data)


def test_a_one_byte_change_no_longer_matches() -> None:
    ref = make_ref()
    assert ref.matches(b"<html></html>")
    assert not ref.matches(b"<html> </html>")


@pytest.mark.parametrize(
    "digest",
    ["A" * 64, "a" * 63, "g" * 64, "sha256:" + "a" * 64],
    ids=["uppercase", "short", "not-hex", "prefixed"],
)
def test_a_digest_must_be_64_lowercase_hex_characters(digest: str) -> None:
    with pytest.raises(ValidationError):
        make_ref(content_sha256=digest)


@pytest.mark.parametrize(
    "storage_ref",
    [
        "/Users/someone/data/raw/x.html",
        "~/data/x.html",
        "file:///tmp/x.html",
        "a\\b",
        "FILE:///Users/someone/x.html",
        "File:/tmp/x.html",
        "C:/Users/someone/x.html",
        "c:x.html",
        "../outside/x.html",
        "data/raw/../../outside.html",
        "data/raw/..",
    ],
    ids=[
        "absolute",
        "home",
        "file-uri",
        "backslash",
        "file-uri-upper-case",
        "file-uri-mixed-case",
        "drive-letter",
        "drive-relative",
        "leading-dot-dot",
        "inner-dot-dot",
        "trailing-dot-dot",
    ],
)
def test_storage_ref_must_be_portable(storage_ref: str) -> None:
    with pytest.raises(ValidationError, match="repository-relative"):
        make_ref(storage_ref=storage_ref)


@pytest.mark.parametrize(
    "storage_ref",
    [
        "data/raw/example/source.html",
        "s3://bucket/raw/source.html",
        "https://www.sec.gov/Archives/edgar/data/7332/exhibit991.htm",
        "data/..hidden/x.html",
    ],
    ids=["relative-path", "s3-uri", "https-uri", "dot-dot-prefix-in-a-name"],
)
def test_portable_storage_refs_are_accepted(storage_ref: str) -> None:
    assert make_ref(storage_ref=storage_ref).storage_ref == storage_ref


@pytest.mark.parametrize(
    "media_type", ["html", "Text/HTML", "text/html;charset"], ids=str
)
def test_media_type_must_be_well_formed(media_type: str) -> None:
    with pytest.raises(ValidationError):
        make_ref(media_type=media_type)


def test_rights_basis_may_not_be_blank() -> None:
    with pytest.raises(ValidationError):
        make_ref(rights_basis="   ")


def test_rights_status_takes_the_enum_in_python_and_its_value_in_json() -> None:
    with pytest.raises(ValidationError):
        make_ref(rights_status="local_only")
    ref = make_ref(rights_status=RightsStatus.RESTRICTED)
    assert '"rights_status":"restricted"' in ref.model_dump_json()
    assert ArtifactRef.model_validate_json(ref.model_dump_json()) == ref


@pytest.mark.parametrize("version", [1, 3], ids=["schema-1", "schema-3"])
def test_another_schema_version_is_refused(version: int) -> None:
    payload = (
        make_ref()
        .model_dump_json()
        .replace('"schema_version":2', f'"schema_version":{version}')
    )
    with pytest.raises(ValidationError):
        ArtifactRef.model_validate_json(payload)
