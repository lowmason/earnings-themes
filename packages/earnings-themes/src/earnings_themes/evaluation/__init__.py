"""Stage 11's evaluation: scoring the pilot, the user's support labels, and
calibration (the Stage 11 spec, A3–A5).

Pure: it reads no file, sends no request, loads no model and prints nothing. It
imports pure Stage 7–9 code and never ingestion, httpx, an NLI runtime or a concrete
adapter, and no gold-drafting module imports it (D19-4).
"""

from earnings_themes.evaluation.align import UnitIndex, unit_index, units_over
from earnings_themes.evaluation.bootstrap import (
    BootstrapPlan,
    Estimate,
    Interval,
    estimate,
)
from earnings_themes.evaluation.calibration import (
    CalibrationArtifact,
    calibrate,
    frozen_configuration,
)
from earnings_themes.evaluation.cells import (
    EventCells,
    EvidenceCell,
    event_cells,
    level_one,
)
from earnings_themes.evaluation.gates import (
    derive_gates,
    evaluate_gates,
    gates_toml,
    load_gates,
)
from earnings_themes.evaluation.label_view import label_views
from earnings_themes.evaluation.labels import (
    SupportLabel,
    SupportLabelSet,
    check_labels,
    labels_toml,
    load_labels,
    merge_labels,
)
from earnings_themes.evaluation.policy import CalibratedPolicy
from earnings_themes.evaluation.preregistration import (
    Preregistration,
    freeze_preregistration,
    load_preregistration,
    preregistration_toml,
)
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.evaluation.records import (
    Gates,
    GateVerdict,
    Metric,
    PartitionReport,
    PilotReport,
)
from earnings_themes.evaluation.report import (
    Accepted,
    EventObservation,
    LabelledTarget,
    compare_readings,
    partition_report,
    stability_figures,
)
from earnings_themes.evaluation.sampling import PoolTarget, label_pool, sample_targets

__all__ = [
    "Accepted",
    "BootstrapPlan",
    "CalibratedPolicy",
    "CalibrationArtifact",
    "Estimate",
    "EvaluationError",
    "EvaluationProblem",
    "EventCells",
    "EventObservation",
    "EvidenceCell",
    "GateVerdict",
    "Gates",
    "Interval",
    "LabelledTarget",
    "Metric",
    "PartitionReport",
    "PilotReport",
    "PoolTarget",
    "Preregistration",
    "SupportLabel",
    "SupportLabelSet",
    "UnitIndex",
    "calibrate",
    "check_labels",
    "compare_readings",
    "derive_gates",
    "estimate",
    "evaluate_gates",
    "event_cells",
    "freeze_preregistration",
    "frozen_configuration",
    "gates_toml",
    "label_pool",
    "label_views",
    "labels_toml",
    "level_one",
    "load_gates",
    "load_labels",
    "load_preregistration",
    "merge_labels",
    "partition_report",
    "preregistration_toml",
    "sample_targets",
    "stability_figures",
    "unit_index",
    "units_over",
]
