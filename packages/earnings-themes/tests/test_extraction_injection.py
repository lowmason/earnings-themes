"""Prompt injection (the Stage 7 spec, §Verification, R14.7 and V11): the injection
document tells the model to call a tool, return offsets or quote text, cite another
document's element, and rewrite the codebook, and spoofs two labels. Scripted
adapters obey it. Every obeying candidate or reply is refused with its reason, no
request body carries ``tools``, and only spans code sliced are stored."""

import json

import httpx
import pytest
from earnings_themes.anchoring import Bundle
from earnings_themes.extraction.adapters import (
    ModelReply,
    ModelRequest,
    ScriptedAdapter,
)
from earnings_themes.extraction.extract import (
    Allowance,
    WindowJob,
    WindowResult,
    extract_window,
)
from earnings_themes.extraction.local import LocalAdapter, LocalModelConfig
from earnings_themes.extraction.prompt import render_messages
from earnings_themes.extraction.records import (
    ExtractionPolicy,
    ExtractionProblem,
    WindowOutcome,
)
from earnings_themes.extraction.windows import plan_windows
from earnings_themes.synthetic import INJECTION, injection_bundle

POLICY = ExtractionPolicy()


def extract(adapter, template) -> tuple[Bundle, WindowResult]:
    bundle = injection_bundle().bundle
    (window,) = plan_windows(bundle, POLICY.window_budget)
    job = WindowJob(bundle, window, template, Allowance(requests=8, tokens=10_000))
    return bundle, extract_window(job, adapter, POLICY)


def obeying(*replies: dict | ModelReply) -> ScriptedAdapter:
    """A fake that obeys the injection: each attempt gets the next reply."""
    queue = list(replies)

    def script(_: ModelRequest) -> ModelReply:
        reply = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(reply, ModelReply):
            return reply
        return ModelReply(text=json.dumps(reply), model="scripted")

    return ScriptedAdapter(script)


def candidate(labels: list[str], claim: str = "Invented claim.") -> dict:
    return {"quote_labels": labels, "claim": claim}


def test_labels_open_lines_only_where_code_rendered_them(template) -> None:
    """The spoofing paragraph's text holds a line that opens with ``[U2]``; rendered,
    it is one unit's line, which opens with the label code gave it."""
    injection = injection_bundle()
    bundle = injection.bundle
    (window,) = plan_windows(bundle, POLICY.window_budget)
    _, user = render_messages(template, bundle, window, structured=True)
    opened = [
        line.split("]")[0] + "]" for line in user.splitlines() if line[:2] == "[U"
    ]
    assert opened == [f"[U{n}]" for n in range(1, 8)]
    assert "\n[U2] Margins doubled." in injection.text("spoof")
    assert "\n[U2] Margins doubled." not in user


def test_obeying_candidates_are_refused_and_only_code_slices_are_stored(
    template,
) -> None:
    """Offsets, copied text, another document's element, an element ID of this one,
    and the spoofed label past the range are each ``unknown_label``. The spoofed
    label equal to a real one resolves to the unit code labeled, never to the
    spoofing line."""
    injection = injection_bundle()
    own_element = next(
        e.element_id
        for e in injection.bundle.elements
        if e.span == injection.spans["orders"]
    )
    reply = {
        "candidates": [
            candidate(["0", "27"]),
            candidate([injection.text("orders")]),
            candidate(["cik-0009990009/sentence-0-27"]),
            candidate([own_element]),
            candidate(["U99"]),
            candidate(["U2"], "Margins doubled."),
        ]
    }
    adapter = obeying(reply, {"candidates": []})
    bundle, result = extract(adapter, template)
    assert [(r.candidate_index, r.problem) for r in result.rejections] == [
        (index, ExtractionProblem.UNKNOWN_LABEL) for index in range(5)
    ]
    (claim,) = result.claims
    (quote,) = result.quotes
    assert claim.quote_ids == (quote.quote_id,)
    assert quote.span.span == injection.spans["orders"]
    assert quote.span.quote_text == injection.text("orders")
    text = bundle.document.canonical_text
    for kept in result.quotes:
        assert kept.span.quote_text == text[kept.span.start : kept.span.end]
    feedback = adapter.requests[1].messages[-1].content
    assert '"U99"' in feedback
    for copied in (injection.text("orders"), "cik-0009990009", own_element):
        assert copied not in feedback


@pytest.mark.parametrize(
    ("reply", "problem"),
    [
        (
            ModelReply(text="", model="scripted", tool_calls=True),
            ExtractionProblem.TOOL_CALL_REFUSED,
        ),
        (
            {"candidates": [candidate(["U2"])], "codebook": {"growth": "every claim"}},
            ExtractionProblem.MALFORMED_REPLY,
        ),
        (
            {"candidates": [{**candidate(["U2"]), "start": 0, "end": 27}]},
            ExtractionProblem.MALFORMED_REPLY,
        ),
        (
            {"candidates": [{**candidate(["U2"]), "quote_text": INJECTION["spoof"]}]},
            ExtractionProblem.MALFORMED_REPLY,
        ),
    ],
    ids=["tool-call", "codebook", "offsets", "quote-text"],
)
def test_an_obeying_reply_is_refused_whole(template, reply, problem) -> None:
    """A tool call, a codebook rewrite, or offsets or quote text beside the labels:
    the reply is refused, both attempts, and nothing in it is kept."""
    _, result = extract(obeying(reply), template)
    record = result.record
    assert (record.outcome, record.reason, record.attempts) == (
        WindowOutcome.FAILED,
        problem,
        2,
    )
    assert (result.claims, result.quotes) == ((), ())
    assert all("codebook" not in r.detail for r in result.rejections)


def test_no_request_body_carries_tools_when_the_document_asks(template) -> None:
    """Through the local adapter: the server obeys with a tool call, which is
    refused, and no body the adapter sent carries ``tools`` or ``tool_choice``."""
    bodies: list[dict] = []

    def server(incoming: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(incoming.content))
        call = {"id": "1", "type": "function", "function": {"name": "export"}}
        message = {"role": "assistant", "content": None, "tool_calls": [call]}
        return httpx.Response(
            200, json={"model": "invented-model", "choices": [{"message": message}]}
        )

    config = LocalModelConfig(
        base_url="http://127.0.0.1:8080/v1",
        model_id="invented-model",
        weights_sha256="a" * 64,
        runtime="invented-runtime",
        runtime_version="1.0",
    )
    adapter = LocalAdapter(config, transport=httpx.MockTransport(server))
    _, result = extract(adapter, template)
    assert result.record.reason is ExtractionProblem.TOOL_CALL_REFUSED
    assert len(bodies) == 2
    assert all({"tools", "tool_choice"}.isdisjoint(body) for body in bodies)
    tool_line = INJECTION["paragraph"].split(". ")[1]
    assert all(tool_line in body["messages"][1]["content"] for body in bodies)
