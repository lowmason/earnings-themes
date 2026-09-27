"""The universe's operative identity (plan 7, EV4): evidence that decides no event
leaves it unchanged, and every fact an event's eligibility reads changes it."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import RightsStatus, sha256_hex
from earnings_ingestion.cohort.build import EPOCH, build
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.identity import operative_hash, operative_projection
from earnings_ingestion.cohort.synthetic import FIXTURE_DIR, build_options
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.urls import submissions_url

ROOT = Path(__file__).resolve().parents[3]
V1 = ROOT / "config" / "universe" / "djia" / "manifests" / "djia-2024q3-2026q2-v1.json"
SYNTHETIC = ROOT / FIXTURE_DIR / "manifests" / "djia-synthetic-v1.json"
OPTIONS = build_options()


def hashes(repo: Path) -> tuple[str, str]:
    """The build's content hash and operative hash."""
    built = build(repo, **OPTIONS)
    return built.content_hash, operative_hash(built.manifest(1, EPOCH))


def edit(repo: Path, name: str, old: str, new: str) -> None:
    path = repo / FIXTURE_DIR / name
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, old
    path.write_text(text.replace(old, new), encoding="utf-8")


def change_block(repo: Path, evidence_id: str) -> str:
    """The ``[[changes]]`` table for ``evidence_id``, with its entries."""
    text = (repo / FIXTURE_DIR / "evidence.toml").read_text(encoding="utf-8")
    start = text.index(f'[[changes]]\nevidence_id = "{evidence_id}"')
    ends = [text.find(marker, start + 1) for marker in ("[[changes]]", "[[checks]]")]
    return text[start : min(end for end in ends if end != -1)]


@pytest.fixture
def repo(cohort_repo: Path) -> Path:
    return cohort_repo


def test_a_withheld_notice_changes_the_content_but_not_the_identity(repo) -> None:
    """The notice of 2026-09-25 was published after the cutoff. It names Fenwick,
    whose unresolved mapping has no interval, so it decides no event."""
    before = hashes(repo)
    edit(repo, "evidence.toml", change_block(repo, "index-2026-09-25"), "")
    after = hashes(repo)
    assert after[0] != before[0]
    assert after[1] == before[1]


def test_a_refetched_sec_record_changes_the_content_but_not_the_identity(
    repo,
) -> None:
    before = hashes(repo)
    store = ArtifactStore(repo / FIXTURE_DIR / "raw", repo)
    url = submissions_url(9990001)
    old = store.latest(
        "sec-edgar",
        url,
        rights_status=RightsStatus.REDISTRIBUTABLE,
        rights_basis="synthetic",
    )
    body = json.dumps(json.loads(old.body), indent=1).encode()
    retrieval = Retrieval(
        request_url=url,
        final_url=url,
        retrieved_at=datetime(2026, 9, 28, 12, 0, tzinfo=UTC),
        retrieval_method=RetrievalMethod.HTTP,
        http_status=200,
        media_type="application/json",
        content_type="application/json",
        byte_count=len(body),
        sha256=sha256_hex(body),
    )
    store.put(
        "sec-edgar",
        body,
        retrieval,
        rights_status=RightsStatus.REDISTRIBUTABLE,
        rights_basis="synthetic",
    )
    after = hashes(repo)
    assert after[0] != before[0]
    assert after[1] == before[1]


def test_a_register_edit_changes_the_content_but_not_the_identity(repo) -> None:
    """Plan 7 edits the sec-edgar entry, as the spec asks: the source register's
    version is in the content hash, never in the identity (P7-3)."""
    before = hashes(repo)
    edit(repo, "source-register.toml", 'owner = "Synthetic SEC"', 'owner = "SEC"')
    after = hashes(repo)
    assert after[0] != before[0]
    assert after[1] == before[1]


def test_a_moved_bound_changes_both(repo) -> None:
    before = hashes(repo)
    edit(
        repo, "evidence.toml", "effective_on = 2026-06-22", "effective_on = 2026-06-23"
    )
    after = hashes(repo)
    assert after[0] != before[0]
    assert after[1] != before[1]


def test_a_changed_mapping_changes_both(repo) -> None:
    before = hashes(repo)
    edit(repo, "overrides.toml", 'cik = "0009990006"', 'cik = "0009990007"')
    after = hashes(repo)
    assert after[0] != before[0]
    assert after[1] != before[1]


def test_a_changed_action_changes_both(repo) -> None:
    """The projection holds no assertion, but each interval is reconstructed from
    its assertions' actions and lists them by IDs that end in the action, so the
    actions eligibility reads are in the identity."""
    before = hashes(repo)
    edit(
        repo,
        "evidence.toml",
        'action = "removed"\nsecurity_id = "borealis-common"',
        'action = "added"\nsecurity_id = "borealis-common"',
    )
    after = hashes(repo)
    assert after[0] != before[0]
    assert after[1] != before[1]


def test_each_interval_names_its_assertions_actions() -> None:
    """``eligibility.span`` splits an interval's assertions by action; each ID it
    looks up ends in the action it finds, in v1 and in the synthetic cohort."""
    for manifest in (load_manifest(V1), load_manifest(SYNTHETIC)):
        actions = {
            a.membership_assertion_id: a.asserted_action for a in manifest.assertions
        }
        for interval in manifest.intervals:
            for assertion_id in interval.assertion_ids:
                assert assertion_id.endswith(f":{actions[assertion_id]}")


def test_a_new_supporting_assertion_changes_both(repo) -> None:
    """A second notice restating the change of 2024-11-01 merges into its intervals,
    which then rest on one more assertion."""
    before = hashes(repo)
    block = change_block(repo, "index-2024-11-01")
    restated = block.replace(
        'evidence_id = "index-2024-11-01"', 'evidence_id = "index-2024-11-01-restated"'
    )
    edit(repo, "evidence.toml", "[[checks]]", f"{restated}[[checks]]")
    after = hashes(repo)
    assert after[0] != before[0]
    assert after[1] != before[1]


def test_the_projection_holds_only_the_cutoff_admissible_facts() -> None:
    manifest = load_manifest(SYNTHETIC)
    projection = operative_projection(manifest)
    assert sorted(projection) == [
        "candidate_issuer_ids",
        "definition",
        "intervals",
        "issuers",
        "mappings",
    ]
    assert sorted(projection["definition"]) == [
        "membership_reference",
        "period_end_start",
        "period_end_stop",
        "public_information_cutoff",
        "selection_policy_version",
        "universe_id",
        "universe_name",
    ]
    assert "fenwick-common" not in {m["security_id"] for m in projection["mappings"]}


def test_v1_loads_unchanged_and_has_an_operative_hash() -> None:
    v1 = load_manifest(V1)
    assert v1.definition.content_hash == (
        "2d9743945dc5748fccec4c4963f6fa891a41e8863d56e99841569ff25fa884b4"
    )
    assert operative_hash(v1) == (
        "c350923422d9bf2e65a0b5929f4c0d45370458c6a044c3de012a1dfeb116e573"
    )
    assert operative_hash(load_manifest(SYNTHETIC)) == (
        "57dcc2eb3d5f98e38717c54f9e2dc5419beca02f15fda04d2cb384d93358ae5c"
    )
