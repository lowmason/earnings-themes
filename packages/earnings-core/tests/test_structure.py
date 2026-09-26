import pytest
from earnings_core.documents import CanonicalDocument
from earnings_core.elements import DocumentElement, ElementType, TableCellContext
from earnings_core.rejections import Rejection, RejectionReason
from earnings_core.spans import TextSpan
from earnings_core.structure import resolve_pointer, validate_elements


def reasons(rejections: tuple[Rejection, ...]) -> list[RejectionReason]:
    return [rejection.reason for rejection in rejections]


def test_the_sample_structure_is_valid(sample) -> None:
    assert validate_elements(sample.document, sample.elements) == ()


def test_an_element_of_another_document_is_refused(sample) -> None:
    other = CanonicalDocument.create(
        source_document_id="another-call",
        canonicalization_version="test-1",
        canonical_text=sample.text,
    )
    stranger = DocumentElement.create(
        other, ElementType.OTHER, TextSpan(start=0, end=5)
    )
    assert reasons(validate_elements(sample.document, [stranger])) == [
        RejectionReason.WRONG_DOCUMENT
    ]


def test_a_tampered_element_id_is_caught(sample) -> None:
    section = sample.element(ElementType.SECTION, "Prepared remarks")
    moved = section.model_copy(update={"span": TextSpan(start=0, end=8)})
    assert reasons(validate_elements(sample.document, [moved])) == [
        RejectionReason.ELEMENT_ID_MISMATCH
    ]


def test_a_span_past_the_text_is_refused(sample) -> None:
    beyond = DocumentElement.create(
        sample.document,
        ElementType.OTHER,
        TextSpan(start=0, end=len(sample.text) + 1),
    )
    assert reasons(validate_elements(sample.document, [beyond])) == [
        RejectionReason.SPAN_OUT_OF_BOUNDS
    ]


def test_a_duplicate_element_is_refused(sample) -> None:
    section = sample.element(ElementType.SECTION, "Prepared remarks")
    assert reasons(validate_elements(sample.document, [section, section])) == [
        RejectionReason.DUPLICATE_ELEMENT
    ]


def test_parent_references_must_resolve_precede_and_contain(sample) -> None:
    section = sample.element(ElementType.SECTION, "Prepared remarks")
    heading = sample.element(ElementType.HEADING, "Prepared remarks")
    orphan = heading.model_copy(update={"parent_id": "section-999-1000"})
    assert reasons(validate_elements(sample.document, [orphan])) == [
        RejectionReason.UNKNOWN_PARENT
    ]
    assert reasons(validate_elements(sample.document, [heading, section])) == [
        RejectionReason.PARENT_ORDER
    ]
    later = sample.element(ElementType.SPEAKER_TURN, "Analyst:")
    escaped = later.model_copy(update={"parent_id": section.element_id})
    assert reasons(validate_elements(sample.document, [section, escaped])) == [
        RejectionReason.OUTSIDE_PARENT
    ]


def test_spans_that_cross_without_nesting_are_refused(sample) -> None:
    welcome = sample.span_of("Welcome")
    revenue = sample.span_of("Revenue")
    straddle = DocumentElement.create(
        sample.document,
        ElementType.OTHER,
        TextSpan(start=welcome.start, end=revenue.end),
    )
    found = validate_elements(sample.document, [*sample.elements, straddle])
    operator = sample.element(ElementType.SPEAKER_TURN, "Operator:")
    ceo = sample.element(ElementType.SPEAKER_TURN, "CEO:")
    sentence = sample.element(ElementType.SENTENCE, "Revenue rose")
    assert [(r.reason, r.detail) for r in found] == [
        (
            RejectionReason.CROSSING_ELEMENTS,
            f"{straddle.element_id} overlaps {operator.element_id} without nesting",
        ),
        (
            RejectionReason.CROSSING_ELEMENTS,
            f"{ceo.element_id} overlaps {straddle.element_id} without nesting",
        ),
        (
            RejectionReason.CROSSING_ELEMENTS,
            f"{sentence.element_id} overlaps {straddle.element_id} without nesting",
        ),
    ]


def test_every_crossing_pair_is_reported() -> None:
    document = CanonicalDocument.create(
        source_document_id="crossing-test",
        canonicalization_version="test-1",
        canonical_text="x" * 20,
    )
    a, b, c = (
        DocumentElement.create(
            document, ElementType.OTHER, TextSpan(start=start, end=end)
        )
        for start, end in ((0, 10), (5, 15), (12, 20))
    )
    found = validate_elements(document, [a, b, c])
    assert [r.detail for r in found] == [
        "other-5-15 overlaps other-0-10 without nesting",
        "other-12-20 overlaps other-5-15 without nesting",
    ]


def test_a_level_on_a_type_without_levels_is_malformed(sample) -> None:
    section = sample.element(ElementType.SECTION, "Prepared remarks")
    turn = sample.element(ElementType.SPEAKER_TURN, "Operator:")
    leveled = turn.model_copy(update={"level": 2})
    found = validate_elements(sample.document, [section, leveled])
    assert reasons(found) == [RejectionReason.MALFORMED_RECORD]
    assert "carries level 2" in found[0].detail


def test_a_table_cell_stripped_of_its_context_is_malformed() -> None:
    table, metric, *_ = table_elements()
    stripped = metric.model_copy(update={"table_cell": None})
    found = validate_elements(TABLE, [table, stripped])
    assert reasons(found) == [RejectionReason.MALFORMED_RECORD]


def test_table_context_on_another_type_is_malformed_only() -> None:
    table, metric, *_ = table_elements()
    paragraph = DocumentElement.create(
        TABLE, ElementType.PARAGRAPH, TextSpan(start=0, end=6)
    )
    misplaced = paragraph.model_copy(update={"table_cell": metric.table_cell})
    found = validate_elements(TABLE, [table, misplaced])
    assert reasons(found) == [RejectionReason.MALFORMED_RECORD]


def test_an_element_that_is_its_own_parent_is_malformed_only(sample) -> None:
    heading = sample.element(ElementType.HEADING, "Prepared remarks")
    looped = heading.model_copy(update={"parent_id": heading.element_id})
    found = validate_elements(sample.document, [looped])
    assert reasons(found) == [RejectionReason.MALFORMED_RECORD]
    assert "is its own parent" in found[0].detail


def test_a_tampered_document_is_reported_once(sample) -> None:
    tampered = sample.document.model_copy(update={"canonical_text": "changed"})
    assert reasons(validate_elements(tampered, sample.elements)) == [
        RejectionReason.DOCUMENT_INTEGRITY
    ]


TABLE_TEXT = "Metric\tQ3 2026\nNet sales\t$9.8"
TABLE = CanonicalDocument.create(
    source_document_id="table-test",
    canonicalization_version="test-1",
    canonical_text=TABLE_TEXT,
)


def cell(
    text: str, row: int, column: int, *, header: bool, parent: str, headers=()
) -> DocumentElement:
    start = TABLE_TEXT.index(text)
    return DocumentElement.create(
        TABLE,
        ElementType.TABLE_CELL,
        TextSpan(start=start, end=start + len(text)),
        parent_id=parent,
        table_cell=TableCellContext(
            row=row, column=column, is_header=header, header_cell_ids=tuple(headers)
        ),
    )


def table_elements(parent_type: ElementType = ElementType.TABLE) -> list:
    table = DocumentElement.create(
        TABLE, parent_type, TextSpan(start=0, end=len(TABLE_TEXT))
    )
    metric = cell("Metric", 0, 0, header=True, parent=table.element_id)
    quarter = cell("Q3 2026", 0, 1, header=True, parent=table.element_id)
    sales = cell(
        "Net sales",
        1,
        0,
        header=False,
        parent=table.element_id,
        headers=[metric.element_id],
    )
    value = cell(
        "$9.8",
        1,
        1,
        header=False,
        parent=table.element_id,
        headers=[quarter.element_id],
    )
    return [table, metric, quarter, sales, value]


def test_a_table_with_header_context_is_valid() -> None:
    assert validate_elements(TABLE, table_elements()) == ()


def test_a_table_cell_must_sit_in_a_table() -> None:
    found = validate_elements(TABLE, table_elements(ElementType.PARAGRAPH))
    assert set(reasons(found)) == {RejectionReason.TABLE_CELL_PARENT}


def test_a_header_reference_must_name_a_header_cell_of_the_same_table() -> None:
    table, metric, quarter, sales, _value = table_elements()
    wrong = cell(
        "$9.8", 1, 1, header=False, parent=table.element_id, headers=[sales.element_id]
    )
    found = validate_elements(TABLE, [table, metric, quarter, sales, wrong])
    assert reasons(found) == [RejectionReason.INVALID_HEADER_REFERENCE]


def test_a_pointer_resolves_to_its_elements_span(sample) -> None:
    sentence = sample.element(ElementType.SENTENCE, "Margins held")
    assert resolve_pointer(sample.document, sample.elements, sentence.element_id) == (
        sentence.span
    )


@pytest.mark.parametrize(
    "pointer",
    ["sentence-0-5", "", "sentence-12", "SENTENCE-0-16", "p12"],
    ids=["absent", "empty", "truncated", "wrong-case", "prompt-label"],
)
def test_an_invalid_pointer_is_rejected(sample, pointer: str) -> None:
    outcome = resolve_pointer(sample.document, sample.elements, pointer)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.UNKNOWN_ELEMENT


def test_a_pointer_into_another_version_is_rejected(sample) -> None:
    newer = CanonicalDocument.create(
        source_document_id="sample-call",
        canonicalization_version="test-1",
        canonical_text=sample.text.replace("5%", "6%"),
    )
    heading = sample.element(ElementType.HEADING, "Prepared remarks")
    outcome = resolve_pointer(newer, sample.elements, heading.element_id)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.WRONG_DOCUMENT


def test_a_tampered_pointer_target_is_rejected(sample) -> None:
    heading = sample.element(ElementType.HEADING, "Prepared remarks")
    moved = heading.model_copy(update={"span": TextSpan(start=0, end=8)})
    outcome = resolve_pointer(sample.document, [moved], heading.element_id)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.ELEMENT_ID_MISMATCH
