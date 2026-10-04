"""The prompt and the reply contract (the Stage 7 spec, §The prompt and the reply;
ES16, ES17, ES19)."""

import json
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_themes.extraction.prompt import (
    REPLY_SCHEMA,
    Reply,
    parse_reply,
    parse_template,
    refused_feedback,
    render_messages,
    render_units,
    unusable_feedback,
)
from earnings_themes.extraction.records import ExtractionProblem
from earnings_themes.extraction.windows import plan_windows

TEMPLATE = (
    Path(__file__).resolve().parents[3] / "prompts" / "extraction" / "pointer-1.md"
)


def test_the_template_parses_and_its_hash_covers_its_bytes() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    template = parse_template(text)
    assert template.sha256 == sha256_hex(TEMPLATE.read_bytes())
    assert "{units}" in template.user
    assert "{schema}" in template.schema
    assert "{units}" not in template.system


@pytest.mark.parametrize(
    "text",
    [
        "# System\nA.\n# User\n{units}\n",
        "# User\n{units}\n# System\nA.\n# Schema\n{schema}\n",
        "Preamble.\n# System\nA.\n# User\n{units}\n# Schema\n{schema}\n",
        "# System\nA {units}.\n# User\n{units}\n# Schema\n{schema}\n",
        "# System\nA.\n# User\nNo units.\n# Schema\n{schema}\n",
        "# System\nA.\n# User\n{units}\n# Schema\nNo schema.\n",
    ],
    ids=["no-schema", "order", "preamble", "units-twice", "no-units", "no-schema-mark"],
)
def test_a_template_without_its_sections_or_placeholders_is_refused(text) -> None:
    with pytest.raises(ValueError):
        parse_template(text)


def test_units_render_one_line_each_grouped_by_block(synthetic) -> None:
    bundle = synthetic.bundle
    (window,) = plan_windows(bundle, 4000)
    t = synthetic.text
    assert render_units(bundle, window) == "\n".join(
        [
            f"[U1] {t('heading')}",
            "",
            f"[U2] {t('sentence 1')}",
            f"[U3] {t('sentence 2')}",
            "",
            f"[U4] {t('repeat')}",
            "",
            f"[U5] {t('scanned')}",
            "",
            f"[U6] {t('harbor')}",
        ]
    )


def test_a_context_heading_comes_first_unlabeled_and_not_quotable(synthetic) -> None:
    bundle = synthetic.bundle
    window = plan_windows(bundle, 40)[1]
    t = synthetic.text
    assert render_units(bundle, window) == "\n".join(
        [
            f"[context, not quotable] {t('heading')}",
            "",
            f"[U1] {t('sentence 1')}",
            f"[U2] {t('sentence 2')}",
        ]
    )


def test_only_without_structured_mode_does_the_system_message_carry_the_schema(
    synthetic,
) -> None:
    template = parse_template(TEMPLATE.read_text(encoding="utf-8"))
    (window,) = plan_windows(synthetic.bundle, 4000)
    schema = json.dumps(REPLY_SCHEMA, sort_keys=True)
    system, user = render_messages(template, synthetic.bundle, window, structured=True)
    assert (system, schema in system) == (template.system, False)
    assert render_units(synthetic.bundle, window) in user
    system, _ = render_messages(template, synthetic.bundle, window, structured=False)
    assert system.startswith(template.system)
    assert system.endswith(schema)


def test_the_schema_is_closed_at_every_level() -> None:
    candidate = REPLY_SCHEMA["$defs"]["CandidateReply"]
    assert (REPLY_SCHEMA["additionalProperties"], REPLY_SCHEMA["required"]) == (
        False,
        ["candidates"],
    )
    assert (candidate["additionalProperties"], candidate["required"]) == (
        False,
        ["quote_labels", "claim"],
    )
    assert candidate["properties"]["quote_labels"]["minItems"] == 1


def test_a_reply_parses_and_an_empty_list_is_valid() -> None:
    reply = parse_reply('{"candidates": [{"quote_labels": ["U1"], "claim": "A."}]}')
    assert isinstance(reply, Reply)
    assert reply.candidates[0].quote_labels == ("U1",)
    assert parse_reply('{"candidates": []}') == Reply(candidates=())


@pytest.mark.parametrize(
    ("text", "problems"),
    [
        ("", ("record: Invalid JSON: EOF while parsing a value at line 1 column 0",)),
        (
            '{"candidates": [], "Secret words": 1}',
            ("<key>: Extra inputs are not permitted",),
        ),
        (
            '{"candidates": [{"quote_labels": [], "claim": 7, "Secret words": 1}]}',
            (
                "candidates.0.<key>: Extra inputs are not permitted",
                (
                    "candidates.0.quote_labels: Tuple should have at least 1 item"
                    " after validation, not 0"
                ),
                "candidates.0.claim: Input should be a valid string",
            ),
        ),
    ],
    ids=["not-json", "extra-key", "candidate"],
)
def test_a_broken_reply_names_each_problem_by_field_never_by_value(
    text, problems
) -> None:
    assert parse_reply(text) == problems


def test_feedback_names_fields_and_labels_and_reasons() -> None:
    unusable = (
        "Your reply could not be used:\n"
        "- candidates.0.claim: Field required\n"
        "Reply again with the JSON object only."
    )
    assert unusable_feedback(("candidates.0.claim: Field required",)) == unusable
    refused = [
        (1, ("U9",), ExtractionProblem.UNKNOWN_LABEL),
        (3, ("U2", "U2"), ExtractionProblem.DUPLICATE_LABEL),
        (4, ("Invented copied text.", "U0", "U3"), ExtractionProblem.UNKNOWN_LABEL),
    ]
    expected = (
        "These candidates were refused:\n"
        '- candidates[1], labels ["U9"]: unknown_label\n'
        '- candidates[3], labels ["U2", "U2"]: duplicate_label\n'
        '- candidates[4], labels ["<not a label>", "<not a label>", "U3"]:'
        " unknown_label\n"
        "Each label is one of U1 to U7, at most once per candidate, and each claim"
        " is non-blank and at most 500 characters.\n"
        "Reply with corrected versions of these candidates only, as a new object."
    )
    assert refused_feedback(refused, units=7, claim_limit=500) == expected
