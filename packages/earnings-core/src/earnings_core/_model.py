"""The base classes every earnings-core contract shares."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

SCHEMA_VERSION = 1
"""The version of every earnings-core contract; any field change bumps it (A §187)."""


class ContractModel(BaseModel):
    """Immutable, closed, strictly typed: a contract never coerces a value or grows a field.

    Strict mode rejects a bool, a float, or a numeric string where an integer belongs
    (A §532). ``model_copy(update=...)`` skips validation, so the validators recheck
    every stored invariant instead of trusting construction.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class VersionedRecord(ContractModel):
    """A top-level record that carries its schema version when serialized."""

    schema_version: Literal[1] = SCHEMA_VERSION
