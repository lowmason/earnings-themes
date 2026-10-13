"""Stage 9's invented assessed case, reused from the coding tests: one invented
document, claim, quote and theme, assessed by scripted judges (GS13)."""

from importlib import import_module

_coding = import_module("packages.earnings-themes.tests.coding.conftest")

coding_case = _coding.coding_case
coding_policy = _coding.coding_policy
classifier_identity = _coding.classifier_identity
proposal_job = _coding.proposal_job
assessed_case = _coding.assessed_case
