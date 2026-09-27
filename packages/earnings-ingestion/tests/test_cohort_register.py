"""The membership source register loads strictly and versions what a manifest cites."""

from pathlib import Path

import pytest
from earnings_core import RightsStatus
from earnings_ingestion.cohort.records import EvidenceClass, SourceRole
from earnings_ingestion.cohort.register import SEC_RIGHTS, load_registers
from pydantic import ValidationError

ENTRY = """
[sources.{source_id}]
owner = "Synthetic Index Co."
url = "https://roster.example/djia"
access_method = "HTTPS GET of a fixed revision through the cohort web client."
cost = "Free."
license_terms = "Synthetic terms for tests."
terms_url = "https://roster.example/terms"
terms_sha256 = "{terms}"
redistribution_status = "Synthetic; redistributable."
coverage = "A synthetic roster."
expected_update_pattern = "Never updated."
known_limitations = ["Synthetic."]
last_verified = 2026-09-26
evidence_class = "secondary"
roles = ["anchor", "corroboration"]
rights_status = "redistributable"
rights_basis = "Synthetic test data."
"""
SEC = """
[sources.sec-edgar]
owner = "SEC"
last_verified = 2026-09-22
[sources.sec-edgar.access]
project_max_requests_per_second = 2
"""


def write(tmp_path: Path, *entries: str, sec: str = SEC) -> Path:
    (tmp_path / "docs").mkdir()
    body = "schema_version = 1\n" + "".join(entries)
    (tmp_path / "docs" / "membership-source-register.toml").write_text(body)
    (tmp_path / "docs" / "source-register.toml").write_text(sec)
    return tmp_path


def entry(source_id: str, terms: str = "a" * 64) -> str:
    return ENTRY.format(source_id=source_id, terms=terms)


def test_an_entry_gives_the_sources_class_roles_and_rights(tmp_path) -> None:
    registers = load_registers(write(tmp_path, entry("synthetic-roster")))
    found = registers.entry("synthetic-roster")
    assert found.evidence_class is EvidenceClass.SECONDARY
    assert found.roles == (SourceRole.ANCHOR, SourceRole.CORROBORATION)
    rights = registers.rights("synthetic-roster")
    assert rights.rights_status is RightsStatus.REDISTRIBUTABLE
    assert registers.rights("sec-edgar") == SEC_RIGHTS


def test_an_unregistered_source_is_refused(tmp_path) -> None:
    registers = load_registers(write(tmp_path, entry("synthetic-roster")))
    with pytest.raises(ValueError, match="not in the membership source register"):
        registers.entry("elsewhere")


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ('evidence_class = "secondary"', 'evidence_class = "unknown"'),
        ('cost = "Free."', 'cost = "Free."\nquote = "Copied text."'),
        ('terms_sha256 = "' + "a" * 64 + '"', 'terms_sha256 = "abc"'),
    ],
    ids=["unknown-class", "extra-field", "short-hash"],
)
def test_a_malformed_entry_is_refused(tmp_path, old, new) -> None:
    with pytest.raises(ValidationError):
        load_registers(write(tmp_path, entry("synthetic-roster").replace(old, new)))


def test_only_a_user_supplied_list_may_omit_its_terms(tmp_path) -> None:
    terms = f'terms_url = "https://roster.example/terms"\nterms_sha256 = "{"a" * 64}"\n'
    bare = entry("synthetic-roster").replace(terms, "")
    with pytest.raises(ValidationError, match="records its terms"):
        load_registers(write(tmp_path, bare))
    user = bare.replace(
        'evidence_class = "secondary"', 'evidence_class = "user_supplied"'
    )
    user = user.replace('roles = ["anchor", "corroboration"]', 'roles = ["check"]')
    (tmp_path / "docs" / "membership-source-register.toml").write_text(
        "schema_version = 1\n" + user
    )
    assert load_registers(tmp_path).entry("synthetic-roster").terms_url is None


def test_the_release_register_must_hold_sec_edgar(tmp_path) -> None:
    with pytest.raises(ValueError, match="no sec-edgar entry"):
        load_registers(write(tmp_path, entry("synthetic-roster"), sec="[sources]\n"))


def test_the_version_changes_only_with_a_cited_entry(tmp_path) -> None:
    root = write(tmp_path, entry("synthetic-roster"), entry("other-roster"))
    before = load_registers(root).version(["synthetic-roster", "sec-edgar"])
    path = root / "docs" / "membership-source-register.toml"
    path.write_text(
        "schema_version = 1\n"
        + entry("synthetic-roster")
        + entry("other-roster", terms="b" * 64)
    )
    assert load_registers(root).version(["synthetic-roster"]) == before
    path.write_text(
        "schema_version = 1\n"
        + entry("synthetic-roster", terms="b" * 64)
        + entry("other-roster")
    )
    assert load_registers(root).version(["synthetic-roster"]) != before
