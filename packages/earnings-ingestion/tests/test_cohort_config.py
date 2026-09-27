"""The curated cohort files load strictly: facts and citations, nothing else."""

from datetime import date

import pytest
from earnings_ingestion.cohort.config import load_cohort_config
from earnings_ingestion.cohort.records import BoundTiming, OverrideKind
from pydantic import ValidationError

UNIVERSE = """
universe_id = "djia-test"
universe_name = "djia"
period_end_start = 2024-07-01
period_end_stop = 2026-07-01
public_information_cutoff = 2026-09-22
membership_reference = "first_publication_time"
selection_policy_version = "djia-pilot/1"
expected_member_count = 2

[etf_proxy]
source_id = "synthetic-fund"
cik = "0009990009"
"""
H = "a" * 64
EVIDENCE = f"""
schema_version = 1

[[snapshots]]
evidence_id = "anchor"
source_id = "synthetic-roster"
role = "anchor"
url = "https://roster.example/djia?rev=1"
artifact_sha256 = "{H}"
canonical_sha256 = "{H}"
as_of = 2024-06-28
published_on = 2024-06-20

  [[snapshots.members]]
  security_id = "acme-common"
  name = "Acme Industrial"
  ticker = "ACME"
  span = [10, 25]
  cited_sha256 = "{H}"

[[changes]]
evidence_id = "change-1"
source_id = "synthetic-index"
url = "https://index.example/news/1"
artifact_sha256 = "{H}"
canonical_sha256 = "{H}"
announced_on = 2024-11-01
published_on = 2024-11-01
published_at = 2024-11-01T21:15:00Z
effective_on = 2024-11-08
timing = "before_open"
date_span = [40, 90]
date_cited_sha256 = "{H}"

  [[changes.entries]]
  action = "added"
  security_id = "corvid-common"
  name = "Corvid Systems"
  ticker = "CRVD"
  span = [5, 19]
  cited_sha256 = "{H}"

[[checks]]
evidence_id = "user-list"
source_id = "user-list"
as_of = 2026-09-22
published_on = 2026-09-26
members = [{{ name = "Acme Industrial", ticker = "ACME" }}]
"""
OVERRIDES = f"""
schema_version = 1

[[overrides]]
override_id = "acme-issuer"
kind = "set_issuer"
security_id = "acme-common"
cik = "0009990001"
rationale = "Reviewed."
reviewer = "Reviewer Name"
recorded_on = 2026-09-28
effective_from = 2024-07-01
citations = [{{ source_id = "sec-edgar", url = "https://data.sec.gov/x.json", artifact_sha256 = "{H}" }}]
"""


def write(tmp_path, evidence=EVIDENCE, overrides=OVERRIDES):
    (tmp_path / "universe.toml").write_text(UNIVERSE)
    (tmp_path / "evidence.toml").write_text(evidence)
    if overrides is not None:
        (tmp_path / "overrides.toml").write_text(overrides)
    return tmp_path


def test_the_curated_files_load_into_strict_models(tmp_path) -> None:
    config = load_cohort_config(write(tmp_path))
    assert config.universe.etf_proxy.forms == ("NPORT-P", "NPORT-P/A")
    (anchor,) = config.evidence.snapshots
    assert (anchor.as_of, anchor.members[0].span) == (date(2024, 6, 28), (10, 25))
    (change,) = config.evidence.changes
    assert change.timing is BoundTiming.BEFORE_OPEN
    assert change.published_at.utcoffset().total_seconds() == 0
    (override,) = config.overrides.overrides
    assert override.kind is OverrideKind.SET_ISSUER


def test_overrides_are_optional(tmp_path) -> None:
    assert load_cohort_config(write(tmp_path, overrides=None)).overrides.overrides == ()


ALIAS = """
[[overrides]]
override_id = "{override_id}"
kind = "holding_alias"
security_id = "{security_id}"
holding_name = "Acme Industrial Corp"
citations = []
rationale = "Reviewed."
reviewer = "Reviewer Name"
recorded_on = 2026-09-28
effective_from = 2024-07-01
"""


@pytest.mark.parametrize(
    "second", ["corvid-common", "acme-common"], ids=["conflicting", "agreeing"]
)
def test_a_holding_name_takes_one_alias(tmp_path, second) -> None:
    first = ALIAS.format(override_id="alias-1", security_id="acme-common")
    config = load_cohort_config(write(tmp_path, overrides=OVERRIDES + first))
    assert config.overrides.overrides[-1].kind is OverrideKind.HOLDING_ALIAS
    both = first + ALIAS.format(override_id="alias-2", security_id=second)
    with pytest.raises(ValidationError, match="holding_name repeated"):
        load_cohort_config(write(tmp_path, overrides=OVERRIDES + both))


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('evidence_id = "change-1"', 'evidence_id = "anchor"', "repeated"),
        ("span = [10, 25]", "span = [25, 10]", "empty or reversed"),
        ('ticker = "ACME"\n  span', 'ticker = "ACME"\n  quote = "x"\n  span', "Extra"),
        ('timing = "before_open"', 'timing = "at_noon"', "timing"),
        ("as_of = 2024-06-28", 'as_of = "June 28"', "as_of"),
    ],
    ids=["repeated-id", "reversed-span", "wording", "unknown-timing", "not-a-date"],
)
def test_a_malformed_evidence_file_is_refused(tmp_path, old, new, message) -> None:
    assert old in EVIDENCE
    with pytest.raises(ValidationError, match=message):
        load_cohort_config(write(tmp_path, evidence=EVIDENCE.replace(old, new)))


def test_two_anchors_are_refused(tmp_path) -> None:
    second = EVIDENCE.split("[[changes]]")[0].replace(
        '"anchor"\nsource', '"anchor-2"\nsource'
    )
    evidence = EVIDENCE + second.replace("schema_version = 1\n", "")
    with pytest.raises(ValidationError, match="at most one snapshot"):
        load_cohort_config(write(tmp_path, evidence=evidence))
