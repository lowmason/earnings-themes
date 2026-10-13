"""The preregistration (the Stage 11 spec, A5 and §Preregistration; FP9, FP10,
FP15; R8.4).

``preregistration-v1.toml`` is committed on its own before any pilot output exists
(B2). It holds no text: the judge floor, the policy menu and its selection rule, the
label sample, the bootstrap, and V6's gate rule. It carries its own
``content_hash``, and ``load_preregistration`` refuses a file that does not hash to
it, so a later edit is caught (FP9).

- **The floor** is reported and recorded by V6; under Stage 9's routing it changes
  no decision (D19-1).
- **The menu** holds scorer-cutoff candidates over MiniCheck's joint score, each with
  its cutoff grid (D19-1).
- **The bootstrap** draws the 90% interval the spec reports throughout.
- **The gates** are exactly the metrics §Metrics marks gated. Each is higher-is-better,
  as ``derive_gates`` and ``evaluate_gates`` assume (a gate is a lower bound), so a
  reported, descriptive or not-estimated metric can never be gated (D1).
"""

from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, PositiveInt, field_validator, model_validator

from earnings_themes import tomlfile
from earnings_themes.evaluation.bootstrap import BootstrapPlan
from earnings_themes.evaluation.records import Metric, checked, sealed
from earnings_themes.gold import CodebookRef
from earnings_themes.records import IdPart, Part, Pin, Sha256Hex, ThemesRecord, parse

Share = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]

REQUIRED_GATES = frozenset(
    {
        Metric.RELEASE_PRECISION,
        Metric.RELEASE_RECALL,
        Metric.THEME_F1_MICRO,
        Metric.THEME_F1_MACRO,
        Metric.SPAN_UNIT_F1,
        Metric.GOLD_EVIDENCE_RECALL,
        Metric.SUPPORT_PRECISION,
    }
)
"""The metrics §Metrics gates, and the only ones the gate rule may list."""
LEVEL = 0.9
"""Every interval's level: the spec's 90% percentile interval, which V6's gates
file names."""
HEADER = (
    "Stage 11's preregistration (FP9), committed before any pilot output exists."
    " Numbers, rules and hashes only. Its content_hash covers every other field."
)


def _repeated(values: Iterable[str]) -> str:
    """The values that occur more than once, sorted and comma-joined."""
    return ", ".join(sorted(v for v, count in Counter(values).items() if count > 1))


class FloorRule(Part):
    """The judge agreement floor (FP9, R8.4)."""

    statistic: Literal["cohen_kappa"]
    reported: Literal["gwet_ac1"]
    population: Literal["family_verdict_vs_joint_label"]
    bound: Literal["event_bootstrap_lower"]
    floor: Annotated[float, Field(ge=0.3, le=0.6, allow_inf_nan=False)]
    consequence: Literal["reported_only"]


class Candidate(Part):
    """One menu candidate: accept an assessed target with an eligible quote when
    its MiniCheck joint score is at least the fitted cutoff (D19-1)."""

    candidate_id: IdPart
    rule: Literal["scorer_cutoff"]
    signal: Literal["minicheck_joint"]
    signals: Literal[1]
    grid: Annotated[tuple[Share, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def _sorted_grid(self) -> Self:
        if list(self.grid) != sorted(set(self.grid)):
            raise ValueError(
                f"candidate {self.candidate_id}: the grid must be sorted and unique"
            )
        return self


class SelectionRule(Part):
    """How a candidate is chosen (§Calibration)."""

    recall_floor: Annotated[float, Field(gt=0, le=1, allow_inf_nan=False)]
    objective: Literal["max_train_precision"]
    tie_break: Literal["fewer_signals_then_lower_cutoff"]


class SamplingPlan(Part):
    """The label sample (FP8)."""

    seed: int
    pool: Literal["assessed_and_flagged"]
    train_size: PositiveInt
    train_cap: PositiveInt
    dev_size: PositiveInt
    dev_cap: PositiveInt
    minimum_usable: Annotated[int, Field(ge=50)]
    extension_step: PositiveInt


class GateRule(Part):
    """V6's rule (FP15)."""

    rule: Literal["dev-lower-bound/1"]
    gated: Annotated[tuple[Metric, ...], Field(min_length=1)]
    undefined_gate: Literal["not_gated", "point_estimate"]

    @model_validator(mode="after")
    def _the_spec_gates(self) -> Self:
        if twice := _repeated(self.gated):
            raise ValueError(f"a metric is gated once: {twice} repeated")
        gated = set(self.gated)
        missing = ", ".join(sorted(REQUIRED_GATES - gated))
        extra = ", ".join(sorted(gated - REQUIRED_GATES))
        if missing or extra:
            raise ValueError(
                "the gates must be exactly §Metrics' gated metrics"
                f" (missing: {missing or 'none'};"
                f" not gated by the spec: {extra or 'none'})"
            )
        return self


class Preregistration(ThemesRecord):
    """``preregistration-v<N>.toml``."""

    preregistration_version: PositiveInt
    pin: Pin
    split_hash: Sha256Hex
    codebook: CodebookRef
    floor: FloorRule
    menu: Annotated[tuple[Candidate, ...], Field(min_length=1)]
    selection: SelectionRule
    sampling: SamplingPlan
    bootstrap: BootstrapPlan
    gates: GateRule
    content_hash: Sha256Hex

    @field_validator("menu")
    @classmethod
    def _distinct_candidates(cls, menu: tuple[Candidate, ...]) -> tuple[Candidate, ...]:
        if twice := _repeated(candidate.candidate_id for candidate in menu):
            raise ValueError(f"candidate IDs must be unique: {twice} repeated")
        return menu

    @field_validator("bootstrap")
    @classmethod
    def _ninety_percent(cls, bootstrap: BootstrapPlan) -> BootstrapPlan:
        if bootstrap.level != LEVEL:
            raise ValueError(
                f"bootstrap.level must be {LEVEL}, the spec's 90% interval,"
                f" not {bootstrap.level}"
            )
        return bootstrap


def freeze_preregistration(fields: Mapping[str, object]) -> Preregistration:
    """``fields`` as a preregistration, with its ``content_hash``."""
    draft = parse({**fields, "content_hash": "0" * 64}, Preregistration, "draft")
    return sealed(draft)


def preregistration_toml(record: Preregistration) -> str:
    """The committed file (B2)."""
    return tomlfile.dumps(record.model_dump(mode="json"), header=HEADER)


def load_preregistration(path: Path) -> Preregistration:
    """The committed preregistration, refused unless it hashes to its
    ``content_hash``."""
    return checked(parse(tomlfile.read(path), Preregistration, path.name), path.name)
