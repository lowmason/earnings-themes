from dataclasses import dataclass

import httpx
import pytest
from pf_fetch import LivePolicyStop, Throttle
from v1_return_types import (
    PATHS,
    conclusion,
    declared,
    describe,
    install_transport_throttle,
    render,
)


class Sample:
    def method(self) -> "dict[str, int]":
        return {}

    @property
    def prop(self) -> "list[str]":
        return []

    def bare(self):
        return None

    def __init__(self, data: "pa.Table") -> None:  # noqa: F821 - a string annotation, as in edgartools
        self.data = data


@dataclass
class Record:
    frame: "pd.DataFrame"  # noqa: F821


def test_declared_reads_annotations_as_written():
    assert declared(Sample, "method") == "dict[str, int]"
    assert declared(Sample, "prop") == "list[str]"
    assert declared(Sample, "bare") == "(none)"
    assert declared(Sample, "data") == "__init__ parameter: pa.Table"
    assert declared(Record, "frame") == "attribute: pd.DataFrame"


def test_describe_flags_foreign_dataframes_in_containers():
    class FakeFrame:
        pass

    FakeFrame.__module__ = "pandas.core.frame"
    assert describe([FakeFrame()])["foreign_dataframe"] is True
    assert describe({"a": 1}) == {
        "observed": "builtins.dict",
        "elements": ["builtins.int"],
        "foreign_dataframe": False,
    }


def test_conclusion_names_every_foreign_path_or_says_vacuous():
    records = [
        {"call": "b", "foreign_dataframe": True},
        {"call": "a", "foreign_dataframe": True},
        {"call": "c", "foreign_dataframe": False},
    ]
    assert conclusion(records) == "R14.5 cast required for: a; b"
    assert (
        conclusion([{"call": "c", "foreign_dataframe": False}])
        == "R14.5 vacuous: no path returns a foreign dataframe."
    )


def test_render_collapses_identical_rows_and_reports_requests():
    record = {
        "fixture_id": "f",
        "family": "a",
        "call": "x()",
        "declared": "int",
        "observed": "builtins.int",
        "elements": [],
        "foreign_dataframe": False,
    }
    text = render([record, dict(record, fixture_id="g")], requests=7)
    assert text.count("`x()`") == 1 and "Live requests made: 7." in text


def test_paths_cover_all_three_families():
    assert {spec.family for spec in PATHS} == {"a", "b", "c"}


def test_transport_throttle_counts_and_caps_requests(monkeypatch):
    monkeypatch.setattr(
        httpx.HTTPTransport, "handle_request", lambda self, request: httpx.Response(200)
    )
    monkeypatch.setattr(
        httpx.AsyncHTTPTransport,
        "handle_async_request",
        httpx.AsyncHTTPTransport.handle_async_request,
    )
    throttle = Throttle(min_interval=0.0, max_requests=2)
    install_transport_throttle(throttle)
    transport = httpx.HTTPTransport()
    request = httpx.Request("GET", "https://www.sec.gov/x")
    transport.handle_request(request)
    transport.handle_request(request)
    assert throttle.count == 2
    with pytest.raises(LivePolicyStop):
        transport.handle_request(request)
