"""Coding diagnostics on invented sentinel data remain fixed and private."""

import copy
import traceback
import warnings

import pytest
from earnings_themes.coding import records as r
from earnings_themes.records import NonBlank

from .test_records import payloads

SENTINEL = "INVENTED_CODING_PRIVATE_SENTINEL"


def safe_output(value):
    """Assert on a boolean so pytest never expands the tested private value."""
    return SENTINEL not in str(value) + repr(value)


@pytest.mark.parametrize("name", tuple(payloads()))
def test_all_contract_representations_expose_only_content_hash(name):
    record = r.checked(payloads()[name], getattr(r, name))
    assert str(record) == repr(record)
    assert repr(record).startswith(f"{name}(sha256=")
    assert len(repr(record).split("sha256=", 1)[1][:-1]) == 64


def test_attributes_and_model_returned_ids_remain_local_in_json():
    data = {
        "theme_ids": [SENTINEL],
        "attributes": {"topic": SENTINEL, "event_type": SENTINEL},
    }
    record = r.checked(data, r.CodingReply)
    diagnostic = all(
        safe_output(value) for value in (record, record.attributes, [record])
    )
    assert diagnostic
    assert record.model_dump(mode="json") == {
        "theme_ids": [SENTINEL],
        "attributes": {
            "topic": SENTINEL,
            "sentiment": None,
            "direction": None,
            "event_type": SENTINEL,
        },
    }


class RawPart(r.CodingPart):
    """Invented future consumer of the safe base, without an adapter."""

    raw_reply: NonBlank


class NestedPart(r.CodingPart):
    rows: tuple[RawPart, ...]


def test_raw_reply_and_nested_collections_have_safe_representations():
    raw = r.checked({"raw_reply": SENTINEL}, RawPart)
    nested = r.checked({"rows": [{"raw_reply": SENTINEL}]}, NestedPart)
    diagnostic = all(
        safe_output(value) for value in (raw, nested, [raw, nested], {"rows": (raw,)})
    )
    assert diagnostic
    assert nested.model_dump(mode="json") == {"rows": [{"raw_reply": SENTINEL}]}


@pytest.mark.parametrize(
    "data",
    [
        SENTINEL,
        {SENTINEL: SENTINEL},
        {"theme_ids": [], "attributes": {SENTINEL: SENTINEL}},
        {"theme_ids": [SENTINEL, SENTINEL], "attributes": {}},
        {"theme_ids": [], "attributes": {"sentiment": SENTINEL}},
    ],
)
def test_malicious_fields_and_raw_replies_produce_only_fixed_errors(data):
    with pytest.raises(r.CodingError, match="^malformed_record$") as caught:
        r.checked(data, r.CodingReply)
    diagnostic = safe_output(caught.value) and SENTINEL not in "".join(
        traceback.format_exception_only(caught.value)
    )
    assert diagnostic
    assert caught.value.__suppress_context__


def test_unknown_transport_exception_diagnostics_are_redacted():
    transport = OSError(SENTINEL)
    diagnostic = safe_output(r.CodingError(transport))
    assert diagnostic
    assert str(r.CodingError(transport)) == "unexpected_error"
    with pytest.raises(r.CodingError, match="^malformed_record$") as caught:
        r.checked(transport, r.CodingReply)
    diagnostic = safe_output(caught.value)
    assert diagnostic


def string_paths(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from string_paths(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from string_paths(child, (*path, index))
    elif isinstance(value, str):
        yield path


@pytest.mark.parametrize("name", tuple(payloads()))
def test_sentinels_in_each_string_field_are_retained_locally_or_refused_safely(name):
    original = payloads()[name]
    for path in string_paths(original):
        data = copy.deepcopy(original)
        parent = data
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = SENTINEL
        try:
            value = r.checked(data, getattr(r, name))
        except r.CodingError as error:
            value = error
        diagnostic = safe_output(value)
        assert diagnostic


def test_unknown_string_subclass_reason_is_not_printed():
    class UnsafeString(str):
        def __str__(self):
            return SENTINEL

        def __repr__(self):
            return SENTINEL

    error = r.CodingError(UnsafeString("transport_error"))
    diagnostic = safe_output(error)
    assert diagnostic
    assert str(error) == "unexpected_error"


def test_constructed_invalid_value_never_emits_serializer_warning():
    from .test_records import BoundaryRecord

    invalid = BoundaryRecord.model_construct(count=SENTINEL)
    with warnings.catch_warnings(record=True) as emitted:
        warnings.simplefilter("always")
        with pytest.raises(r.CodingError, match="^malformed_record$"):
            r.checked(invalid, BoundaryRecord)
    diagnostic = len(emitted) == 0
    assert diagnostic
