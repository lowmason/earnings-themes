"""Plan 21 B6 / plan 23: per-lookup cost at real cache-key size (invented text only).

Invented documents of real length: D documents x P one-sentence paragraph
elements, with about one claim per document. The support-cache key embeds every
bundle, claim and quote, so its size tracks the documents, not the claim count.
The codebook holds N invented themes (`--themes N`, default 22, as codebook v0).
Prints sizes, counts and seconds only: one line per phase, then the per-unit costs.

Usage (from the worktree root):
  uv run --locked --all-packages python expirements/run-path-performance/realsize.py 20 1850 --themes 22
  ... --themes 22 --project   # also print the projected train `pilot run` time
"""

import argparse
import importlib.util
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
spec = importlib.util.spec_from_file_location(
    "scaling", Path(__file__).with_name("scaling.py")
)
scaling = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scaling)

from datetime import UTC, datetime

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    TextSpan,
    digest,
    sha256_hex,
)
from earnings_themes.anchoring import Bundle
from earnings_themes.coding.cache import CodingCache
from earnings_themes.coding.decide import decide_assignments
from earnings_themes.coding.records import CodingPolicy
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
from earnings_themes.support import (
    read_support_run,
    write_support_run,
)
from earnings_themes.support.cache import SupportCache
from earnings_themes.support.records import SupportSources
from earnings_themes.support.store import reverify_support_run

SENTENCE = "Invented Lumen widgets shipped {i} units in an invented quarter."

# Train's size (D21-34, P21-1) and plan 23 Task 7's projection formula.
TRAIN_CLAIMS = 1171
TRAIN_SUPPORT_ENTRIES = 7800
TRAIN_JUDGE_ENTRIES = 4866
TRAIN_TARGETS = 1170
REPLAY_PASSES = 2
LOAD_SECONDS = 32 * 60  # `load_pass`, measured before plan 23: an upper bound
# Gate counts over one tiny `make_run`, after plan 23. The first three are pinned
# by apps/earnings-pipeline/tests/test_pilot_gate_counts.py (sweeps are
# `_cache_verification` calls, the third is `_reverify_support_run`). The decide
# count was counted over the same `make_run` helpers by a scratch test that
# patched every module name bound to `decide_assignments`.
SWEEPS = 12
DECIDES = 9
REVERIFY_CALLS = 25
REVERIFY_PER_DECIDE = 2  # one `decide_assignments` call reverifies twice (Task 4)


def bundle(doc, paragraphs):
    parts, spans, at = [], [], 0
    for i in range(paragraphs):
        s = SENTENCE.format(i=i)
        parts.append(s)
        spans.append((at, at + len(s)))
        at += len(s) + 2
    text = "\n\n".join(parts)
    document = CanonicalDocument.create(
        source_document_id=f"invented-real-{doc}",
        canonicalization_version="invented-1",
        canonical_text=text,
    )
    elements = tuple(
        DocumentElement.create(
            document, ElementType.PARAGRAPH, TextSpan(start=a, end=b)
        )
        for a, b in spans
    )
    return Bundle(f"invented-real-{doc}", document, elements, ())


def sources(book, template, docs, paragraphs, every):
    bundles = tuple(bundle(d, paragraphs) for d in range(docs))
    count = {"n": 0}

    def reply(request):
        count["n"] += 1
        claims = (
            [{"quote_labels": ["U1", "U2"], "claim": f"Invented claim {count['n']}."}]
            if (count["n"] - 1) % every == 0
            else []
        )
        return ModelReply(text=json.dumps({"candidates": claims}), model="scripted")

    result = extract_run(
        bundles,
        ScriptedAdapter(reply),
        ExtractionPolicy(),
        template,
        Ceilings(
            requests_per_document=10**6,
            requests_per_run=10**9,
            tokens_per_run=10**12,
        ),
        run_id="invented-extraction",
        started_at=datetime(2026, 10, 5, tzinfo=UTC),
        software={"fixture": "1"},
    )
    return SupportSources(
        StoredRun.of(result), bundles, book, digest("invented provenance")
    ), count["n"]


def project(per_unit, sweeps=SWEEPS, decides=DECIDES):
    """The plan's terms for one train `pilot run`: (label, seconds) pairs.

    `per_unit` holds the four measured costs, in seconds. The terms are plan 23
    Task 7's formula: proposal replay and support replay, each over 2 passes; the
    raw-cache sweeps of the judge entries; the decide calls; and the load.
    """
    return [
        (
            f"proposal replay: {TRAIN_CLAIMS} claims x {REPLAY_PASSES} passes",
            TRAIN_CLAIMS * per_unit["proposal replay, per claim"] * REPLAY_PASSES,
        ),
        (
            f"support replay: {TRAIN_SUPPORT_ENTRIES} entries x {REPLAY_PASSES} passes",
            TRAIN_SUPPORT_ENTRIES
            * per_unit["support replay, per support entry"]
            * REPLAY_PASSES,
        ),
        (
            f"raw-cache sweeps: {sweeps} x {TRAIN_JUDGE_ENTRIES} judge entries",
            sweeps * TRAIN_JUDGE_ENTRIES * per_unit["artifact_hash, per judge entry"],
        ),
        (
            f"decide: {decides} calls x {TRAIN_TARGETS} targets",
            decides * TRAIN_TARGETS * per_unit["decide_assignments, per target"],
        ),
        ("load (measured before plan 23, an upper bound)", LOAD_SECONDS),
    ]


def hours(seconds):
    return f"{seconds / 3600:7.2f} h"


def print_terms(title, terms):
    print(title)
    for label, seconds in terms:
        print(f"  {label:<60} {seconds:11.0f} s {hours(seconds)}")
    total = sum(seconds for _, seconds in terms)
    print(f"  {'total':<60} {total:11.0f} s {hours(total)}", flush=True)
    return total


def extra_terms(extra, n, scaled=False):
    """Costs the plan's formula leaves out, from the same measured run.

    One `decide_assignments` call reverifies the support run twice, and the decide
    term already prices those calls. So only the other `_reverify_support_run`
    calls are extra. `n` is the number of targets the one reverify call covered.
    With `scaled`, each of them is priced as growing linearly with the targets.
    """
    own = REVERIFY_CALLS - REVERIFY_PER_DECIDE * DECIDES
    grow = TRAIN_TARGETS / n if scaled else 1
    return [
        (
            f"classifier-cache sweeps: {SWEEPS} x {TRAIN_CLAIMS} entries",
            SWEEPS * TRAIN_CLAIMS * extra["classifier artifact_hash, per entry"],
        ),
        (
            f"reverify_support_run outside decide: {own} calls at {n} targets"
            + (f", x {grow:.1f}" if scaled else ""),
            own * extra["reverify_support_run, per call"] * grow,
        ),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("docs", type=int, help="documents")
    parser.add_argument("paragraphs", type=int, help="paragraph elements per document")
    parser.add_argument(
        "every", type=int, nargs="?", default=0, help="claim every N windows"
    )
    parser.add_argument("--themes", type=int, default=scaling.DEFAULT_THEMES)
    parser.add_argument(
        "--project",
        action="store_true",
        help="print the projected train `pilot run` time from the measured costs",
    )
    args = parser.parse_args()
    docs, paragraphs, every = args.docs, args.paragraphs, args.every
    book = scaling.codebook(args.themes)
    template = parse_template(
        Path("prompts/extraction/pointer-1.md").read_text("utf-8")
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        start = time.perf_counter()
        # One window per ~60 paragraphs; aim for about one claim per document.
        windows = max(1, paragraphs * 66 // 4000)
        src, requests = sources(book, template, docs, paragraphs, every or windows)
        n = len(src.stored_run.claims)
        print(
            f"build: docs={docs} paragraphs/doc={paragraphs} themes={len(book.themes)} "
            f"extraction_requests={requests} claims={n} "
            f"quotes={len(src.stored_run.quotes)} {time.perf_counter() - start:.1f} s",
            flush=True,
        )
        text = "Classify invented claims using only supplied frozen theme IDs."
        policy = CodingPolicy(
            prompt_text=text,
            prompt_hash=sha256_hex(text.encode("utf-8")),
            parameters=Parameters(max_tokens=64),
        )
        job = scaling.cases.make_proposal_job(src, policy, scaling.identity(), root)
        reply = {"theme_ids": ["capacity"], "attributes": {}}
        proposals, _ = scaling.timed(
            "propose live",
            n,
            lambda: job.run([reply] * n, ceilings=scaling.CODING_CEILINGS),
        )
        coding_files = list((root / "classifier-cache").rglob("*.json"))
        print(
            f"coding cache: {len(coding_files)} entries, largest "
            f"{max((p.stat().st_size for p in coding_files), default=0) / 1e6:.2f} MB"
        )
        coding_cache = CodingCache(root / "classifier-cache", "replay")
        start = time.perf_counter()
        for path in coding_files:
            coding_cache.artifact_hash(path.name)
        extra = {
            "classifier artifact_hash, per entry": (time.perf_counter() - start)
            / max(1, len(coding_files))
        }
        scaling.timed(
            "propose replay",
            n,
            lambda: job.run([], "replay", ceilings=scaling.CODING_CEILINGS),
        )
        result = scaling.timed(
            "assess live", n, lambda: scaling.assess(src, proposals, root, "live")
        )
        files = sorted((root / "support-cache").rglob("*.json"))
        sizes = [p.stat().st_size for p in files]
        print(
            f"support cache: {len(files)} entries, mean "
            f"{sum(sizes) / len(sizes) / 1e6:.2f} MB, largest {max(sizes) / 1e6:.2f} MB"
        )
        start = time.perf_counter()
        scaling.assess(src, proposals, root, "replay")
        took = time.perf_counter() - start
        print(
            f"assess replay              n={n:<6} {took:9.2f} s  "
            f"= {took / len(files):.2f} s per support entry",
            flush=True,
        )
        per_unit = {
            "proposal replay, per claim": scaling.ELAPSED["propose replay"] / n,
            "support replay, per support entry": took / len(files),
        }
        cache = SupportCache(root / "support-cache", "replay")
        judge = [p for p in files if json.loads(p.read_bytes())["kind"] == "judge"]
        start = time.perf_counter()
        sampled = judge[:5]
        for path in sampled:
            cache.artifact_hash(path.name)
        each = (time.perf_counter() - start) / len(sampled)
        print(f"artifact_hash (judge entry)  {each:9.2f} s each", flush=True)
        per_unit["artifact_hash, per judge entry"] = each
        scaling.timed(
            "write support",
            n,
            lambda: write_support_run(root / "support", result, src),
        )
        stored = scaling.timed(
            "read support", n, lambda: read_support_run(root / "support")
        )
        scaling.timed(
            "reverify_support_run",
            n,
            lambda: reverify_support_run(stored, src),
        )
        scaling.timed(
            "decide (no policy)",
            n,
            lambda: decide_assignments(proposals, stored, src, None),
        )
        per_unit["decide_assignments, per target"] = scaling.ELAPSED[
            "decide (no policy)"
        ] / len(proposals.targets)
        extra["reverify_support_run, per call"] = scaling.ELAPSED[
            "reverify_support_run"
        ]
        print("per-unit costs (floors, in seconds):")
        for name, seconds in per_unit.items():
            print(f"  {name:<36} {seconds:9.3f} s")
        print("per-unit costs not in the plan's formula (floors, in seconds):")
        for name, seconds in extra.items():
            print(f"  {name:<36} {seconds:9.3f} s")
        if args.project:
            print()
            plan = print_terms(
                f"projected train `pilot run` ({SWEEPS} sweeps, {DECIDES} decides),"
                " the plan's formula:",
                project(per_unit),
            )
            measured = print_terms(
                "not in the plan's formula, measured as it is:",
                extra_terms(extra, n),
            )
            scaled = print_terms(
                "not in the plan's formula, reverify calls scaled to train's targets"
                " (extrapolated):",
                extra_terms(extra, n, scaled=True),
            )
            print(f"total, the plan's formula {hours(plan)}")
            print(
                f"total, plan formula + measured extra terms {hours(plan + measured)}"
            )
            print(
                "total, plan formula + extra terms with scaled reverify "
                f"{hours(plan + scaled)}",
                flush=True,
            )


if __name__ == "__main__":
    main()
