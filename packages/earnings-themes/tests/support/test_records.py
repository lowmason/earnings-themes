"""Closed support contracts on invented values only; no source artifacts."""

import traceback
from dataclasses import fields

import pytest
from earnings_core import RejectionReason, digest
from earnings_themes.support import records as r
from earnings_themes.support.problems import SupportError, SupportProblem

H = "a" * 64
S = "INVENTED_SENTINEL_RATIONALE"


def payloads():
    book = {"codebook_id": "book", "codebook_version": 0, "content_hash": H}
    target = {
        "source_run_id": "source",
        "doc_id": "doc",
        "claim_id": "claim",
        "theme_id": "theme",
        "codebook": book,
    }
    theme = {
        "codebook": book,
        "theme_id": "theme",
        "label": S,
        "definition": S,
        "parent_id": None,
        "inclusion_rules": [S],
        "exclusion_rules": [],
    }
    runtime = {
        "model_id": S,
        "revision": "revision",
        "files": [{"relative_path": "weights.bin", "sha256": H}],
        "runtime": "scripted",
        "runtime_version": "1",
        "device": "cpu",
        "precision": "fp32",
        "encoding_version": "1",
    }
    scorer = {"kind": "scripted", "runtime": runtime, "input_limit": 100}
    judge = {
        "family": "family-a",
        "runtime": runtime,
        "input_limit": 100,
        "output_limit": 50,
        "hosting": "scripted",
        "weight_license": None,
    }
    answer = {
        "claim_support": "supported",
        "theme_fit": "fits",
        "joint_support_score": 0.7,
        "quote_assessments": [{"quote_id": "q-1-2", "contribution": "supporting"}],
        "reason_codes": [],
        "summary": S,
    }
    reference = {
        "target_id": "target",
        "doc_id": "doc",
        "canonical_hash": H,
        "element_id": "sentence-1-2",
        "start": 1,
        "end": 2,
        "text_hash": H,
    }
    target_record = {
        "target_id": "target",
        "target": target,
        "source_run_hash": H,
        "claim_hash": H,
        "input_hash": H,
        "original_quote_ids": ["q-1-2"],
        "evidence_ids": ["q-1-2"],
        "theme": theme,
    }
    ceilings = dict.fromkeys(
        (
            "scorer_per_target",
            "scorer_per_document",
            "scorer_per_run",
            "judge_per_target",
            "judge_per_document",
            "judge_per_run",
            "tokens_per_document",
            "tokens_per_run",
        ),
        0,
    )
    run = {
        "run_id": "run",
        "started_at": "2026-10-05T12:00:00Z",
        "source_run_id": "source",
        "source_run_hash": H,
        "documents": [["doc", H]],
        "codebook": book,
        "configuration_hash": H,
        "extractor_family": "extractor",
        "scorer_identity": scorer,
        "judge_identities": [judge, dict(judge, family="family-b")],
        "support_version": "semantic-support/1",
        "validator_version": "3",
        "software": [["lock_hash", H]],
        "ceilings": ceilings,
        "counts_by_status": [["assessed", 1]],
        "counts_by_reason": [],
        "evaluations": 1,
        "requests": 4,
        "prompt_tokens": 10,
        "completion_tokens": 4,
        "reserved_tokens": 20,
        "unreported": 0,
        "cache_hits": 0,
        "billable_cost": "none, self-hosted",
        "artifact_hashes": [],
    }
    return {
        "CodebookReference": book,
        "Target": target,
        "ThemeSnapshot": theme,
        "FileHash": runtime["files"][0],
        "RuntimeIdentity": runtime,
        "WeightLicense": {
            "source_url": "https://example.test/license",
            "terms_reference": S,
            "intended_use": S,
            "verified_on": "2026-10-05",
            "permits_use": True,
        },
        "ScorerIdentity": scorer,
        "JudgeIdentity": judge,
        "EvidenceReference": dict(
            reference, quote_id="q-1-2", validator_version="3", mask_ids=[]
        ),
        "ContextReference": dict(reference, kind="block"),
        "TargetRecord": target_record,
        "QuoteAssessment": answer["quote_assessments"][0],
        "JudgeAnswer": answer,
        "EntailmentSignal": {
            "signal_id": "signal",
            "target_id": "target",
            "scope": "quote",
            "quote_id": "q-1-2",
            "evaluation_id": "evaluation",
            "identity": scorer,
            "input_hash": H,
            "status": "available",
            "score": 0.7,
            "reason": None,
            "input_tokens": 10,
            "latency_ms": 0,
            "cached": False,
        },
        "JudgeAttempt": {
            "attempt_id": "attempt",
            "trial_id": "trial",
            "attempt": 1,
            "request_hash": H,
            "prompt_hash": H,
            "schema_hash": H,
            "input_tokens": 10,
            "reserved_tokens": 20,
            "actual_prompt_tokens": None,
            "actual_completion_tokens": None,
            "latency_ms": 0,
            "cached": False,
            "raw_ref": S,
            "problem": None,
            "answer": answer,
        },
        "JudgeTrial": {
            "trial_id": "trial",
            "target_id": "target",
            "identity": judge,
            "presentation": "evidence_first",
            "attempt_ids": ["attempt"],
            "status": "available",
            "answer": answer,
            "reason": None,
        },
        "ReviewOutcome": {
            "target_id": "target",
            "status": "assessed",
            "flags": [],
            "missing": [],
            "signal_ids": ["signal"],
            "trial_ids": ["trial"],
        },
        "SupportCeilings": ceilings,
        "UsageRecord": {
            "target_id": "target",
            "doc_id": "doc",
            "operation_id": "operation",
            "kind": "judge",
            "reserved_tokens": 20,
            "actual_prompt_tokens": None,
            "actual_completion_tokens": None,
            "unreported": True,
            "cached": False,
            "latency_ms": 0,
        },
        "SupportPolicy": {
            "support_version": "semantic-support/1",
            "prompt_text": S,
            "prompt_hash": H,
            "parameters": {
                "temperature": 0.0,
                "seed": 0,
                "max_tokens": 50,
                "structured": True,
            },
        },
        "SupportRunRecord": run,
    }


@pytest.mark.parametrize("name", list(payloads()))
def test_records_round_trip_and_print_only_hash(name):
    model = getattr(r, name)
    value = r.parse_support(payloads()[name], model)
    serialized = value.model_dump(mode="json")
    assert r.parse_support(serialized, model) == value
    assert str(value) == repr(value) == f"{name}(sha256={digest(serialized)})"
    assert "SENTINEL" not in str([value])
    assert model.model_config["frozen"] and model.model_config["strict"]
    assert model.model_config["extra"] == "forbid"
    assert model.model_json_schema()["additionalProperties"] is False


def assert_refused(payload, model):
    with pytest.raises(SupportError) as caught:
        r.parse_support(payload, model)
    assert str(caught.value) == "malformed_record"
    assert "SENTINEL" not in repr(caught.value)
    assert "SENTINEL" not in "".join(traceback.format_exception(caught.value))
    assert caught.value.__suppress_context__


@pytest.mark.parametrize("name", list(payloads()))
def test_extra_fields_are_redacted_for_every_record(name):
    assert_refused(dict(payloads()[name], INVENTED_SENTINEL_KEY=S), getattr(r, name))


@pytest.mark.parametrize("path", [(), ("quote_assessments", 0)])
def test_reply_extra_keys_are_redacted_at_every_depth(path):
    payload = payloads()["JudgeAnswer"]
    nested = payload
    for key in path:
        nested = nested[key]
    nested["INVENTED_SENTINEL_KEY"] = S
    assert_refused(payload, r.JudgeAnswer)


@pytest.mark.parametrize(
    "score", [float("nan"), float("inf"), -float("inf"), -0.1, 1.1, True, S]
)
@pytest.mark.parametrize(
    "name,field",
    [("JudgeAnswer", "joint_support_score"), ("EntailmentSignal", "score")],
)
def test_invalid_scores_are_refused(name, field, score):
    assert_refused(dict(payloads()[name], **{field: score}), getattr(r, name))


@pytest.mark.parametrize("summary", ["", " ", "x" * 501])
def test_invalid_summary_is_refused(summary):
    assert_refused(dict(payloads()["JudgeAnswer"], summary=summary), r.JudgeAnswer)


@pytest.mark.parametrize("value", [True, 1.5, "1", -1])
@pytest.mark.parametrize(
    "name,field",
    [
        ("EvidenceReference", "start"),
        ("ContextReference", "end"),
        ("SupportCeilings", "scorer_per_run"),
        ("JudgeAttempt", "input_tokens"),
        ("UsageRecord", "latency_ms"),
        ("SupportRunRecord", "requests"),
        ("CodebookReference", "codebook_version"),
    ],
)
def test_counts_and_offsets_are_strict_nonnegative(name, field, value):
    assert_refused(dict(payloads()[name], **{field: value}), getattr(r, name))


@pytest.mark.parametrize(
    "name,field,value",
    [
        ("JudgeAnswer", "reason_codes", ["negation", "negation"]),
        (
            "JudgeAnswer",
            "quote_assessments",
            [{"quote_id": "q", "contribution": "supporting"}] * 2,
        ),
        ("TargetRecord", "original_quote_ids", ["q", "q"]),
        ("EvidenceReference", "mask_ids", ["m", "m"]),
        ("JudgeTrial", "attempt_ids", ["a", "a"]),
        ("ReviewOutcome", "flags", ["negation", "negation"]),
        ("EntailmentSignal", "status", "accepted"),
        ("JudgeTrial", "status", "accepted"),
        ("ReviewOutcome", "status", "accepted"),
        ("TargetRecord", "schema_version", 2),
        ("JudgeAttempt", "attempt", True),
        ("SupportPolicy", "max_attempts", True),
        ("EntailmentSignal", "reason", S),
        ("JudgeAttempt", "problem", S),
        ("ReviewOutcome", "missing", [S]),
        ("EvidenceReference", "end", 1),
        ("JudgeIdentity", "hosting", "local"),
        ("SupportRunRecord", "started_at", "2026-10-05T13:00:00+01:00"),
        ("SupportRunRecord", "software", [["unknown", "1"]]),
        ("SupportRunRecord", "counts_by_reason", [[S, 1]]),
        ("RuntimeIdentity", "files", [{"relative_path": "../weights", "sha256": H}]),
        ("FileHash", "relative_path", "/weights"),
        ("FileHash", "relative_path", "C:\\weights"),
        ("FileHash", "relative_path", "sub/../weights"),
    ],
)
def test_invalid_contract_combinations_are_refused(name, field, value):
    assert_refused(dict(payloads()[name], **{field: value}), getattr(r, name))


@pytest.mark.parametrize(
    "score,reason,status",
    [
        (None, None, "available"),
        (0.7, "scorer_failed", "available"),
        (0.7, "scorer_failed", "unavailable"),
        (None, None, "unavailable"),
    ],
)
def test_signal_availability_has_exact_score_reason_contract(score, reason, status):
    assert_refused(
        dict(payloads()["EntailmentSignal"], score=score, reason=reason, status=status),
        r.EntailmentSignal,
    )


def test_fixed_reason_vocabulary_and_versions():
    assert r.SUPPORT_SCHEMA_VERSION == 1
    assert r.SUPPORT_VERSION == "semantic-support/1"
    assert {x.value for x in r.ReasonCode} == {
        "wrong_attribution",
        "wrong_period",
        "negation",
        "scope_mismatch",
        "partial_support",
        "theme_mismatch",
        "exclusion_conflict",
        "context_only_support",
        "insufficient_evidence",
        "compound_claim",
    }
    for reason in (*SupportProblem, *RejectionReason):
        assert str(SupportError(reason.value)) == reason.value
    assert str(SupportError(S)) == "unexpected_error"


@pytest.mark.parametrize(
    "name",
    [
        "SupportSources",
        "ResolvedInput",
        "RefusedTarget",
        "AssessmentResult",
        "SupportRunResult",
        "StoredSupportRun",
    ],
)
def test_in_memory_containers_never_print_source_bearing_fields(name):
    model = getattr(r, name)
    container = model(**dict.fromkeys((field.name for field in fields(model)), S))
    assert "SENTINEL" not in str(container) + repr(container) + str([container])
    assert model.__dataclass_params__.frozen


def test_revalidation_refuses_constructed_invalid_model():
    valid = r.parse_support(payloads()["JudgeAnswer"], r.JudgeAnswer)
    invalid = valid.model_copy(update={"summary": ""})
    assert_refused(invalid.model_dump(mode="json"), r.JudgeAnswer)


@pytest.mark.parametrize("name", list(payloads()))
def test_every_nested_object_is_closed(name):
    import copy

    def paths(value, path=()):
        if isinstance(value, dict):
            yield path
            for key, child in value.items():
                yield from paths(child, (*path, key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from paths(child, (*path, index))

    payload = payloads()[name]
    for path in paths(payload):
        modified = copy.deepcopy(payload)
        nested = modified
        for key in path:
            nested = nested[key]
        nested["INVENTED_SENTINEL_KEY"] = S
        assert_refused(modified, getattr(r, name))


@pytest.mark.parametrize("value", [1, "true", False])
def test_weight_license_requires_literal_boolean_true(value):
    assert_refused(
        dict(payloads()["WeightLicense"], permits_use=value), r.WeightLicense
    )


def test_run_reason_counts_include_semantic_flags_without_ground_truth_labels():
    payload = dict(payloads()["SupportRunRecord"], counts_by_reason=[["negation", 1]])
    record = r.parse_support(payload, r.SupportRunRecord)
    assert record.counts_by_reason == (("negation", 1),)
    assert "accepted" not in type(record).model_fields
