"""Coding diagnostics on invented sentinel data remain fixed and private."""

import copy
import json
import traceback
import warnings

import pytest
from earnings_themes.coding import records as r
from earnings_themes.records import NonBlank

from .cases import (
    FixturePolicy,
    invented_bundle,
    make_assessed_case,
    make_proposal_job,
    make_sources,
    make_support_parts,
)
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


@pytest.mark.parametrize(
    "kind",
    ["malformed-json", "map-key", "copied-source", "unknown-theme", "tool-metadata"],
)
def test_unusable_sentinel_reply_has_only_fixed_diagnostics(
    codebook,
    template,
    coding_policy,
    classifier_identity,
    tmp_path,
    no_network,
    capsys,
    kind,
):
    from earnings_themes.coding.cache import CodingCache
    from earnings_themes.extraction.adapters import ModelReply

    from .cases import invented_codebook

    sources = make_sources(
        invented_codebook(codebook),
        invented_bundle(),
        template,
        claim_texts=(SENTINEL,),
    )
    job = make_proposal_job(sources, coding_policy, classifier_identity, tmp_path)
    answer = {"theme_ids": ["demand"], "attributes": {}}
    reason = "malformed_reply"
    if kind == "malformed-json":
        reply = "{" + SENTINEL
    elif kind == "map-key":
        reply = {**answer, SENTINEL: SENTINEL}
    elif kind == "copied-source":
        reply = {**answer, "claim": sources.stored_run.claims[0].claim}
    elif kind == "unknown-theme":
        reply = {**answer, "theme_ids": [SENTINEL]}
        reason = "invalid_references"
    else:
        reply = ModelReply(
            text=json.dumps({**answer, "tool_calls": [{"name": SENTINEL}]}),
            model=classifier_identity.runtime.model_id,
            tool_calls=True,
        )
        reason = "tool_call_refused"
    result, calls = job.run([reply, reply])
    assert calls == 2
    assert result.targets == result.novelty == ()
    assert [row.reason for row in result.attempts] == [reason, reason]
    cache = CodingCache(tmp_path / "classifier-cache", "replay")
    entries = [cache.get(request, classifier_identity) for request in job.requests]
    retained_locally = all(SENTINEL in entry.model_dump_json() for entry in entries)
    assert retained_locally
    diagnostic = all(
        safe_output(value)
        for value in (
            result,
            result.record,
            result.attempts,
            job.requests,
            entries,
            {"records": (result.record, *result.attempts, *entries)},
        )
    )
    assert diagnostic
    feedback_is_fixed = job.requests[1].messages[-1].content == (
        f"Unusable reply: {reason}. Return the closed JSON response only."
    )
    assert feedback_is_fixed
    captured = capsys.readouterr()
    diagnostic = safe_output(captured.out + captured.err)
    assert diagnostic
    assert no_network == []


@pytest.mark.parametrize("phase", ["classifier", "policy-reference", "policy-vote"])
def test_arbitrary_exception_name_and_message_are_not_diagnostics(
    proposal_job,
    assessed_case,
    fixture_policy,
    coding_policy,
    classifier_identity,
    phase,
    no_network,
    capsys,
):
    private_error = type(SENTINEL, (RuntimeError,), {})

    def forbidden(*args, **kwargs):
        raise private_error(SENTINEL)

    with pytest.raises(r.CodingError, match="^unexpected_error$") as caught:
        if phase == "classifier":
            fresh = make_proposal_job(
                proposal_job.sources,
                coding_policy,
                classifier_identity,
                proposal_job.root / "exception",
            )
            fresh.run([private_error(SENTINEL)])
        elif phase == "policy-reference":

            class BrokenReference:
                reference = property(forbidden)
                evaluate = forbidden

            assessed_case.decide(BrokenReference())
        else:
            fixture_policy.evaluate = forbidden
            assessed_case.decide(fixture_policy)
    diagnostic = safe_output(caught.value) and SENTINEL not in "".join(
        traceback.format_exception_only(caught.value)
    )
    assert diagnostic
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__
    captured = capsys.readouterr()
    diagnostic = safe_output(captured.out + captured.err)
    assert diagnostic
    assert no_network == []


def test_malicious_classifier_policy_ids_and_nested_rationale_remain_local(
    coding_case, coding_policy, classifier_identity, tmp_path, no_network, capsys
):
    identity = classifier_identity.model_copy(
        update={
            "family": SENTINEL,
            "runtime": classifier_identity.runtime.model_copy(
                update={"model_id": SENTINEL}
            ),
        }
    )
    job = make_proposal_job(coding_case, coding_policy, identity, tmp_path)
    proposals, calls = job.run(
        [{"theme_ids": ["demand"], "attributes": {"topic": SENTINEL}}]
    )
    assert calls == 1
    scorer, panel = make_support_parts()
    for judge in panel:
        original = judge.script

        def rationale(request, original=original):
            reply = original(request)
            body = json.loads(reply.text)
            body["summary"] = SENTINEL
            return reply.model_copy(update={"text": json.dumps(body)})

        judge.script = rationale
    case = make_assessed_case(proposals, coding_case, tmp_path, parts=(scorer, panel))
    policy = FixturePolicy(proposals, case.support)
    policy.reference = policy.reference.model_copy(update={"policy_id": SENTINEL})
    result = case.decide(policy)
    nested = (
        proposals.record,
        proposals.attributes,
        result.decisions,
        case.support.trials,
        {"signals": case.support.trials, "policy": policy.reference},
    )
    diagnostic = all(safe_output(value) for value in nested)
    assert diagnostic
    retained_locally = (
        SENTINEL in proposals.record.model_dump_json()
        and SENTINEL in result.decisions[0].model_dump_json()
        and all(SENTINEL in trial.model_dump_json() for trial in case.support.trials)
    )
    assert retained_locally
    captured = capsys.readouterr()
    diagnostic = safe_output(captured.out + captured.err)
    assert diagnostic
    assert no_network == []


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
