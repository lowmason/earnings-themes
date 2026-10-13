"""The calibrated assignment policy (the Stage 11 spec, A5; Stage 9's
``AssignmentPolicy``).

It applies the calibration artifact's selected rule. Stage 9 binds a policy
reference to one coding run's and one support run's configuration hashes
(``_policy_reference``), and the Stage 10 workflow fixes that reference before its
runs exist, so the caller supplies both hashes and the codebook (plan 19's handoff
to A8). An artifact with no selection binds no policy: every target stays in review
(``no_candidate``).
"""

from earnings_core import digest

from earnings_themes.coding.decide import DecisionInput
from earnings_themes.coding.records import PolicyReference, PolicyVote
from earnings_themes.evaluation.calibration import CalibrationArtifact, ScorerCutoff
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.evaluation.records import content_hash
from earnings_themes.support.records import CodebookReference


class CalibratedPolicy:
    """``AssignmentPolicy`` from a calibration artifact."""

    def __init__(
        self,
        artifact: CalibrationArtifact,
        *,
        codebook: CodebookReference,
        classifier_configuration_hash: str,
        support_configuration_hash: str,
    ) -> None:
        if content_hash(artifact) != artifact.content_hash:
            raise EvaluationError(
                EvaluationProblem.CONTENT_HASH_MISMATCH, "content_hash"
            )
        selection = artifact.selection
        if selection is None:
            raise EvaluationError(EvaluationProblem.NO_CANDIDATE, "selection")
        self._rule = ScorerCutoff(selection.cutoff)
        self._reference = PolicyReference(
            policy_id=f"calibrated-{selection.candidate_id}",
            policy_hash=digest(selection.model_dump(mode="json")),
            kind="calibrated",
            codebook=codebook,
            classifier_configuration_hash=classifier_configuration_hash,
            support_configuration_hash=support_configuration_hash,
            calibration_reference=artifact.content_hash,
        )

    @property
    def reference(self) -> PolicyReference:
        return self._reference

    def evaluate(self, view: DecisionInput) -> PolicyVote:
        return self._rule.vote(view)
