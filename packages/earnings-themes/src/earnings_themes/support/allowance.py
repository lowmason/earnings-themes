"""Sequential explicit dispatch ceilings; reservations survive missing usage."""

from earnings_core import digest

from earnings_themes.extraction.adapters import Usage
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import SupportCeilings, UsageRecord
from earnings_themes.support.resolve import _validated


def reserved_judge_tokens(input_tokens: int, completion_limit: int) -> int:
    if type(input_tokens) is not int or type(completion_limit) is not int:
        raise SupportError("malformed_record")
    if input_tokens < 0 or completion_limit < 1:
        raise SupportError("malformed_record")
    return input_tokens + completion_limit


class Allowance:
    """Check every applicable ceiling before mutating any accounting state.

    The caller counts and checks the complete runtime input before reserving.
    Original reservations remain in snapshots; charged tokens are tracked apart
    from that immutable audit amount. Instances are sequential, not thread safe.
    """

    def __init__(self, ceilings: SupportCeilings) -> None:
        self.ceilings = _validated(ceilings, SupportCeilings)
        self._rows: dict[str, UsageRecord] = {}
        self._charged: dict[str, int] = {}
        self._settled: set[str] = set()

    def snapshot(self) -> tuple[UsageRecord, ...]:
        return tuple(self._rows.values())

    def reserve_scorer(self, target_id: str, doc_id: str) -> str:
        return self._reserve(target_id, doc_id, "scorer", 0)

    def reserve_judge(
        self, target_id: str, doc_id: str, input_tokens: int, completion_limit: int
    ) -> str:
        return self._reserve(
            target_id,
            doc_id,
            "judge",
            reserved_judge_tokens(input_tokens, completion_limit),
        )

    def _reserve(self, target_id: str, doc_id: str, kind: str, tokens: int) -> str:
        operation = digest(
            {
                "ordinal": len(self._rows),
                "kind": kind,
                "target": target_id,
                "document": doc_id,
            }
        )
        # Validate caller fields before checking budgets, with redacted diagnostics.
        row = _validated(
            UsageRecord.model_construct(
                target_id=target_id,
                doc_id=doc_id,
                operation_id=operation,
                kind=kind,
                reserved_tokens=tokens,
                actual_prompt_tokens=None,
                actual_completion_tokens=None,
                unreported=True,
                cached=False,
                latency_ms=0,
            ),
            UsageRecord,
        )
        rows = [r for r in self._rows.values() if r.kind == kind and not r.cached]
        counts = (
            sum(r.target_id == target_id for r in rows),
            sum(r.doc_id == doc_id for r in rows),
            len(rows),
        )
        limits = (
            getattr(self.ceilings, f"{kind}_per_target"),
            getattr(self.ceilings, f"{kind}_per_document"),
            getattr(self.ceilings, f"{kind}_per_run"),
        )
        if any(count >= limit for count, limit in zip(counts, limits, strict=True)):
            raise SupportError(f"{kind}_exhausted")
        if kind == "judge":
            document_tokens = sum(
                self._charged[key]
                for key, r in self._rows.items()
                if r.doc_id == doc_id
            )
            if (
                document_tokens + tokens > self.ceilings.tokens_per_document
                or sum(self._charged.values()) + tokens > self.ceilings.tokens_per_run
            ):
                raise SupportError("tokens_exhausted")
        self._rows[operation] = row
        self._charged[operation] = tokens
        return operation

    def settle(self, reservation_id: str, usage: Usage | None) -> None:
        if (
            not isinstance(reservation_id, str)
            or reservation_id not in self._rows
            or reservation_id in self._settled
        ):
            raise SupportError("malformed_record")
        row = self._rows[reservation_id]
        if usage is not None:
            usage = _validated(usage, Usage)
            actual = usage.prompt_tokens + usage.completion_tokens
            if row.kind == "judge":
                self._charged[reservation_id] = actual
            row = row.model_copy(
                update={
                    "actual_prompt_tokens": usage.prompt_tokens,
                    "actual_completion_tokens": usage.completion_tokens,
                    "unreported": False,
                }
            )
        self._rows[reservation_id] = row
        self._settled.add(reservation_id)

    def __repr__(self) -> str:
        return f"Allowance(operations={len(self._rows)})"

    __str__ = __repr__
