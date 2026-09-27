"""The evidence record and the freeze (the Stage 5 spec, §The event manifest; EV11,
P6-14), over the synthetic event layer and Stage 4's synthetic cohort.
"""

import shutil
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.events.build import EventBuild, build_events
from earnings_ingestion.events.evidence import check_evidence, evidence_of
from earnings_ingestion.events.freeze import (
    EventFreezeRefused,
    freeze_events,
    frozen_event_manifests,
    load_event_evidence,
    load_event_manifest,
    serialize,
)
from earnings_ingestion.events.layer import (
    ACME,
    CORVID,
    REPORTS,
    filings,
    review,
    write_layer,
)
from earnings_ingestion.events.pilot import freeze_pilot, frozen_pilots, select_pilot
from earnings_ingestion.events.records import (
    EventManifest,
    EventOverridesFile,
    content_hash,
    pilot_content_hash,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.synthetic import SyntheticStore
from earnings_ingestion.sec.urls import filing_index_url, submissions_url

ROOT = Path(__file__).resolve().parents[3]
COHORT = ROOT / "tests" / "fixtures" / "cohort" / "manifests" / "djia-synthetic-v1.json"
NOW = datetime(2026, 9, 28, 18, 0, tzinfo=UTC)
LATER = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def universe():
    return load_manifest(COHORT)


@pytest.fixture
def layer(tmp_path) -> SyntheticStore:
    return write_layer(tmp_path / "data" / "raw" / "events", tmp_path)


def build(universe, layer: SyntheticStore, overrides=()) -> EventBuild:
    return build_events(
        universe,
        SavedResponses(layer.store),
        EventOverridesFile(schema_version=1, overrides=overrides),
        corpus_id="djia-synthetic",
    )


def reviewed(universe, layer: SyntheticStore) -> EventBuild:
    return build(universe, layer, review(build(universe, layer)))


def freeze(built: EventBuild, layer: SyntheticStore, directory: Path):
    return freeze_events(built, SavedResponses(layer.store), directory, now=NOW)


def test_the_freeze_refuses_and_names_each_reason(universe, layer, tmp_path) -> None:
    directory = tmp_path / "corpus"
    with pytest.raises(EventFreezeRefused) as refused:
        freeze(build(universe, layer), layer, directory)
    reasons = refused.value.reasons
    assert [reason.split(": ")[0] for reason in reasons] == [
        "period_gap:cik-0009990002:2025-03-31:2026-07-01",
        "period_gap:cik-0009990003:2024-07-01:2024-12-31",
        "period_gap:cik-0009990006:2025-03-31:2025-09-30",
        "cik-0009990001:2025-02-28",
        "cik-0009990002:2024-09-30",
        "cik-0009990005:2025-06-27",
    ]
    assert reasons[3].endswith("several_release_filings, not retained")
    assert not directory.exists()


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ("drop", "cik-0009990005:2025-06-27: no_release_filing, not retained"),
        ("stale", "keep-eligible: a stale override"),
    ],
)
def test_an_unretained_row_or_a_stale_override_alone_holds_the_freeze(
    universe, layer, tmp_path, change, reason
) -> None:
    overrides = review(build(universe, layer))
    if change == "drop":
        overrides = tuple(
            o for o in overrides if o.override_id != "keep-dynamo-no-release"
        )
    else:
        (kept,) = [o for o in overrides if o.override_id == "keep-dynamo-no-release"]
        extra = kept.model_copy(
            update={
                "override_id": "keep-eligible",
                "event_id": "cik-0009990001:2024-08-31",
            }
        )
        overrides = (*overrides, extra)
    with pytest.raises(EventFreezeRefused) as refused:
        freeze(build(universe, layer, overrides), layer, tmp_path / "corpus")
    assert refused.value.reasons == (reason,)


def test_a_reviewed_build_freezes_with_evidence_that_verifies(
    universe, layer, tmp_path
) -> None:
    frozen = freeze(reviewed(universe, layer), layer, tmp_path / "corpus")
    assert frozen.created
    assert (frozen.path.name, frozen.evidence_path.name) == (
        "events-v1.json",
        "events-v1.evidence.json",
    )
    assert load_event_manifest(frozen.path) == frozen.manifest
    evidence = load_event_evidence(frozen.evidence_path, frozen.manifest)
    assert evidence.event_manifest_hash == frozen.manifest.definition.content_hash
    assert check_evidence(evidence, layer.store) == ()
    assert len(evidence.events) == 32
    assert [(f.convention, f.rows_cross_checked) for f in evidence.files][:2] == [
        (Convention.EASTERN_DIGITS, 9),
        (Convention.EASTERN_DIGITS, 5),
    ]
    assert len(evidence.files) == 6
    assert len(evidence.skipped_pages) == 1
    events = {cited.event_id: cited for cited in evidence.events}
    acme = events["cik-0009990001:2025-02-28"]
    (release,) = [f for f, _ in filings(ACME) if f.accepted == "2025-03-20 16:05:00"]
    assert acme.release.url == filing_index_url(ACME.cik, release.accession)
    assert acme.item_text is not None
    assert len(acme.candidates) == 2
    assert events["cik-0009990003:2025-06-30"].labels is None
    none = events["cik-0009990005:2025-06-27"]
    assert (none.release, none.item_text, none.cross_check) == (None, None, None)
    assert events["cik-0009990002:2024-09-30"].amendments[0].url.endswith("-index.htm")


def test_identical_content_is_the_same_version(universe, layer, tmp_path) -> None:
    built = reviewed(universe, layer)
    first = freeze(built, layer, tmp_path / "corpus")
    again = freeze(built, layer, tmp_path / "corpus")
    assert (again.created, again.path) == (False, first.path)
    assert len(list((tmp_path / "corpus").iterdir())) == 2


def test_a_refetch_with_the_same_facts_writes_nothing(
    universe, layer, tmp_path
) -> None:
    """Acme's submissions file, fetched again a day later in true UTC: the evidence
    would change, and the manifest does not (EV11)."""
    before = reviewed(universe, layer)
    frozen = freeze(before, layer, tmp_path / "corpus")
    again = SyntheticStore(layer.store.root, layer.store.repo, LATER)
    again.submissions(
        ACME.cik,
        ACME.name,
        [filing for filing, _ in filings(ACME)],
        convention=Convention.UTC,
    )
    after = build(universe, again, before.overrides)
    assert [f.resolved_by for f in after.findings if f.resolved_by]
    assert after.content_hash == before.content_hash
    evidence = evidence_of(after, frozen.manifest, SavedResponses(again.store))
    (acme,) = [f for f in evidence.files if f.url == submissions_url(ACME.cik)]
    assert (acme.convention, acme.retrieved_at) == (Convention.UTC, LATER)
    assert not freeze(after, again, tmp_path / "corpus").created
    assert len(list((tmp_path / "corpus").iterdir())) == 2


def test_a_changed_fact_writes_the_next_version(universe, layer, tmp_path) -> None:
    """Corvid's companyfacts, fetched again with agreeing labels, changes a row."""
    before = reviewed(universe, layer)
    first = freeze(before, layer, tmp_path / "corpus")
    again = SyntheticStore(layer.store.root, layer.store.repo, LATER)
    listed = filings(CORVID)
    facts = [
        (filing.accession, report.labels[0][0], report.labels[0][1])
        for filing, report in listed
        if report in REPORTS[CORVID]
    ]
    again.companyfacts(CORVID.cik, CORVID.name, facts)
    frozen = freeze(
        build(universe, again, before.overrides), again, tmp_path / "corpus"
    )
    assert frozen.created
    assert frozen.manifest.definition.event_manifest_version == 2
    rows = {row.event_id: row for row in frozen.manifest.rows}
    corvid = rows["cik-0009990003:2025-06-30"]
    assert (corvid.reported_fiscal_year, corvid.reported_fiscal_quarter) == (2025, "Q2")
    assert load_event_manifest(first.path) == first.manifest


def test_loading_rechecks_the_hash_and_the_name(universe, layer, tmp_path) -> None:
    frozen = freeze(reviewed(universe, layer), layer, tmp_path / "corpus")
    renamed = tmp_path / "events-v2.json"
    shutil.copy(frozen.path, renamed)
    with pytest.raises(ValueError, match="holds version 1"):
        load_event_manifest(renamed)
    changed = tmp_path / "events-v1.json"
    text = frozen.path.read_text().replace('"retained": true', '"retained": false', 1)
    changed.write_text(text)
    with pytest.raises(ValueError, match="does not hash"):
        load_event_manifest(changed)


@pytest.mark.parametrize(
    ("tamper", "message"),
    [
        ("corpus", "corpus_id other is not"),
        ("version", "event_manifest_version 2 is not"),
        ("other content", "event_manifest_hash"),
        ("truncated", "event_ids of its events"),
        ("swapped", "event_ids of its events"),
    ],
)
def test_loading_evidence_binds_it_to_its_manifest(
    universe, layer, tmp_path, tamper, message
) -> None:
    """Corvid's companyfacts, fetched again with agreeing labels, give a second v1 of
    the same corpus, with the same event IDs and other content (D8)."""
    before = reviewed(universe, layer)
    frozen = freeze(before, layer, tmp_path / "a")
    evidence = load_event_evidence(frozen.evidence_path, frozen.manifest)
    assert evidence.event_manifest_hash == frozen.manifest.definition.content_hash
    path = frozen.evidence_path
    if tamper == "other content":
        again = SyntheticStore(layer.store.root, layer.store.repo, LATER)
        facts = [
            (filing.accession, report.labels[0][0], report.labels[0][1])
            for filing, report in filings(CORVID)
            if report in REPORTS[CORVID]
        ]
        again.companyfacts(CORVID.cik, CORVID.name, facts)
        other = freeze(build(universe, again, before.overrides), again, tmp_path / "b")
        rows = [row.event_id for row in other.manifest.rows]
        assert other.path.name == frozen.path.name
        assert rows == [row.event_id for row in frozen.manifest.rows]
        path = other.evidence_path
    else:
        events = evidence.events
        update = {
            "corpus": {"corpus_id": "other"},
            "version": {"event_manifest_version": 2},
            "truncated": {"events": events[:-1]},
            "swapped": {"events": (events[1], events[0], *events[2:])},
        }[tamper]
        name = "events-v2.evidence.json" if tamper == "version" else path.name
        path = tmp_path / name
        path.write_bytes(serialize(evidence.model_copy(update=update)))
    with pytest.raises(ValueError, match=message):
        load_event_evidence(path, frozen.manifest)


def test_a_changed_interval_or_policy_changes_the_hash_and_a_version_alone_does_not(
    universe, layer
) -> None:
    """P-VF and P7-2: the universe's operative facts and the policies are hashed;
    its version is not."""
    built = reviewed(universe, layer)
    intervals = [
        interval.model_copy(update={"effective_from": date(2024, 11, 9)})
        if interval.security_id == "corvid-common"
        else interval
        for interval in universe.intervals
    ]
    moved = universe.model_copy(update={"intervals": tuple(intervals)})
    renumbered = universe.model_copy(
        update={
            "definition": universe.definition.model_copy(update={"universe_version": 2})
        }
    )
    overrides = built.overrides
    assert build(universe, layer, overrides).content_hash == built.content_hash
    assert build(renumbered, layer, overrides).content_hash == built.content_hash
    assert build(moved, layer, overrides).content_hash != built.content_hash
    manifest = built.manifest(1, NOW)
    policy = manifest.definition.model_copy(
        update={"discovery_policy_version": "release-id/2"}
    )
    assert content_hash(manifest.model_copy(update={"definition": policy})) != (
        manifest.definition.content_hash
    )


def of_corpus(manifest: EventManifest, corpus_id: str, version: int) -> EventManifest:
    """``manifest`` as another corpus's version, hashed as frozen."""
    moved = manifest.model_copy(
        update={
            "definition": manifest.definition.model_copy(
                update={"corpus_id": corpus_id, "event_manifest_version": version}
            )
        }
    )
    hashed = moved.definition.model_copy(update={"content_hash": content_hash(moved)})
    return moved.model_copy(update={"definition": hashed})


def test_the_freeze_refuses_a_build_of_another_corpus(
    universe, layer, tmp_path
) -> None:
    directory = tmp_path / "corpus"
    built = reviewed(universe, layer)
    freeze(built, layer, directory)
    other = build_events(
        universe,
        SavedResponses(layer.store),
        EventOverridesFile(schema_version=1, overrides=built.overrides),
        corpus_id="djia-other",
    )
    assert not other.holds_freeze
    with pytest.raises(ValueError, match="holds corpus djia-synthetic, not djia-other"):
        freeze(other, layer, directory)
    assert sorted(path.name for path in directory.iterdir()) == [
        "events-v1.evidence.json",
        "events-v1.json",
    ]


def test_a_directory_of_two_corpora_or_two_pilots_is_refused(
    universe, layer, tmp_path
) -> None:
    """Each frozen file names its version, not its corpus: the directory is the only
    tie, so the loaders refuse one that holds two. ``pilot_id`` is
    ``<corpus_id>-pilot``, whatever the policy, so a later policy's pilot shares it."""
    directory = tmp_path / "corpus"
    frozen = freeze(reviewed(universe, layer), layer, directory)
    pilot = freeze_pilot(
        select_pilot(frozen.manifest, universe), universe, directory, now=NOW
    )
    other = of_corpus(frozen.manifest, "djia-other", 2)
    (directory / "events-v2.json").write_bytes(serialize(other))
    with pytest.raises(ValueError, match=r"more than one corpus: \['djia-other', 'dj"):
        frozen_event_manifests(directory)
    with pytest.raises(ValueError, match="holds djia-synthetic-pilot, not djia-other"):
        freeze_pilot(select_pilot(other, universe), universe, directory, now=NOW)
    assert not (directory / "pilot-v2.json").exists()
    manifest = pilot.manifest
    renamed = manifest.definition.model_copy(
        update={"pilot_id": "djia-other-pilot", "pilot_version": 2}
    )
    stray = manifest.model_copy(update={"definition": renamed})
    hashed = renamed.model_copy(update={"content_hash": pilot_content_hash(stray)})
    stray = stray.model_copy(update={"definition": hashed})
    (directory / "pilot-v2.json").write_bytes(serialize(stray))
    with pytest.raises(ValueError, match=r"more than one pilot: \['djia-other-pilot'"):
        frozen_pilots(directory)
