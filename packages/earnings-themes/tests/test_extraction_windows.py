"""Units and windows (the Stage 7 spec, §Units and §Windows; ES12, ES13, ES14; R10.1
and R10.2): every unit lies in exactly one window, every eligible element holds a
unit, and the plan never reads a unit's text."""

from collections import Counter

from earnings_core import CanonicalDocument, ElementType
from earnings_themes.anchoring import Bundle, bundle_problems
from earnings_themes.extraction.units import block_of, eligible, units
from earnings_themes.extraction.windows import plan_windows

BUDGET = 4000


def test_the_stage_1_fixtures_hold_797_units_in_37_windows(fixtures) -> None:
    kinds = Counter(
        unit.type.value for bundle in fixtures.values() for unit in units(bundle)
    )
    windows = sum(len(plan_windows(bundle, BUDGET)) for bundle in fixtures.values())
    assert (dict(kinds), windows) == (
        {"sentence": 686, "heading": 108, "paragraph": 1, "footnote": 2},
        37,
    )


def test_every_unit_lies_in_exactly_one_window(fixtures) -> None:
    for name, bundle in fixtures.items():
        planned = [u for w in plan_windows(bundle, BUDGET) for u in w.unit_ids]
        expected = [unit.element_id for unit in units(bundle)]
        assert (name, planned) == (name, expected)


def test_every_eligible_element_holds_a_unit(fixtures) -> None:
    for name, bundle in fixtures.items():
        found = units(bundle)
        empty = [
            element.element_id
            for element in eligible(bundle)
            if not any(element.span.contains(unit.span) for unit in found)
        ]
        assert (name, empty) == (name, [])


def test_a_sentence_s_block_is_its_paragraph_list_item_or_footnote(fixtures) -> None:
    kinds = Counter()
    for bundle in fixtures.values():
        by_id = {element.element_id: element for element in bundle.elements}
        for unit in units(bundle):
            if unit.type is ElementType.SENTENCE:
                kinds[by_id[block_of(unit, by_id)].type.value] += 1
    assert set(kinds) <= {"paragraph", "list_item", "footnote"}
    assert sum(kinds.values()) == 686


def test_labels_run_in_document_order_within_each_window(fixtures) -> None:
    for bundle in fixtures.values():
        by_id = {element.element_id: element for element in bundle.elements}
        for window in plan_windows(bundle, BUDGET):
            starts = [by_id[unit_id].span.start for unit_id in window.unit_ids]
            assert starts == sorted(starts)
            assert list(window.labels) == [
                f"U{n}" for n in range(1, len(window.unit_ids) + 1)
            ]
            assert window.window_id == f"w-{window.start}-{window.end}"


def test_a_block_is_never_split_and_one_over_the_budget_stands_alone(fixtures) -> None:
    over = []
    for name, bundle in fixtures.items():
        by_id = {element.element_id: element for element in bundle.elements}
        for window in plan_windows(bundle, BUDGET):
            size = sum(by_id[unit_id].span.length for unit_id in window.unit_ids)
            for block in window.blocks:
                owners = {block_of(by_id[unit_id], by_id) for unit_id in block}
                assert len(owners) == 1
            if size > BUDGET:
                over.append((name, window.window_id, len(window.blocks), size))
    assert over == [("0000010795-22-000014_ex-99-1", "w-15361-19669", 1, 4301)]


def test_no_budget_gives_one_window_per_document(fixtures) -> None:
    for bundle in fixtures.values():
        windows = plan_windows(bundle, None)
        assert len(windows) == 1
        assert len(windows[0].unit_ids) == len(units(bundle))


def same_lengths_other_text(bundle: Bundle) -> Bundle:
    """``bundle`` with every unit's text replaced by other characters, one for one."""
    chars = list(bundle.document.canonical_text)
    for unit in units(bundle):
        for i in range(unit.span.start, unit.span.end):
            chars[i] = "z" if chars[i] == "q" else "q"
    document = CanonicalDocument.create(
        source_document_id=bundle.document.source_document_id,
        canonicalization_version=bundle.document.canonicalization_version,
        canonical_text="".join(chars),
    )
    elements = tuple(
        e.model_copy(update={"doc_id": document.doc_id}) for e in bundle.elements
    )
    masks = tuple(
        m.model_copy(
            update={
                "doc_id": document.doc_id,
                "canonical_hash": document.canonical_hash,
            }
        )
        for m in bundle.masks
    )
    return Bundle(bundle.name, document, elements, masks)


def test_the_plan_reads_structure_and_lengths_never_text(fixtures) -> None:
    """R10.2: replacing each unit's text with other text of the same length leaves
    the plan identical, so nothing in it can rank or retrieve by content."""
    for bundle in fixtures.values():
        other = same_lengths_other_text(bundle)
        assert bundle_problems(other) == []
        assert other.document.canonical_text != bundle.document.canonical_text

        def plan(b: Bundle) -> list[tuple]:
            return [
                (w.window_id, w.blocks, w.context_id) for w in plan_windows(b, BUDGET)
            ]

        assert plan(other) == plan(bundle)


def test_the_synthetic_document_s_units_and_windows(synthetic) -> None:
    """The heading, the two sentences, and the three unsplit paragraphs are units;
    the table, its cells, and the page artifact are not. A small budget splits the
    blocks into windows, and each window after a heading carries it as context."""
    bundle = synthetic.bundle
    spans = synthetic.spans
    assert [(u.type.value, u.span) for u in units(bundle)] == [
        ("heading", spans["heading"]),
        ("sentence", spans["sentence 1"]),
        ("sentence", spans["sentence 2"]),
        ("paragraph", spans["repeat"]),
        ("paragraph", spans["scanned"]),
        ("paragraph", spans["harbor"]),
    ]
    windows = plan_windows(bundle, 40)
    heading_id = units(bundle)[0].element_id
    assert [(len(w.blocks), len(w.unit_ids), w.context_id) for w in windows] == [
        (1, 1, None),
        (1, 2, heading_id),
        (1, 1, heading_id),
        (1, 1, heading_id),
        (1, 1, heading_id),
    ]
    assert [len(w.unit_ids) for w in plan_windows(bundle, BUDGET)] == [6]
