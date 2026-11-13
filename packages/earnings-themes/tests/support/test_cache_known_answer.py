"""Known-answer pin for the support and coding cache keys (plan 23, Task 1).

Each cache entry is named ``<sha256>.json``, so the names of the files that the
invented ``assessed_case`` path writes are the key digests. A performance change
must reproduce every one of them, or train's cached entries stop replaying
(D21-34). Invented text only (GS13).
"""

from importlib import import_module

_coding = import_module("packages.earnings-themes.tests.coding.conftest")

coding_case = _coding.coding_case
coding_policy = _coding.coding_policy
classifier_identity = _coding.classifier_identity
proposal_job = _coding.proposal_job
assessed_case = _coding.assessed_case

SUPPORT_CACHE_NAMES = [
    "0fb9994341653e9b5d25169e194bd8aa485d2fa7f2176e8789e955d03eccbad6.json",
    "1979ba4f0ec531ee30f671beef8dfaac8a9b4433734c5d468c94d5f5c3d876ca.json",
    "42d407e82d7a67c3941428fc289e8250580455fdc3d8d3e9fbb738213b12887b.json",
    "eff73d9b807974877fa88d87bb855232e3c447185aec76141cb9777b3383dde9.json",
    "f1c20e341ca5b38f8d905075d14818b06640d637796f3d481ed8897529d0b8af.json",
]
CLASSIFIER_CACHE_NAMES = [
    "fbf84b88c0c7608fb8a8822a8df06643856606318ee0792c6d0b47127801487c.json",
]


def test_support_and_coding_cache_names_are_pinned(assessed_case, tmp_path):
    support = sorted(p.name for p in (tmp_path / "support-cache").rglob("*.json"))
    classifier = sorted(p.name for p in (tmp_path / "classifier-cache").rglob("*.json"))
    assert support == SUPPORT_CACHE_NAMES
    assert classifier == CLASSIFIER_CACHE_NAMES
