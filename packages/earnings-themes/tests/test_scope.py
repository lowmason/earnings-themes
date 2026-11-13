"""Plan 23's gate scope: one gate validates an unchanged input once, and every gate
still starts with an empty memo. The tests hold invented values only."""

import gc
import inspect
import weakref

import pytest
from earnings_themes.scope import gate, gated, once, remember


class Keyed:
    """A plain object: it takes a weak reference, and two instances are equal."""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Keyed)

    def __hash__(self) -> int:
        return 0


class Counter:
    """A compute callback that counts its calls and returns the count."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> int:
        self.calls += 1
        return self.calls


def test_once_outside_a_scope_always_computes() -> None:
    keyed = Keyed()
    compute = Counter()

    assert once("kind", (keyed,), compute) == 1
    assert once("kind", (keyed,), compute) == 2
    assert compute.calls == 2


def test_once_inside_a_gate_computes_once_per_identity() -> None:
    first, second = Keyed(), Keyed()
    assert first == second
    assert first is not second
    compute = Counter()

    with gate():
        assert once("kind", (first,), compute) == 1
        assert once("kind", (first,), compute) == 1
        assert compute.calls == 1
        # Equal but distinct: the key is identity, not equality.
        assert once("kind", (second,), compute) == 2
        assert once("kind", (second,), compute) == 2
        # Another kind, or another order of the same objects, is another key.
        assert once("other", (first,), compute) == 3
        assert once("pair", (first, second), compute) == 4
        assert once("pair", (second, first), compute) == 5
        assert once("pair", (first, second), compute) == 4
        assert compute.calls == 5


def test_nested_gate_joins_and_fresh_gate_hides_the_outer_memo() -> None:
    keyed = Keyed()
    compute = Counter()

    with gate():
        assert once("kind", (keyed,), compute) == 1
        with gate():
            # A plain gate joins the open scope.
            assert once("kind", (keyed,), compute) == 1
            assert compute.calls == 1
        with gate(fresh=True):
            # A fresh gate hides the outer memo and keeps its own.
            assert once("kind", (keyed,), compute) == 2
            assert once("kind", (keyed,), compute) == 2
            with gate():
                assert once("kind", (keyed,), compute) == 2
        # The fresh gate has closed: the outer memo is visible again.
        assert once("kind", (keyed,), compute) == 1
        assert compute.calls == 2

    # No scope is open any more, so nothing is reused.
    assert once("kind", (keyed,), compute) == 3


def test_an_exception_is_not_remembered() -> None:
    keyed = Keyed()
    calls = []

    def refuse() -> int:
        calls.append(1)
        raise ValueError("refused")

    with gate():
        for expected in (1, 2):
            with pytest.raises(ValueError, match="refused"):
                once("kind", (keyed,), refuse)
            assert len(calls) == expected
        # A later success under the same key is computed and then kept.
        compute = Counter()
        assert once("kind", (keyed,), compute) == 1
        assert once("kind", (keyed,), compute) == 1
        assert compute.calls == 1


def test_closing_the_outermost_gate_releases_the_memo() -> None:
    outer, inner = Keyed(), Keyed()
    outer_ref, inner_ref = weakref.ref(outer), weakref.ref(inner)

    with gate():
        once("kind", (outer,), lambda: "outer value")
        with gate(fresh=True):
            once("kind", (inner,), lambda: "inner value")
            del inner
            gc.collect()
            # The scope holds the keyed object, so its id cannot be reused.
            assert inner_ref() is not None
        # A fresh gate releases its own memo when it closes.
        gc.collect()
        assert inner_ref() is None
        del outer
        gc.collect()
        assert outer_ref() is not None
        with gate():
            # A joined gate releases nothing: the outer scope is still open.
            gc.collect()
            assert outer_ref() is not None

    gc.collect()
    assert outer_ref() is None


def test_gated_decorator_opens_or_joins() -> None:
    keyed = Keyed()
    compute = Counter()

    @gated
    def check(label: str, *, times: int = 2) -> list[int]:
        """Validate ``keyed`` ``times`` times."""
        return [once(label, (keyed,), compute) for _ in range(times)]

    @gated(fresh=True)
    def recheck() -> int:
        return once("shared", (keyed,), compute)

    # The wrapper keeps the name, the docstring and the signature.
    assert check.__name__ == "check"
    assert check.__doc__ == "Validate ``keyed`` ``times`` times."
    assert (
        str(inspect.signature(check)) == "(label: str, *, times: int = 2) -> list[int]"
    )
    assert recheck.__name__ == "recheck"

    # A call opens a scope: the repeat inside it is reused, the next call is not.
    assert check("a") == [1, 1]
    assert check("a", times=1) == [2]
    assert compute.calls == 2

    # Called inside an open gate, a plain gated function joins that scope.
    with gate():
        assert once("shared", (keyed,), compute) == 3
        assert check("shared") == [3, 3]
        # A fresh gated function hides the open scope for its own call.
        assert recheck() == 4
        assert once("shared", (keyed,), compute) == 3
    assert compute.calls == 4

    # The scope closes when the call raises.
    @gated
    def fail() -> None:
        once("kind", (keyed,), compute)
        raise RuntimeError("refused")

    with pytest.raises(RuntimeError, match="refused"):
        fail()
    assert once("kind", (keyed,), compute) == 6


def test_remember_adds_a_second_key() -> None:
    source, result = Keyed(), Keyed()
    compute = Counter()

    with gate():
        # Compute a result from the source, then record the result as checked too.
        assert once("load", (source,), lambda: result) is result
        remember("checked", (result,), "ok")
        assert once("checked", (result,), compute) == "ok"
        assert compute.calls == 0
        # The first key still answers.
        assert once("load", (source,), compute) is result
        assert compute.calls == 0

    # Outside a scope, remember does nothing.
    remember("checked", (result,), "ok")
    assert once("checked", (result,), compute) == 1

    # The remembered value is gone with its scope, and does not leak into the next.
    with gate():
        assert once("checked", (result,), compute) == 2
