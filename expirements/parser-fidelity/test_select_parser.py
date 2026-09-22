from score import rates
from select_parser import (
    control_check,
    priority_comparison,
    render,
    select,
    tie,
    worst_class,
)

NAMES = ("edgartools", "secparser", "walker", "control")


def pooled(coverage, footnotes=(0, 4), order=(0, 20), section=(0, 5), table=(0, 6)):
    counts = {
        "coverage": list(coverage),
        "footnote_merging": list(footnotes),
        "reading_order": list(order),
        "header_section": list(section),
        "header_table": list(table),
    }
    for extra in (
        "split",
        "other_merges",
        "duplication",
        "footnotes_in_tables",
        "cell_association",
    ):
        counts[extra] = [0, 0]
    return {"counts": counts, "rates": rates(counts)}


def classes(**by_candidate):
    """Two classes; each candidate gets (class A pooled, class B pooled)."""
    return {
        "clean_html": {name: values[0] for name, values in by_candidate.items()},
        "table_heavy": {name: values[1] for name, values in by_candidate.items()},
    }


def gates(nondeterministic=(), tripped=()):
    return {
        name: {
            "f1": {
                "deterministic": name not in nondeterministic,
                "guard_trips": ["socket.getaddrinfo"] if name in tripped else [],
            }
        }
        for name in NAMES
    }


LOCKS = {
    "edgartools": {
        "resolved": True,
        "lowered": [],
        "parse_ok": True,
        "pandas_added": True,
        "added_runtime": ["pandas", "pyarrow"],
    },
    "secparser": {
        "resolved": True,
        "lowered": ["lxml 6.1.3 -> 5.4.0"],
        "parse_ok": False,
        "pandas_added": True,
        "added_runtime": ["pandas"],
    },
    "walker": {
        "resolved": True,
        "lowered": [],
        "parse_ok": True,
        "pandas_added": False,
        "added_runtime": [],
    },
}


def test_worst_class_skips_classes_without_a_denominator():
    data = classes(
        walker=(pooled((9, 10), footnotes=(0, 0)), pooled((5, 10), footnotes=(1, 4)))
    )
    assert worst_class(data, "walker", "coverage") == (0.5, 10, "table_heavy")
    assert worst_class(data, "walker", "footnote_merging") == (0.25, 4, "table_heavy")


def test_tie_margin_uses_the_smaller_denominator():
    assert tie((0.80, 10, "a"), (0.75, 40, "b"))  # |0.05| <= 1/10
    assert not tie((0.80, 40, "a"), (0.70, 40, "b"))  # |0.10| > 1/40


def test_coverage_ranks_first():
    data = classes(
        edgartools=(pooled((95, 100)), pooled((60, 100), footnotes=(0, 4))),
        walker=(pooled((90, 100)), pooled((80, 100), footnotes=(3, 4))),
    )
    remaining, trace = priority_comparison(data, ["edgartools", "walker"])
    assert remaining == ["walker"]
    assert trace[0].startswith("coverage:")


def test_ties_fall_through_to_the_next_metric_then_tie_breaks():
    same = pooled((90, 100))
    data = classes(
        edgartools=(same, same),
        walker=(same, same),
        secparser=(same, same),
        control=(pooled((50, 100)), same),
    )
    outcome = select({"classes": data}, gates(), LOCKS)
    assert outcome["eligible"] == ["edgartools", "walker"]
    assert (
        outcome["selected"] == "walker"
    )  # tied on every metric; walker adds no dependency
    assert any(step.startswith("dependencies") for step in outcome["trace"])


def test_gates_exclude_ineligible_candidates_but_they_are_still_reported():
    strong, weak = pooled((99, 100)), pooled((70, 100))
    data = classes(
        edgartools=(weak, weak),
        secparser=(strong, strong),
        walker=(weak, weak),
        control=(weak, weak),
    )
    outcome = select({"classes": data}, gates(nondeterministic=("walker",)), LOCKS)
    assert outcome["eligible"] == ["edgartools"]
    assert outcome["selected"] == "edgartools"
    assert outcome["ineligible_would_have_won"] == ["secparser"]
    gains = outcome["ineligible_gains"]["secparser"]["coverage"]
    assert gains["ineligible"][0] == 0.99 and gains["selected"][0] == 0.70
    assert "secparser is ineligible but would have survived step 3" in render(outcome)


def test_no_eligible_candidate_returns_the_decision():
    data = classes(**{name: (pooled((90, 100)), pooled((90, 100))) for name in NAMES})
    outcome = select({"classes": data}, gates(tripped=("edgartools", "walker")), LOCKS)
    assert outcome["selected"] is None and "returns to the user" in outcome["status"]


def test_control_check_flags_fixtures_that_cannot_discriminate():
    same = pooled((90, 100))
    data = classes(walker=(same, same), control=(same, same))
    beats, discriminates = control_check(data, "walker")
    assert beats == {"clean_html": False, "table_heavy": False} and not discriminates
    data = classes(walker=(same, same), control=(pooled((60, 100)), same))
    assert control_check(data, "walker") == (
        {"clean_html": True, "table_heavy": False},
        True,
    )
