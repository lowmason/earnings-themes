"""Plan 21 B6 / plan 23 run-path scaling (invented text only, no pilot data).

Builds D documents x M claims through the real extraction, coding and support
seams with scripted adapters, then times the phases `pilot run` repeats at train
scale: replay of proposals and support, support write/read, proposal-support
validation, decisions, and the coding run's write (validate + reverify), read and
reverify. Prints phase names, sizes and seconds only.

Usage (from the worktree root):
  uv run --locked --all-packages python expirements/run-path-performance/scaling.py 20 2 4 8
"""

import importlib
import json
import sys
import tempfile
import time
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path.cwd()))

from earnings_core import digest, sha256_hex
from earnings_themes.codebook import (
    Approval,
    CodebookDraft,
    freeze_codebook,
)
from earnings_themes.coding import validate_proposal_support
from earnings_themes.coding.decide import decide_assignments
from earnings_themes.coding.records import CodingCeilings, CodingPolicy
from earnings_themes.coding.store import (
    read_coding_run,
    reverify_coding_run,
    write_coding_run,
)
from earnings_themes.extraction.adapters import (
    ModelReply,
    ScriptedAdapter,
)
from earnings_themes.extraction.prompt import parse_template
from earnings_themes.extraction.records import (
    Ceilings,
    ExtractionPolicy,
    Parameters,
)
from earnings_themes.extraction.run import extract_run
from earnings_themes.extraction.store import StoredRun
from earnings_themes.records import parse
from earnings_themes.support import (
    assess_run,
    read_support_run,
    write_support_run,
)
from earnings_themes.support.cache import SupportCache
from earnings_themes.support.records import (
    JudgeIdentity,
    RuntimeIdentity,
    SupportCeilings,
    SupportPolicy,
    SupportSources,
)
from earnings_themes.synthetic import (
    DEV,
    LATER,
    PIN,
    TEST,
    TRAIN,
    build_synthetic,
    codebook_draft,
    synthetic_split,
)

cases = importlib.import_module("packages.earnings-themes.tests.coding.cases")
REPO = Path.cwd()
BIG = 10**9


def codebook():
    made = freeze_codebook(
        parse(codebook_draft(), CodebookDraft, "draft"),
        pin=PIN,
        split=synthetic_split(),
        bundles={e: build_synthetic(e).bundle for e in (TRAIN, DEV, TEST, LATER)},
        approval=Approval(
            approver="fixture",
            approved_on=date(2026, 10, 2),
            adr="docs/adr/0003-approve-pilot-codebook-v0.md",
        ),
    )
    return cases.invented_codebook(made)


def sources(book, template, docs, claims):
    bundles = tuple(cases.invented_bundle(f"invented-scale-{i}") for i in range(docs))
    texts = [f"An invented operating claim number {j}." for j in range(claims)]
    adapter = ScriptedAdapter(
        lambda request: ModelReply(
            text=json.dumps(
                {"candidates": [{"quote_labels": ["U1"], "claim": t} for t in texts]}
            ),
            model="scripted",
        )
    )
    result = extract_run(
        bundles,
        adapter,
        ExtractionPolicy(),
        template,
        Ceilings(requests_per_document=2, requests_per_run=BIG, tokens_per_run=BIG),
        run_id="invented-extraction",
        started_at=datetime(2026, 10, 5, tzinfo=UTC),
        software={"fixture": "1"},
    )
    return SupportSources(
        StoredRun.of(result), bundles, book, digest("invented provenance")
    )


def identity():
    return JudgeIdentity(
        family="invented-classifier-family",
        runtime=RuntimeIdentity(
            model_id="invented-classifier",
            revision="fixture-1",
            files=(),
            runtime="scripted",
            runtime_version="1",
            device="cpu",
            precision="float32",
            encoding_version="fixture-1",
        ),
        input_limit=10000,
        output_limit=2048,
        hosting="scripted",
        weight_license=None,
    )


def support_policy():
    prompt = (REPO / "prompts/support/judge-1.md").read_text(encoding="utf-8")
    return SupportPolicy(
        support_version="semantic-support/1",
        prompt_text=prompt,
        prompt_hash=sha256_hex(prompt.encode("utf-8")),
        parameters=Parameters(max_tokens=64),
    )


SUPPORT_CEILINGS = SupportCeilings(
    scorer_per_target=40,
    scorer_per_document=BIG,
    scorer_per_run=BIG,
    judge_per_target=40,
    judge_per_document=BIG,
    judge_per_run=BIG,
    tokens_per_document=BIG,
    tokens_per_run=BIG,
)
CODING_CEILINGS = CodingCeilings(
    requests_per_claim=2,
    requests_per_document=BIG,
    requests_per_run=BIG,
    tokens_per_document=BIG,
    tokens_per_run=BIG,
)


def assess(src, proposals, root, mode):
    scorer, panel = cases.make_support_parts(replay=mode == "replay")
    return assess_run(
        "invented-support-run",
        src,
        proposals.targets,
        scorer,
        panel,
        support_policy(),
        SUPPORT_CEILINGS,
        extractor_family="invented-extractor",
        cache=SupportCache(root / "support-cache", mode),
        started_at=datetime(2026, 10, 5, tzinfo=UTC),
        software={"fixture": "1", "lock_hash": digest("invented lock")},
    )


def timed(label, n, fn):
    start = time.perf_counter()
    value = fn()
    print(f"{label:<28} n={n:<6} {time.perf_counter() - start:9.2f} s", flush=True)
    return value


def one(book, template, docs, claims):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        text = "Classify invented claims using only supplied frozen theme IDs."
        policy = CodingPolicy(
            prompt_text=text,
            prompt_hash=sha256_hex(text.encode("utf-8")),
            parameters=Parameters(max_tokens=64),
        )
        src = sources(book, template, docs, claims)
        n = len(src.stored_run.claims)
        job = cases.make_proposal_job(src, policy, identity(), root)
        reply = {"theme_ids": ["capacity"], "attributes": {}}
        proposals, _ = timed(
            "propose live",
            n,
            lambda: job.run([reply] * n, ceilings=CODING_CEILINGS),
        )
        timed(
            "propose replay",
            n,
            lambda: job.run([], "replay", ceilings=CODING_CEILINGS),
        )
        result = timed("assess live", n, lambda: assess(src, proposals, root, "live"))
        timed("assess replay", n, lambda: assess(src, proposals, root, "replay"))
        timed(
            "write support",
            n,
            lambda: write_support_run(root / "support", result, src),
        )
        stored = timed("read support", n, lambda: read_support_run(root / "support"))
        timed(
            "validate proposal-support",
            n,
            lambda: validate_proposal_support(proposals, stored, src),
        )
        timed(
            "decide (no policy)",
            n,
            lambda: decide_assignments(proposals, stored, src, None),
        )
        case = SimpleNamespace(
            proposals=proposals,
            sources=src,
            support=stored,
            decide=lambda policy=None: decide_assignments(
                proposals, stored, src, policy
            ),
        )
        coding = cases.make_coding_run(case, None)
        timed(
            "write coding",
            n,
            lambda: write_coding_run(root / "coding", coding, src, stored, None),
        )
        read = timed("read coding", n, lambda: read_coding_run(root / "coding"))
        timed(
            "reverify coding",
            n,
            lambda: reverify_coding_run(read, src, stored, None),
        )


def main():
    docs = int(sys.argv[1])
    book = codebook()
    template = parse_template(
        (REPO / "prompts/extraction/pointer-1.md").read_text(encoding="utf-8")
    )
    for claims in (int(a) for a in sys.argv[2:]):
        one(book, template, docs, claims)


if __name__ == "__main__":
    main()
