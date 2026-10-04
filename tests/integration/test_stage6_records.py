"""Stage 6's committed records, checked from committed files alone (the Stage 6 spec,
§The codebook, §The coverage report, and §The gold): codebook v0 hashes to its
content hash, is approved, and is cited by ADR 0003; the coverage report hashes to
its own; codebook v0, the coverage report, and each gold file bind to the pin and
the split that the suite recomputes (plan 11, P11-2); and each gold file is named
for its event, codes against v0, agrees with its ``no_theme``, and holds together
by ID.

The local legs in ``test_stage6_pilot_v1.py`` recheck these records against the
pilot's documents and skip without ``data/``; this check needs no local store, so a
hand-edited record fails the default suite everywhere. Every assertion compares IDs,
labels, and hashes, bound before it is asserted (GS13).
"""

from pathlib import Path

from earnings_ingestion.events.coverage import load_coverage
from earnings_pipeline.stage6 import (
    CODEBOOK_FILE,
    PILOT_V1,
    PILOT_V1_HASH,
    UNIVERSE_V1,
    Layout,
    file_stem,
    load_pinned,
)
from earnings_themes.annotation import _ids
from earnings_themes.codebook import (
    CODEBOOK_ID,
    CODEBOOK_VERSION,
    CodebookStatus,
    codebook_hash,
    load_codebook,
)
from earnings_themes.gold import CodebookRef, load_gold, no_theme_of
from earnings_themes.split import load_split

REPO = Path(__file__).resolve().parents[2]
EVALUATION = REPO / "evaluation" / "djia-2024q3-2026q2" / "pilot-v1"
ADR = "docs/adr/0003-adopt-codebook-v0-as-the-pilot-codebook.md"


def test_codebook_v0_the_coverage_report_and_the_gold_hold_offline() -> None:
    pinned = load_pinned(Layout(REPO, UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH))
    split_hash = load_split(EVALUATION / "split-v1.json").content_hash
    codebook = load_codebook(REPO / CODEBOOK_FILE)
    stored = codebook.content_hash
    recomputed = codebook_hash(codebook)
    status = codebook.status
    adr = codebook.approval.adr if codebook.approval is not None else None
    cited = stored in (REPO / ADR).read_text(encoding="utf-8")
    corpus = codebook.discovery_corpus
    assert (recomputed, status, adr, cited, corpus.pin, corpus.split_hash) == (
        stored,
        CodebookStatus.APPROVED,
        ADR,
        True,
        pinned.pin,
        split_hash,
    )

    coverage = load_coverage(EVALUATION / "coverage-v1.json")
    assert coverage.pin == pinned.coverage_pin

    reference = CodebookRef(
        codebook_id=CODEBOOK_ID, codebook_version=CODEBOOK_VERSION, content_hash=stored
    )
    themes = codebook.theme_ids()
    paths = sorted((EVALUATION / "gold").glob("*.toml"))
    problems = []
    for path in paths:
        gold = load_gold(path)
        checks = {
            "file_stem": path.stem == file_stem(gold.event_id),
            "pin": gold.pin == pinned.pin,
            "split_hash": gold.split_hash == split_hash,
            "codebook": gold.codebook == reference,
            "no_theme": gold.no_theme == no_theme_of(gold.assignments),
        }
        problems += [f"{path.name}: {name}" for name, ok in checks.items() if not ok]
        refusals = _ids(
            gold.quotes, gold.claims, gold.assignments, gold.hard_negatives, themes, ""
        )
        problems += [f"{path.name}: {refusal}" for refusal in refusals]
    found = len(paths)
    assert found > 0
    assert problems == []
