"""The gate scope: one verification gate checks an unchanged input once (plan 23, D23-1).

A gate named by a spec still re-checks every input in full (D21-34). Inside one gate,
the same unchanged input needs only its first check. ``gate`` opens a scope for that
gate, ``once`` runs a check once per scope, and ``remember`` records a value that a
later ``once`` in the same scope can return without a check.

A scope keys a value by its ``kind`` and the identity (``id``) of the objects it was
computed from, never by their equality. Two equal but distinct objects are checked
twice. The scope holds a strong reference to each keyed object, so an ``id`` cannot
pass to another object while the scope is open. Closing the outermost gate drops the
memo and those references, so memory does not grow with the number of gates run.

Outside a scope, ``once`` always calls ``compute`` and ``remember`` does nothing.
A thread or task starts with no open scope unless it copies the context that holds one.
This module imports nothing from the rest of the package.
"""

import functools
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import cast, overload

type _Key = tuple[str, tuple[int, ...]]
type _Entry = tuple[tuple[object, ...], object]


class _Scope:
    """One gate's memo: each entry keeps the keyed objects next to the value."""

    __slots__ = ("memo",)

    def __init__(self) -> None:
        self.memo: dict[_Key, _Entry] = {}


_open: ContextVar[_Scope | None] = ContextVar(
    "earnings_themes_gate_scope", default=None
)


def _key(kind: str, objects: tuple[object, ...]) -> _Key:
    return kind, tuple(id(item) for item in objects)


@contextmanager
def gate(*, fresh: bool = False) -> Iterator[None]:
    """Open a scope, or join the open one unless ``fresh``.

    A ``fresh`` scope hides the outer memo until it closes. The scope that a gate
    opens is dropped when that gate closes, also when its body raises.
    """
    if not fresh and _open.get() is not None:
        yield
        return
    scope = _Scope()
    token = _open.set(scope)
    try:
        yield
    finally:
        _open.reset(token)
        scope.memo.clear()


@overload
def gated[**P, R](
    function: Callable[P, R], *, fresh: bool = False
) -> Callable[P, R]: ...


@overload
def gated[**P, R](
    function: None = None, *, fresh: bool = False
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def gated[**P, R](
    function: Callable[P, R] | None = None, *, fresh: bool = False
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """Run each call of a plain function inside ``gate(fresh=fresh)``.

    Use it as ``@gated`` or ``@gated(fresh=True)``. The wrapper keeps the function's
    name, docstring and signature. A generator or coroutine function would return
    before its body runs, so do not wrap one.
    """

    def decorate(inner: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(inner)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with gate(fresh=fresh):
                return inner(*args, **kwargs)

        return wrapper

    return decorate if function is None else decorate(function)


def once[T](kind: str, objects: tuple[object, ...], compute: Callable[[], T]) -> T:
    """Return the value that this scope computed for ``kind`` and ``objects``.

    Objects match by identity. Without an earlier value, call ``compute`` and keep
    its result. An exception from ``compute`` is never kept, so the same input
    raises again at the next call. Outside a scope, always call ``compute``.
    """
    scope = _open.get()
    if scope is None:
        return compute()
    key = _key(kind, objects)
    entry = scope.memo.get(key)
    if entry is not None:
        return cast(T, entry[1])
    value = compute()
    scope.memo[key] = (objects, value)
    return value


def remember(kind: str, objects: tuple[object, ...], value: object) -> None:
    """Store ``value`` under one more key, so a later ``once`` returns it.

    Outside a scope, do nothing.
    """
    scope = _open.get()
    if scope is not None:
        scope.memo[_key(kind, objects)] = (objects, value)
