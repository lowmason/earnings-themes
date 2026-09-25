import json
import random

import httpx
import pytest
from discover import (
    Candidate,
    Discovery,
    IndexDocument,
    SubmissionFiling,
    older_pages_covering,
    parse_filing_index,
    parse_master_index,
    parse_submission_filings,
    pick_earnings_filing,
    pick_press_release,
    quarter_bounds,
    render_shortlist,
    sample_ciks,
    suggest,
)
from pf_fetch import EdgarFetcher, Throttle

MASTER_IDX = """Description:           Master Index of EDGAR Dissemination Feed
Last Data Received:    March 31, 2025

CIK|Company Name|Form Type|Date Filed|Filename
--------------------------------------------------------------------------------
320193|Apple Inc.|8-K|2025-01-30|edgar/data/320193/0000320193-25-000007.txt
320193|Apple Inc.|10-Q|2025-01-31|edgar/data/320193/0000320193-25-000008.txt
789019|MICROSOFT CORP|8-K|2025-01-29|edgar/data/789019/0001193125-25-012345.txt
1018724|AMAZON COM INC|8-K|2025-02-06|edgar/data/1018724/0001018724-25-000004.txt
"""

INDEX_PAGE = """<html><body>
<table class="tableFile" summary="Document Format Files">
<tr><th>Seq</th><th>Description</th><th>Document</th><th>Type</th><th>Size</th></tr>
<tr><td>1</td><td>8-K</td><td><a href="/ix?doc=/Archives/edgar/data/320193/000032019325000007/a8-k.htm">a8-k.htm</a> iXBRL</td><td>8-K</td><td>40000</td></tr>
<tr><td>2</td><td>PRESS RELEASE DATED JANUARY 30, 2025</td><td><a href="/Archives/edgar/data/320193/000032019325000007/a8-kex991q1.htm">a8-kex991q1.htm</a></td><td>EX-99.1</td><td>90000</td></tr>
<tr><td>3</td><td>DATA SUPPLEMENT</td><td><a href="/Archives/edgar/data/320193/000032019325000007/a8-kex992.htm">a8-kex992.htm</a></td><td>EX-99.2</td><td>9000</td></tr>
</table></body></html>"""


def recent_block(rows):
    return {
        "accessionNumber": [r[0] for r in rows],
        "form": [r[1] for r in rows],
        "filingDate": [r[2] for r in rows],
        "items": [r[3] for r in rows],
    }


def test_parse_master_index_skips_headers_and_pads_cik():
    rows = parse_master_index(MASTER_IDX)
    assert [r.form for r in rows] == ["8-K", "10-Q", "8-K", "8-K"]
    assert rows[0].cik == "0000320193"
    assert rows[2].accession == "0001193125-25-012345"
    assert rows[2].agent == "0001193125"


def test_sample_ciks_is_deterministic_distinct_and_only_8k():
    rows = parse_master_index(MASTER_IDX)
    first = sample_ciks(rows, count=5, rng=random.Random(1))
    again = sample_ciks(rows, count=5, rng=random.Random(1))
    assert first == again
    assert {r.form for r in first} == {"8-K"}
    assert len({r.cik for r in first}) == len(first) == 3


def test_quarter_bounds_end_on_the_last_day():
    assert quarter_bounds(2024, 1) == ("2024-01-01", "2024-03-31")
    assert quarter_bounds(2024, 4) == ("2024-10-01", "2024-12-31")


def test_pick_earnings_filing_needs_item_202_in_the_quarter():
    filings = parse_submission_filings(
        recent_block(
            [
                ("0000320193-25-000009", "8-K", "2025-02-20", "5.07"),
                ("0000320193-25-000007", "8-K", "2025-01-30", "2.02,9.01"),
                ("0000320193-25-000001", "8-K/A", "2025-01-10", "2.02"),
                ("0000320193-24-000090", "8-K", "2024-10-31", "2.02,9.01"),
            ]
        )
    )
    chosen = pick_earnings_filing(filings, 2025, 1)
    assert chosen == SubmissionFiling(
        "0000320193-25-000007", "8-K", "2025-01-30", "2.02,9.01"
    )
    assert pick_earnings_filing(filings, 2025, 2) is None


def test_older_pages_are_selected_by_date_overlap():
    document = {
        "filings": {
            "files": [
                {
                    "name": "CIK0000320193-submissions-001.json",
                    "filingFrom": "1994-01-26",
                    "filingTo": "2010-03-30",
                },
                {
                    "name": "CIK0000320193-submissions-002.json",
                    "filingFrom": "2010-03-31",
                    "filingTo": "2016-12-31",
                },
            ]
        }
    }
    assert older_pages_covering(document, 2010, 1) == [
        "CIK0000320193-submissions-001.json",
        "CIK0000320193-submissions-002.json",
    ]
    assert older_pages_covering(document, 2005, 3) == [
        "CIK0000320193-submissions-001.json"
    ]


def test_parse_filing_index_reads_types_descriptions_and_ixbrl_links():
    documents = parse_filing_index(INDEX_PAGE)
    assert [d.doc_type for d in documents] == ["8-K", "EX-99.1", "EX-99.2"]
    assert documents[0].filename == "a8-k.htm"
    assert documents[1].description == "PRESS RELEASE DATED JANUARY 30, 2025"


def test_pick_press_release_prefers_the_described_exhibit():
    chosen, reason = pick_press_release(parse_filing_index(INDEX_PAGE))
    assert reason == "ok" and chosen.doc_type == "EX-99.1"
    single = [IndexDocument("2", "EXHIBIT 99", "ex99.htm", "EX-99")]
    assert pick_press_release(single)[0].filename == "ex99.htm"
    ambiguous = [
        IndexDocument("2", "A", "a.htm", "EX-99.1"),
        IndexDocument("3", "B", "b.htm", "EX-99.2"),
    ]
    assert pick_press_release(ambiguous)[0] is None
    text_only = [IndexDocument("2", "PRESS RELEASE", "ex99.txt", "EX-99.1")]
    assert pick_press_release(text_only) == (None, "exhibit is not HTML (ex99.txt)")


def _candidate(fid, cik, agent, year, **tests):
    class_tests = {
        "narrative_only": False,
        "malformed_layout": False,
        "table_heavy": False,
        "clean_html": True,
    }
    class_tests.update(tests)
    class_tests["data_table_share"] = 0.6 if class_tests["table_heavy"] else 0.0
    class_tests.setdefault("visible_chars", 5000)
    return Candidate(
        fid,
        cik,
        "Issuer",
        "acc",
        agent,
        "8-K",
        "2.02",
        "2025-01-30",
        "EX-99.1",
        "x.htm",
        "",
        "u",
        year,
        1,
        True,
        class_tests,
    )


def test_suggest_caps_issuers_and_spreads_agents():
    pool = [
        _candidate("a", "c1", "g1", 2005, narrative_only=True),
        _candidate("b", "c1", "g1", 2008, narrative_only=True),
        _candidate("c", "c1", "g2", 2011, narrative_only=True),
        _candidate("d", "c2", "g2", 2014, narrative_only=True),
    ]
    picks = suggest(pool)["narrative_only"]
    assert len(picks) == 3
    assert sum(p.cik == "c1" for p in picks) == 2
    assert "## narrative_only (4 eligible)" in render_shortlist(pool)


def test_discovery_end_to_end_saves_one_candidate_and_reruns_without_requests(tmp_path):
    exhibit = b"<html><body><p>" + b"Revenue rose. " * 10 + b"</p></body></html>"
    routes = {
        "https://www.sec.gov/Archives/edgar/full-index/2025/QTR1/master.idx": (
            "text/plain",
            MASTER_IDX.encode(),
        ),
        "https://data.sec.gov/submissions/CIK0000320193.json": (
            "application/json",
            json.dumps(
                {
                    "filings": {
                        "recent": recent_block(
                            [("0000320193-25-000007", "8-K", "2025-01-30", "2.02,9.01")]
                        ),
                        "files": [],
                    }
                }
            ).encode(),
        ),
        "https://www.sec.gov/Archives/edgar/data/320193/000032019325000007/0000320193-25-000007-index.htm": (
            "text/html",
            INDEX_PAGE.encode(),
        ),
        "https://www.sec.gov/Archives/edgar/data/320193/000032019325000007/a8-kex991q1.htm": (
            "text/html",
            exhibit,
        ),
    }

    def handler(request):
        url = str(request.url)
        if url in routes:
            content_type, body = routes[url]
            return httpx.Response(
                200, headers={"Content-Type": content_type}, content=body
            )
        if "submissions" in url:
            return httpx.Response(
                200,
                headers={"Content-Type": "application/json"},
                content=json.dumps(
                    {"filings": {"recent": recent_block([]), "files": []}}
                ).encode(),
            )
        return httpx.Response(404)

    def fetcher():
        throttle = Throttle(min_interval=0.0)
        return EdgarFetcher(
            "Jane Doe research jane@example.org",
            throttle=throttle,
            transport=httpx.MockTransport(handler),
            sleep=lambda s: None,
        )

    first = fetcher()
    Discovery(first, root=tmp_path).run_year(2025, 1, per_year=1, rng=random.Random(3))
    lines = (tmp_path / "candidates.jsonl").read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["fixture_id"] == "0000320193-25-000007_ex-99-1"
    assert record["items"] == "2.02,9.01"
    assert record["class_tests"]["narrative_only"] is True
    assert (tmp_path / record["fixture_id"] / "source.html").read_bytes() == exhibit

    second = fetcher()
    Discovery(second, root=tmp_path).run_year(2025, 1, per_year=1, rng=random.Random(3))
    assert second.throttle.count == 0
    assert len((tmp_path / "candidates.jsonl").read_text().splitlines()) == 1


@pytest.mark.parametrize("years", [[2004], [2003, 2010]])
def test_run_refuses_years_before_item_202(years):
    from discover import main

    with pytest.raises(SystemExit):
        main(["run", "--live", "--years", *map(str, years)])


def test_image_only_exhibits_are_excluded_from_the_shortlist():
    pool = [
        _candidate("a", "c1", "g1", 2005, narrative_only=True, visible_chars=40),
        _candidate("b", "c2", "g2", 2008, narrative_only=True),
    ]
    assert [c.fixture_id for c in suggest(pool)["narrative_only"]] == ["b"]
    shortlist = render_shortlist(pool)
    assert "## narrative_only (1 eligible)" in shortlist
    assert "1 have under 500 characters of native text" in shortlist
