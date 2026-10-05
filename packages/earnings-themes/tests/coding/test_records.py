"""Closed coding contracts and reparsing on invented values only."""

import copy
from typing import Literal

import pytest
from earnings_core import RejectionReason
from earnings_themes.coding import records as r
from earnings_themes.coding.records import CodingError, CodingReply, checked
from earnings_themes.support.problems import REASONS as SUPPORT_REASONS
from pydantic import Field, ValidationError

H = "a" * 64


def payloads():
    return {
        "CodingPart": {},
        "CodingRecord": {},
        "CodingAttributes": {
            "topic": "orders",
            "sentiment": "positive",
            "direction": "increase",
            "event_type": "investment",
        },
        "CodingReply": {"theme_ids": ["demand", "capacity"], "attributes": {}},
        "CodingPolicy": {
            "prompt_text": "Invented local coding prompt.",
            "prompt_hash": H,
            "parameters": {},
        },
        "CodingCeilings": {
            "requests_per_claim": 0,
            "requests_per_document": 0,
            "requests_per_run": 0,
            "tokens_per_document": 0,
            "tokens_per_run": 0,
        },
        "PolicyReference": {
            "policy_id": "invented-policy",
            "policy_hash": H,
            "kind": "fixture",
            "codebook": {
                "codebook_id": "invented-book",
                "codebook_version": 0,
                "content_hash": H,
            },
            "support_configuration_hash": H,
            "calibration_reference": None,
        },
        "PolicyVote": {"action": "review"},
    }


def test_annotations_are_separate_from_closed_theme_ids():
    reply = checked(
        {
            "theme_ids": ["demand", "capacity"],
            "attributes": {
                "topic": "orders",
                "sentiment": "positive",
                "direction": "increase",
                "event_type": "investment",
            },
        },
        CodingReply,
    )
    assert reply.theme_ids == ("demand", "capacity")
    assert reply.attributes.direction == "increase"
    assert not hasattr(reply, "importance")


@pytest.mark.parametrize(
    "extra",
    [
        {"cluster_label": "cluster-3"},
        {"accepted": True},
        {"definition": "Changed rules"},
        {"quote_text": "Copied words"},
        {"tools": [{"name": "fetch"}]},
        {"new_theme": "invented"},
    ],
)
def test_extra_fields_are_unusable(extra):
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked({"theme_ids": [], "attributes": {}, **extra}, CodingReply)


def test_duplicate_theme_ids_are_unusable():
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked({"theme_ids": ["demand", "demand"], "attributes": {}}, CodingReply)


@pytest.mark.parametrize("name", tuple(payloads()))
def test_contract_roundtrip_is_frozen_and_closed(name):
    model = getattr(r, name)
    record = checked(payloads()[name], model)
    assert checked(record, model) == record
    assert model.model_config["frozen"]
    assert model.model_config["strict"]
    assert model.model_config["extra"] == "forbid"
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(dict(payloads()[name], unknown="invented"), model)


@pytest.mark.parametrize("name", ["CodingPolicy", "PolicyReference", "PolicyVote"])
def test_policy_bindings_cannot_be_mutated_in_place(name):
    record = checked(payloads()[name], getattr(r, name))
    field = next(iter(type(record).model_fields))
    with pytest.raises(ValidationError):
        setattr(record, field, getattr(record, field))


@pytest.mark.parametrize(
    "field,value",
    [
        ("topic", " "),
        ("event_type", ""),
        ("sentiment", "important"),
        ("direction", "growing"),
        ("sentiment", 1),
        ("direction", True),
        ("importance", 0.8),
        ("cluster_label", "cluster-1"),
        ("subtheme", "invented"),
    ],
)
def test_annotations_reject_invalid_or_additional_values(field, value):
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked({field: value}, r.CodingAttributes)


@pytest.mark.parametrize("value", [True, "1", 1.0, 2, None])
def test_schema_version_is_a_strict_integer_literal(value):
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked({"schema_version": value}, r.CodingRecord)


@pytest.mark.parametrize("value", [True, "2", 2.0, 1, None])
def test_max_attempts_is_a_strict_integer_literal(value):
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(dict(payloads()["CodingPolicy"], max_attempts=value), r.CodingPolicy)


@pytest.mark.parametrize("field", tuple(payloads()["CodingCeilings"]))
@pytest.mark.parametrize("value", [True, "0", 0.0, -1, None])
def test_every_ceiling_is_a_strict_nonnegative_integer(field, value):
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(dict(payloads()["CodingCeilings"], **{field: value}), r.CodingCeilings)


@pytest.mark.parametrize("field", tuple(payloads()["CodingCeilings"]))
@pytest.mark.parametrize("value", [True, "0", 0.0])
@pytest.mark.parametrize("bypass", ["copy", "construct"])
def test_copied_and_constructed_ceilings_preserve_original_integer_types(
    field, value, bypass
):
    data = payloads()["CodingCeilings"]
    if bypass == "copy":
        invalid = checked(data, r.CodingCeilings).model_copy(update={field: value})
    else:
        invalid = r.CodingCeilings.model_construct(**dict(data, **{field: value}))
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(invalid, r.CodingCeilings)


@pytest.mark.parametrize("value", [True, "2", 2.0])
@pytest.mark.parametrize("bypass", ["copy", "construct"])
def test_copied_and_constructed_policy_rechecks_attempt_literal(value, bypass):
    data = payloads()["CodingPolicy"]
    if bypass == "copy":
        invalid = checked(data, r.CodingPolicy).model_copy(
            update={"max_attempts": value}
        )
    else:
        invalid = r.CodingPolicy.model_construct(**dict(data, max_attempts=value))
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(invalid, r.CodingPolicy)


@pytest.mark.parametrize(
    "name,field",
    [
        ("CodingReply", "attributes"),
        ("CodingPolicy", "parameters"),
        ("PolicyReference", "codebook"),
    ],
)
def test_nested_consumed_parts_are_closed(name, field):
    data = copy.deepcopy(payloads()[name])
    data[field]["unknown"] = "invented"
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(data, getattr(r, name))


@pytest.mark.parametrize("value", [True, "0", 0.0, -1])
def test_consumed_codebook_version_remains_a_strict_integer(value):
    data = payloads()["PolicyReference"]
    data["codebook"]["codebook_version"] = value
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(data, r.PolicyReference)


@pytest.mark.parametrize("kind,reference", [("fixture", H), ("calibrated", None)])
def test_calibration_reference_binds_policy_kind(kind, reference):
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(
            dict(
                payloads()["PolicyReference"],
                kind=kind,
                calibration_reference=reference,
            ),
            r.PolicyReference,
        )


def test_calibrated_policy_records_explicit_reference_without_thresholds():
    reference = checked(
        dict(payloads()["PolicyReference"], kind="calibrated", calibration_reference=H),
        r.PolicyReference,
    )
    assert reference.calibration_reference == H
    assert "threshold" not in r.PolicyReference.model_fields


@pytest.mark.parametrize(
    "action,ids",
    [("accept", []), ("accept", ["q", "q"]), ("reject", ["q"]), ("review", ["q"])],
)
def test_policy_votes_require_distinct_support_only_for_acceptance(action, ids):
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked({"action": action, "supporting_quote_ids": ids}, r.PolicyVote)


@pytest.mark.parametrize("action,ids", [("accept", ["q-1-2", "q-3-4"]), ("reject", [])])
def test_valid_policy_votes_preserve_quote_ids(action, ids):
    vote = checked({"action": action, "supporting_quote_ids": ids}, r.PolicyVote)
    assert vote.supporting_quote_ids == tuple(ids)


class BoundaryRecord(r.CodingRecord):
    """Invented consumer of the base's reusable integer/reason guards."""

    attempt: Literal[1, 2] = 1
    start: int = Field(default=0, ge=0)
    count: int = Field(default=0, ge=0)
    reason: str | None = None


@pytest.mark.parametrize("field", ["schema_version", "attempt", "start", "count"])
@pytest.mark.parametrize("value", [True, "1", 1.0])
@pytest.mark.parametrize("bypass", ["payload", "copy", "construct"])
def test_untrusted_integer_bypasses_are_revalidated(field, value, bypass):
    data = {field: value}
    if bypass == "copy":
        data = BoundaryRecord().model_copy(update=data)
    elif bypass == "construct":
        data = BoundaryRecord.model_construct(**data)
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(data, BoundaryRecord)


@pytest.mark.parametrize("bypass", ["copy", "construct"])
def test_untrusted_duplicate_reply_is_revalidated(bypass):
    data = {"theme_ids": ("demand", "demand"), "attributes": r.CodingAttributes()}
    if bypass == "copy":
        invalid = checked(payloads()["CodingReply"], CodingReply).model_copy(
            update=data
        )
    else:
        invalid = CodingReply.model_construct(**data)
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(invalid, CodingReply)


@pytest.mark.parametrize("reason", ["unrecognized", 1, True])
@pytest.mark.parametrize("bypass", ["payload", "copy", "construct"])
def test_reason_vocabulary_is_revalidated(reason, bypass):
    data = {"reason": reason}
    if bypass == "copy":
        data = BoundaryRecord().model_copy(update=data)
    elif bypass == "construct":
        data = BoundaryRecord.model_construct(**data)
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(data, BoundaryRecord)


def test_versions_and_fixed_reason_vocabulary():
    assert r.CODING_SCHEMA_VERSION == 1
    assert r.CODING_VERSION == "deductive-coding/1"
    assert r.REASONS == SUPPORT_REASONS | {p.value for p in r.CodingProblem}
    for reason in (*r.CodingProblem, *RejectionReason):
        assert str(CodingError(reason.value)) == reason.value
        assert checked({"reason": reason.value}, BoundaryRecord).reason == reason.value
    assert str(CodingError("unrecognized")) == "unexpected_error"
