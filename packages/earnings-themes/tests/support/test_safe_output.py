"""Source-bearing diagnostics stay private; raw files stay under pytest tmp."""

import copy
import json
import traceback

import pytest
from earnings_themes.support import records
from earnings_themes.support.cache import SupportCache
from earnings_themes.support.judges import parse_answer
from earnings_themes.support.problems import SupportError
from earnings_themes.support.prompt import render_judge
from earnings_themes.support.store import read_support_run, write_support_run

from .cases import invented_case, judge_reply, resolved_case
from .test_assess import assess
from .test_prompt import policy as policy  # noqa: PLC0414
from .test_records import S, payloads
from .test_run import run

SECRET = "INVENTED_TASK10_PRIVATE"


def safe_diagnostic(value):
    """Bind the computed boolean so failures never print private strings."""
    printable = str(value) + repr(value)
    return SECRET not in printable and S not in printable


def test_unknown_reason_is_redacted():
    diagnostic = safe_diagnostic(SupportError(SECRET))
    assert diagnostic


@pytest.mark.parametrize("name", tuple(payloads()))
def test_every_support_record_redacts_source_bearing_fields(name):
    record = records.parse_support(payloads()[name], getattr(records, name))
    diagnostic = safe_diagnostic(record)
    assert diagnostic
    data = copy.deepcopy(payloads()[name])
    data[SECRET] = SECRET
    with pytest.raises(SupportError) as caught:
        records.parse_support(data, getattr(records, name))
    diagnostic = safe_diagnostic(caught.value)
    assert diagnostic


@pytest.mark.parametrize(
    "field", ["summary", "quote_id", "unknown_key", "raw", "model"]
)
def test_reply_errors_are_fixed_and_private(resolved, panel, policy, field):
    reply = judge_reply()(render_judge(resolved, policy, "evidence_first"))
    data = json.loads(reply.text)
    if field == "summary":
        data["summary"] = SECRET * 30
    elif field == "quote_id":
        data["quote_assessments"][0]["quote_id"] = SECRET
    elif field == "unknown_key":
        data[SECRET] = SECRET
    elif field == "raw":
        reply = reply.model_copy(update={"text": SECRET})
    else:
        reply = reply.model_copy(update={"model": SECRET})
    if field not in {"raw", "model"}:
        reply = reply.model_copy(update={"text": json.dumps(data)})
    with pytest.raises(SupportError) as caught:
        parse_answer(reply, resolved, panel[0].identity)
    diagnostic = safe_diagnostic(caught.value)
    assert diagnostic


def test_request_sources_rationale_and_failures_are_private(
    codebook, scorer, panel, policy, allowance, tmp_path, no_network
):
    resolved = resolved_case(
        *invented_case(
            codebook, (SECRET + " output improved.",), SECRET + " output improved."
        )
    )
    request = render_judge(resolved, policy, "evidence_first")
    diagnostic = safe_diagnostic(request) and safe_diagnostic(resolved)
    assert diagnostic
    original = judge_reply()

    def valid(request):
        reply = original(request)
        data = json.loads(reply.text)
        data["summary"] = SECRET
        return reply.model_copy(update={"text": json.dumps(data)})

    for judge in panel:
        judge.script = valid
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path / "valid")
    diagnostic = all(
        safe_diagnostic(value)
        for value in (
            result,
            result.outcome,
            *result.trials,
            *result.attempts,
            *result.evidence,
            *result.contexts,
        )
    )
    assert diagnostic
    assert result.outcome.status == "assessed"
    assert no_network == []


def test_raw_retry_feedback_omits_private_reply(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    from earnings_themes.extraction.adapters import ModelReply

    for judge in panel:
        judge.script = lambda request: ModelReply(text=SECRET, model="invented-judge")
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    feedback_private = any(
        SECRET in message.content
        for judge in panel
        for request in judge.requests[1:]
        for message in request.messages
    )
    diagnostic = (
        feedback_private,
        result.outcome.status,
        all(safe_diagnostic(a) for a in result.attempts),
    )
    assert diagnostic == (False, "incomplete", True)
    assert all(a.raw_ref for a in result.attempts)


def test_transport_exception_and_failure_summary_are_private(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    def fail(request):
        raise OSError(SECRET)

    panel[0].script = fail
    with pytest.raises(SupportError) as caught:
        assess(resolved, scorer, panel, policy, allowance, tmp_path)
    # format_exception respects the product's suppressed exception chaining.
    summary = "".join(traceback.format_exception_only(caught.value))
    diagnostic = safe_diagnostic(caught.value) and SECRET not in summary
    assert diagnostic
    assert allowance.snapshot()


def test_cache_corruption_and_persisted_unknown_keys_are_private(
    case, scorer, panel, policy, allowance, tmp_path
):
    first = run(case, scorer, panel, policy, allowance.ceilings, tmp_path / "cache")
    path = write_support_run(tmp_path / "support", first, case[0])
    raw_ref = first.assessments[0].attempts[0].raw_ref
    (tmp_path / "cache" / raw_ref).write_text(SECRET)
    replay = run(
        case,
        scorer,
        panel,
        policy,
        allowance.ceilings,
        tmp_path / "cache",
        cache=SupportCache(tmp_path / "cache", "replay"),
    )
    diagnostic = (
        replay.assessments[0].outcome.status,
        "cache_corrupt" in replay.assessments[0].outcome.missing,
        safe_diagnostic(replay),
    )
    assert diagnostic == ("incomplete", True, True)
    manifest = json.loads((path / "run.json").read_bytes())
    manifest[SECRET] = SECRET
    (path / "run.json").write_text(json.dumps(manifest))
    with pytest.raises(SupportError) as caught:
        read_support_run(path)
    diagnostic = safe_diagnostic(caught.value)
    assert diagnostic


def string_paths(value, path=()):
    """Enumerate local test fields without printing their values or map keys."""
    if isinstance(value, dict):
        for key, child in value.items():
            yield from string_paths(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from string_paths(child, (*path, index))
    elif isinstance(value, str):
        yield path


@pytest.mark.parametrize("name", tuple(payloads()))
def test_each_string_field_redacts_sentinel(name):
    payload = payloads()[name]
    for path in string_paths(payload):
        modified = copy.deepcopy(payload)
        parent = modified
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = SECRET
        try:
            value = records.parse_support(modified, getattr(records, name))
        except SupportError as error:
            value = error
        diagnostic = safe_diagnostic(value)
        assert diagnostic


def test_persisted_row_sentinel_is_refused_safely(
    case, scorer, panel, policy, allowance, tmp_path
):
    import polars as pl
    from earnings_core import sha256_hex

    first = run(case, scorer, panel, policy, allowance.ceilings, tmp_path / "cache")
    path = write_support_run(tmp_path / "support", first, case[0])
    artifact = path / "evidence.parquet"
    frame = pl.read_parquet(artifact)
    rows = frame.to_dicts()
    rows[0]["quote_id"] = SECRET
    pl.DataFrame(rows, schema=frame.schema).write_parquet(artifact)
    manifest = json.loads((path / "run.json").read_bytes())
    hashes = dict(manifest["artifact_hashes"])
    hashes[artifact.name] = sha256_hex(artifact.read_bytes())
    manifest["artifact_hashes"] = sorted(hashes.items())
    (path / "run.json").write_text(json.dumps(manifest))
    with pytest.raises(SupportError) as caught:
        read_support_run(path)
    diagnostic = safe_diagnostic(caught.value)
    assert diagnostic
