"""The event build (the Stage 5 spec, §Slots through §Review overrides; plan 7,
P7-15 and P7-16), over the synthetic event layer and Stage 4's synthetic cohort.
"""

from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.records import OverrideCitation
from earnings_ingestion.events.build import (
    EPOCH,
    EventBuild,
    EventBuildError,
    build_events,
)
from earnings_ingestion.events.layer import (
    ACME,
    BOREALIS,
    DYNAMO,
    RETRIEVED,
    Registrant,
    Report,
    filings,
    review,
    write_layer,
)
from earnings_ingestion.events.records import (
    EventOverride,
    EventOverrideKind,
    EventOverridesFile,
    EventReason,
    EventStatus,
    IdentificationMethod,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.synthetic import (
    JSON,
    SyntheticFiling,
    SyntheticStore,
    companyfacts_file,
    save,
    submissions_file,
)
from earnings_ingestion.sec.urls import (
    archive_url,
    companyfacts_url,
    filing_index_url,
    submissions_url,
)

ROOT = Path(__file__).resolve().parents[3]
COHORT = ROOT / "tests" / "fixtures" / "cohort" / "manifests" / "djia-synthetic-v1.json"
SIGNED = {
    "rationale": "Read in review.",
    "reviewer": "Synthetic Reviewer",
    "recorded_on": date(2026, 9, 28),
}
GAPS = (
    "period_gap:cik-0009990002:2025-03-31:2026-07-01",
    "period_gap:cik-0009990003:2024-07-01:2024-12-31",
    "period_gap:cik-0009990006:2025-03-31:2025-09-30",
)
ACME_SET = "cik-0009990001:2025-02-28"
BOREALIS_SAME_DAY = "cik-0009990002:2024-09-30"
DYNAMO_NONE = "cik-0009990005:2025-06-27"
DYNAMO_ID = "cik-0009990005"


@pytest.fixture(scope="module")
def universe():
    return load_manifest(COHORT)


@pytest.fixture(scope="module")
def layer(tmp_path_factory) -> SyntheticStore:
    repo = tmp_path_factory.mktemp("repo")
    return write_layer(repo / "data" / "raw" / "events", repo)


def run(universe, layer: SyntheticStore, *overrides: EventOverride) -> EventBuild:
    return build_events(
        universe,
        SavedResponses(layer.store),
        EventOverridesFile(schema_version=1, overrides=overrides),
        corpus_id="djia-synthetic",
    )


def accession(registrant: Registrant, accepted: str) -> str:
    (filing,) = [f for f, _ in filings(registrant) if f.accepted == accepted]
    return filing.accession


def acknowledge(override_id: str, finding_id: str, digest: str) -> EventOverride:
    return EventOverride(
        override_id=override_id,
        kind=EventOverrideKind.ACKNOWLEDGE,
        finding_id=finding_id,
        finding_digest=digest,
        **SIGNED,
    )


def retain(override_id: str, event_id: str, reason: EventReason) -> EventOverride:
    return EventOverride(
        override_id=override_id,
        kind=EventOverrideKind.RETAIN_UNRESOLVED,
        event_id=event_id,
        reason=reason,
        **SIGNED,
    )


def choose(
    layer: SyntheticStore, event_id: str, registrant: Registrant, accepted: str
) -> EventOverride:
    """Set a filing as the event's release, citing its index page's Accepted value."""
    number = accession(registrant, accepted)
    url = filing_index_url(registrant.cik, number)
    artifact = SavedResponses(layer.store).get(url)
    return EventOverride(
        override_id=f"release-{event_id.replace(':', '-')}",
        kind=EventOverrideKind.SET_RELEASE_FILING,
        event_id=event_id,
        accession=number,
        citations=(
            OverrideCitation(
                source_id="sec-edgar",
                url=url,
                artifact_sha256=artifact.artifact.content_sha256,
                locator=artifact.text.find(accepted),
            ),
        ),
        **SIGNED,
    )


def test_the_layer_builds_its_rows_with_what_holds_the_freeze(universe, layer) -> None:
    built = run(universe, layer)
    assert len(built.rows) == 32
    assert [f.finding_id for f in built.blocking] == list(GAPS)
    assert [row.event_id for row in built.unretained] == [
        ACME_SET,
        BOREALIS_SAME_DAY,
        DYNAMO_NONE,
    ]
    assert built.stale_overrides == ()
    assert built.holds_freeze
    statuses = [row.eligibility_status for row in built.rows]
    assert statuses.count(EventStatus.ELIGIBLE) == 26


def test_the_reviewed_overrides_settle_everything(universe, layer) -> None:
    built = run(universe, layer, *review(run(universe, layer)))
    assert not built.holds_freeze
    eligible = [r for r in built.rows if r.eligibility_status is EventStatus.ELIGIBLE]
    assert len(eligible) == 27
    assert len({row.issuer_id for row in eligible}) == 4
    rows = {row.event_id: row for row in built.rows}
    acme = rows[ACME_SET]
    assert acme.release_accession == accession(ACME, "2025-03-20 16:05:00")
    assert acme.identification_method is IdentificationMethod.OVERRIDE
    assert acme.override_ids == ("release-acme-2025-02-28",)
    assert acme.first_publication_time == datetime(2025, 3, 20, 20, 5, tzinfo=UTC)
    assert len(acme.candidate_accessions) == 2
    same_day = rows[BOREALIS_SAME_DAY]
    assert (same_day.retained, same_day.eligibility_reason) == (
        True,
        EventReason.SAME_DAY_TRANSITION,
    )
    assert (
        same_day.membership_assertion_id == "index-2024-11-01:borealis-common:removed"
    )
    assert rows[DYNAMO_NONE].override_ids == ("keep-dynamo-no-release",)
    assert [f.resolved_by for f in built.findings if f.finding_id in GAPS] == [
        ("gap-borealis",),
        ("gap-corvid",),
        ("gap-eastfield",),
    ]


def test_record_fields_stay_separate_and_unknown_labels_stay_null(
    universe, layer
) -> None:
    """R1.5 and P-A5: the period end, the labels, and the two times are separate
    fields; Corvid's disagreeing labels stay null, and its release is still read."""
    rows = {row.event_id: row for row in run(universe, layer).rows}
    corvid = rows["cik-0009990003:2025-06-30"]
    assert (corvid.reported_fiscal_year, corvid.reported_fiscal_quarter) == (None, None)
    assert corvid.identification_method is IdentificationMethod.SOLE_CANDIDATE
    acme = rows["cik-0009990001:2024-08-31"]
    assert (acme.period_end, acme.reported_fiscal_year) == (date(2024, 8, 31), 2025)
    assert acme.reported_fiscal_quarter == "Q1"
    assert acme.filing_acceptance_time == datetime(2024, 9, 26, 20, 5, tzinfo=UTC)
    assert acme.first_publication_time == acme.filing_acceptance_time


@pytest.mark.parametrize(
    ("year", "period"),
    [(2025, ""), (2025, "   "), (0, "Q3")],
    ids=["blank-period", "whitespace-period", "zero-year"],
)
def test_a_blank_label_stays_null_with_its_finding(
    universe, tmp_path, year, period
) -> None:
    """EV6: companyfacts' facts of Acme's report for 2025-02-28 agree on a blank
    ``fp``, or on an ``fy`` of 0. That states no label: the row's labels stay null,
    with a non-blocking ``fiscal_labels_unknown``, and the build does not fail."""
    layer = write_layer(tmp_path / "data" / "raw" / "events", tmp_path)
    report = accession(ACME, "2025-04-08 16:10:00")
    stated = [
        (filing.accession, *((year, period) if filing.accession == report else label))
        for filing, entry in filings(ACME)
        if isinstance(entry, Report)
        for label in entry.labels
    ]
    body = companyfacts_file(ACME.cik, ACME.name, stated)
    save(layer.store, companyfacts_url(ACME.cik), body, JSON, RETRIEVED.replace(day=29))
    built = run(universe, layer)
    row = {row.event_id: row for row in built.rows}[ACME_SET]
    assert (row.reported_fiscal_year, row.reported_fiscal_quarter) == (None, None)
    (finding,) = [
        f for f in built.findings if f.finding_id == f"fiscal_labels_unknown:{ACME_SET}"
    ]
    assert not finding.holds_freeze
    assert finding.detail == (
        f"companyfacts' facts of {report} disagree on fy and fp, or leave one out"
    )


def test_two_securities_make_one_row_per_period(universe, layer) -> None:
    rows = [row for row in run(universe, layer).rows if row.issuer_id == DYNAMO_ID]
    assert len(rows) == len({row.period_end for row in rows}) == 7


def test_a_changed_finding_makes_its_acknowledgement_stale(universe, layer) -> None:
    built = run(universe, layer, acknowledge("gap-old", GAPS[2], "0" * 64))
    assert built.stale_overrides == ("gap-old",)
    assert GAPS[2] in [f.finding_id for f in built.blocking]
    assert "gap-old: stale, and holds the freeze" in built.report()


@pytest.mark.parametrize(
    ("event_id", "reason"),
    [
        ("cik-0009990001:2024-08-31", EventReason.SEVERAL_RELEASE_FILINGS),
        (DYNAMO_NONE, EventReason.SEVERAL_RELEASE_FILINGS),
    ],
    ids=["eligible-event", "another-reason"],
)
def test_a_retain_that_no_longer_matches_its_event_is_stale(
    universe, layer, event_id, reason
) -> None:
    built = run(universe, layer, retain("keep", event_id, reason))
    assert built.stale_overrides == ("keep",)
    assert not {row.event_id: row for row in built.rows}[event_id].retained


def test_a_set_release_filing_decides_eligibility_again(universe, layer) -> None:
    """The 8-K/A accepted after Borealis left makes the event ineligible; the
    release itself, set by review, stays a same-day case that needs retaining."""
    amended = choose(layer, BOREALIS_SAME_DAY, BOREALIS, "2024-11-12 09:00:00")
    row = {r.event_id: r for r in run(universe, layer, amended).rows}[BOREALIS_SAME_DAY]
    assert row.eligibility_reason is EventReason.NOT_MEMBER_AT_PUBLICATION
    assert row.identification_method is IdentificationMethod.OVERRIDE
    confirmed = choose(layer, BOREALIS_SAME_DAY, BOREALIS, "2024-11-08 07:00:00")
    kept = retain("keep", BOREALIS_SAME_DAY, EventReason.SAME_DAY_TRANSITION)
    row = {r.event_id: r for r in run(universe, layer, confirmed, kept).rows}[
        BOREALIS_SAME_DAY
    ]
    assert row.retained
    assert row.override_ids == ("keep", "release-cik-0009990002-2024-09-30")


def refused(universe, layer, *overrides) -> tuple[str, ...]:
    with pytest.raises(EventBuildError) as raised:
        run(universe, layer, *overrides)
    return raised.value.problems


def test_overrides_that_name_nothing_are_refused(universe, layer) -> None:
    labels = "fiscal_labels_unknown:cik-0009990003:2025-06-30"
    digest = {f.finding_id: f.digest for f in run(universe, layer).findings}[labels]
    problems = refused(
        universe,
        layer,
        retain("keep", "cik-0009990001:2024-09-30", EventReason.NO_RELEASE_FILING),
        acknowledge(
            "gap-none", "period_gap:cik-0009990001:2024-07-01:2024-08-31", "0" * 64
        ),
        acknowledge("labels", labels, digest),
    )
    assert problems == (
        "keep: no event cik-0009990001:2024-09-30",
        "gap-none: no finding period_gap:cik-0009990001:2024-07-01:2024-08-31",
        "labels: a fiscal_labels_unknown finding is never acknowledged",
    )


def test_a_set_release_filing_must_name_a_saved_8_k_of_the_issuer(
    universe, layer
) -> None:
    good = choose(layer, ACME_SET, ACME, "2025-03-20 16:05:00")
    report = accession(ACME, "2025-04-08 16:10:00")
    regulation_fd = accession(DYNAMO, "2025-07-22 06:45:00")
    cases = [
        good.model_copy(update={"accession": "0009990001-25-999999"}),
        good.model_copy(update={"accession": report}),
        good.model_copy(update={"event_id": DYNAMO_NONE, "accession": regulation_fd}),
    ]
    problems = [refused(universe, layer, case)[0] for case in cases]
    who = "release-cik-0009990001-2025-02-28"
    assert problems == [
        f"{who}: the issuer's read filings list no 0009990001-25-999999",
        f"{who}: {report} is a 10-Q, not an 8-K or 8-K/A",
        (
            f"{who}: no index page of {regulation_fd} is saved: run events"
            f" discover --filing 0009990005 {regulation_fd}"
        ),
    ]


def test_a_set_release_filing_must_cite_the_filing_verifiably(universe, layer) -> None:
    good = choose(layer, ACME_SET, ACME, "2025-03-20 16:05:00")
    (citation,) = good.citations
    elsewhere = citation.model_copy(
        update={
            "url": archive_url(ACME.cik, accession(ACME, "2025-03-11 08:00:00"), "")
        }
    )
    changed = citation.model_copy(
        update={
            "locator": citation.locator.model_copy(update={"cited_sha256": "0" * 64})
        }
    )
    folder = archive_url(ACME.cik, good.accession, "")
    assert refused(
        universe, layer, good.model_copy(update={"citations": (elsewhere,)})
    ) == (f"release-cik-0009990001-2025-02-28: no citation is in {folder}",)
    assert refused(
        universe, layer, good.model_copy(update={"citations": (changed,)})
    ) == (
        (
            "release-cik-0009990001-2025-02-28: the cited content no longer hashes"
            " to cited_sha256"
        ),
    )


def test_a_citation_in_the_folder_must_be_a_saved_sec_artifact_with_a_locator(
    universe, layer
) -> None:
    """A citation grounds a set_release_filing only as an SEC artifact retrieved from
    its own URL in the filing's folder, at a locator that verifies. A URL alone,
    another source, no locator, or another URL's artifact verifies nothing."""
    good = choose(layer, ACME_SET, ACME, "2025-03-20 16:05:00")
    (citation,) = good.citations
    ((filing, _),) = [
        (f, e) for f, e in filings(ACME) if f.accepted == "2025-03-20 16:05:00"
    ]
    document = archive_url(ACME.cik, good.accession, filing.primary_document)
    cases = [
        citation.model_copy(update={"artifact_sha256": None, "locator": None}),
        citation.model_copy(update={"source_id": "synthetic-index"}),
        citation.model_copy(update={"locator": None}),
        citation.model_copy(update={"url": document}),
    ]
    folder = archive_url(ACME.cik, good.accession, "")
    expected = (
        (
            f"release-cik-0009990001-2025-02-28: no citation in {folder} is a saved"
            " SEC artifact, retrieved from its URL, with a locator"
        ),
    )
    for case in cases:
        override = good.model_copy(update={"citations": (case,)})
        assert refused(universe, layer, override) == expected, case


def test_a_filing_accepted_after_the_cutoff_is_refused(universe, tmp_path) -> None:
    """P-C4. The layer saves no index page for Acme's late release; this test saves
    one, so that the cutoff itself refuses it."""
    layer = write_layer(tmp_path / "data" / "raw" / "events", tmp_path)
    ((late, _),) = [
        (f, e) for f, e in filings(ACME) if f.accepted == "2026-09-24 16:05:00"
    ]
    layer.index(ACME.cik, late, (("Earnings release", "late.htm", "EX-99.1"),))
    override = choose(layer, "cik-0009990001:2026-05-31", ACME, late.accepted)
    assert refused(universe, layer, override) == (
        (
            f"release-cik-0009990001-2026-05-31: {late.accession} was accepted on"
            " 2026-09-24, after the cutoff 2026-09-22 (P-C4)"
        ),
    )


def test_a_missing_response_stops_the_build(universe, tmp_path) -> None:
    empty = SyntheticStore(tmp_path / "data" / "raw" / "events", tmp_path, EPOCH)
    problems = refused(universe, empty)
    assert len(problems) == 10
    submissions = "https://data.sec.gov/submissions/CIK0009990001.json"
    facts = "https://data.sec.gov/api/xbrl/companyfacts/CIK0009990001.json"
    assert problems[:2] == (
        f"nothing saved from {submissions}: run events discover",
        f"nothing saved from {facts}: run events discover",
    )


def resave_submissions(
    layer: SyntheticStore, registrant: Registrant, *extra: SyntheticFiling
) -> None:
    """Save, a day later, the registrant's submissions file with ``extra`` rows."""
    listed = [filing for filing, _ in filings(registrant)]
    body = submissions_file(
        registrant.cik,
        registrant.name,
        [*listed, *extra],
        convention=registrant.convention,
    )
    later = RETRIEVED.replace(day=29)
    save(layer.store, submissions_url(registrant.cik), body, JSON, later)


def test_a_filing_listed_twice_stops_the_build(universe, tmp_path) -> None:
    """Two copies of Acme's release for 2024-08-31 would be two candidates, and so a
    false several_release_filings; the repeat is refused instead."""
    layer = write_layer(tmp_path / "data" / "raw" / "events", tmp_path)
    (twice,) = [f for f, _ in filings(ACME) if f.accepted == "2024-09-26 16:05:00"]
    resave_submissions(layer, ACME, twice)
    (problem,) = refused(universe, layer)
    assert problem.startswith(f"{twice.accession} is listed 2 times: at /filings/")


def test_a_filing_two_issuers_list_changes_nothing(universe, tmp_path) -> None:
    """The repeat check is per issuer: a schedule listed under Acme and Borealis
    alike leaves the build as it was."""
    layer = write_layer(tmp_path / "data" / "raw" / "events", tmp_path)
    before = run(universe, layer).content_hash
    schedule = SyntheticFiling(
        accession="0009990002-25-000900",
        form="SC 13G",
        filing_date=date(2025, 2, 10),
        accepted="2025-02-10 10:00:00",
    )
    resave_submissions(layer, ACME, schedule)
    resave_submissions(layer, BOREALIS, schedule)
    assert run(universe, layer).content_hash == before


def test_a_companyfacts_file_of_another_registrant_stops_the_build(
    universe, tmp_path
) -> None:
    """Each companyfacts file states its CIK. One saved under Acme's URL but naming
    Borealis would label Acme's events with Borealis' facts, so it is refused."""
    layer = write_layer(tmp_path / "data" / "raw" / "events", tmp_path)
    url = companyfacts_url(ACME.cik)
    body = companyfacts_file(BOREALIS.cik, BOREALIS.name, [])
    save(layer.store, url, body, JSON, RETRIEVED.replace(day=29))
    assert refused(universe, layer) == (
        f"{url} is the companyfacts file of CIK {BOREALIS.cik}",
    )


def test_the_report_prints_each_candidate_s_reading(universe, layer) -> None:
    report = run(universe, layer).report()
    start = report.index(
        "cik-0009990005:2024-12-31  eligible  member_at_publication"
        f"  {accession(DYNAMO, '2025-02-11 06:45:00')} (stated_period)"
    )
    assert report[start + 1] == (
        f"  candidate {accession(DYNAMO, '2025-01-13 08:00:00')} accepted"
        " 2025-01-13 13:00 UTC: dates -; periods Q4 2024; preliminary yes;"
        " it calls its results preliminary"
    )
    assert report[start + 2].endswith("periods FY 2024; preliminary no; kept")
    assert f"{GAPS[0]} [blocks]: " in "\n".join(report)


def test_the_content_hash_leaves_out_the_version_and_time(universe, layer) -> None:
    built = run(universe, layer)
    later = built.manifest(2, datetime(2026, 9, 29, tzinfo=UTC))
    assert later.definition.content_hash == built.content_hash
    assert run(universe, layer).content_hash == built.content_hash
    assert later.definition.discovery_policy_version == "release-id/1"
    assert later.definition.eligibility_policy_version == "eligibility/1"
