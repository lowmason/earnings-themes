"""Plan 21 B6 / plan 23: per-lookup cost at real cache-key size (invented text only).

Invented documents of real length: D documents x P one-sentence paragraph
elements, with about one claim per document. The support-cache key embeds every
bundle, claim and quote, so its size tracks the documents, not the claim count.
Prints sizes, counts and seconds only.

Usage (from the worktree root):
  uv run --locked --all-packages python expirements/run-path-performance/realsize.py 20 1850
"""

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


def main():
    docs, paragraphs = int(sys.argv[1]), int(sys.argv[2])
    every = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    book = scaling.codebook()
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
            f"build: docs={docs} paragraphs/doc={paragraphs} extraction_requests="
            f"{requests} claims={n} quotes={len(src.stored_run.quotes)} "
            f"{time.perf_counter() - start:.1f} s",
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
        cache = SupportCache(root / "support-cache", "replay")
        judge = [p for p in files if json.loads(p.read_bytes())["kind"] == "judge"]
        start = time.perf_counter()
        for path in judge[:5]:
            cache.artifact_hash(path.name)
        print(
            f"artifact_hash (judge entry)  {(time.perf_counter() - start) / 5:9.2f} s each",
            flush=True,
        )
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


if __name__ == "__main__":
    main()
