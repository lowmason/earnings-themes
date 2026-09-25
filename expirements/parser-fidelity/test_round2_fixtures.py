import pytest
import tomllib
from discover import Candidate
from round2_fixtures import (
    render_approval,
    round2_pool,
    round2_selection,
    short_classes,
)


def _candidate(fid, cik, agent, year, exhibit="EX-99.1", **tests):
    class_tests = {
        "narrative_only": False,
        "malformed_layout": False,
        "table_heavy": False,
        "clean_html": False,
        "visible_chars": 5000,
    }
    class_tests.update(tests)
    return Candidate(
        fid,
        cik,
        f"Issuer {cik}",
        "acc",
        agent,
        "8-K",
        "2.02",
        "2025-01-30",
        exhibit,
        "x.htm",
        "",
        "u",
        year,
        1,
        True,
        class_tests,
    )


def test_pool_drops_excluded_releases_and_every_release_from_their_issuers():
    pool = [
        _candidate("a", "c1", "g1", 2005, clean_html=True),
        _candidate("b", "c1", "g2", 2008, clean_html=True),
        _candidate("c", "c2", "g3", 2011, clean_html=True),
    ]
    assert [c.fixture_id for c in round2_pool(pool, {"a"})] == ["c"]


def test_pool_matches_issuers_on_cik_not_on_the_filer_agent():
    pool = [
        _candidate("a", "c1", "g1", 2005, clean_html=True),
        _candidate("b", "c2", "g1", 2008, clean_html=True),
    ]
    assert [c.fixture_id for c in round2_pool(pool, {"a"})] == ["b"]


def test_an_excluded_release_missing_from_the_candidates_is_an_error():
    with pytest.raises(ValueError, match="zzz"):
        round2_pool([_candidate("a", "c1", "g1", 2005, clean_html=True)], {"zzz"})


def test_first_two_picks_are_the_fixtures_and_the_third_is_the_spare():
    pool = [
        _candidate(f"n{i}", f"c{i}", f"g{i}", 2004 + i, narrative_only=True)
        for i in range(1, 5)
    ]
    fixtures, spares = round2_selection(pool, set())["narrative_only"]
    assert [c.fixture_id for c in fixtures] == ["n1", "n2"]
    assert [c.fixture_id for c in spares] == ["n3"]


def _full_pool():
    pool = []
    for n, cls in enumerate(
        ("clean_html", "malformed_layout", "table_heavy", "narrative_only")
    ):
        pool += [
            _candidate(f"{cls}-{i}", f"c{n}{i}", f"g{n}{i}", 2005 + i, **{cls: True})
            for i in range(3)
        ]
    return pool


def test_a_class_with_fewer_than_two_picks_is_short():
    pool = [
        c
        for c in _full_pool()
        if c.fixture_id not in {"table_heavy-0", "table_heavy-1"}
    ]
    assert short_classes(round2_selection(pool, set())) == ["table_heavy"]
    assert short_classes(round2_selection(_full_pool(), set())) == []


def test_the_rendered_approval_lists_the_fixtures_the_devset_and_the_spares():
    pool = _full_pool() + [_candidate("dev-1", "d1", "h1", 2012, clean_html=True)]
    selection = round2_selection(pool, {"dev-1"})
    text = render_approval(selection, [pool[-1]], approved_on="2026-09-24")
    approval = tomllib.loads(text)
    assert approval["approved_by"] == ""
    assert approval["short_classes"] == []
    assert [(e["fixture_id"], e["primary_class"]) for e in approval["fixtures"]] == [
        (fixture.fixture_id, cls)
        for cls in ("clean_html", "malformed_layout", "table_heavy", "narrative_only")
        for fixture in selection[cls][0]
    ]
    assert [e["fixture_id"] for e in approval["devset"]] == ["dev-1"]
    for cls in ("clean_html", "malformed_layout", "table_heavy", "narrative_only"):
        spare = selection[cls][1][0].fixture_id
        assert f'# spare, {cls}: "{spare}"' in text
