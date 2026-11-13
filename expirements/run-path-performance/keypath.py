"""Plan 24: the cost of one support-cache key at real size (invented text only).

Builds the invented source of `realsize.py`: D documents x P one-sentence
paragraph elements, with a claim every N extraction windows. Then it builds the
cache key of one claim and prints one line per phase, in milliseconds, best of 3:
the key build (`scorer_key`), `SupportCacheKey(material)`, `_binding_once` and
`_material_kind` on a fresh key text, `artifact_hash` of one judge entry, and
that entry's parse. It ends with the byte size of each top-level value of the key.
Only one claim gets a cache entry, so the run is short. It sends no request.

Usage (from the worktree root):
  uv run --locked --all-packages python expirements/run-path-performance/keypath.py 20 1850 --themes 22
  ... --themes 22 --every 1   # a claim in every window, about 620 claims
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
    "realsize", Path(__file__).with_name("realsize.py")
)
realsize = importlib.util.module_from_spec(spec)
spec.loader.exec_module(realsize)
scaling = realsize.scaling

from earnings_core import canonical_json
from earnings_themes.extraction.adapters import ModelReply
from earnings_themes.extraction.prompt import parse_template
from earnings_themes.support import cache as cache_module
from earnings_themes.support.cache import (
    SupportCache,
    SupportCacheEntry,
    SupportCacheKey,
    judge_key,
    scorer_key,
)
from earnings_themes.support.prompt import render_judge
from earnings_themes.support.records import (
    CodebookReference,
    Presentation,
    ResolvedInput,
    Target,
)
from earnings_themes.support.resolve import resolve_target
from earnings_themes.support.scorers import score_requests

REPS = 3


def forget_text_memos():
    """A key of a new text meets no per-text memo. Other memos stay as they are."""
    cache_module._binding_once.cache_clear()
    cache_module._material_kind.cache_clear()


def best(label, call, *, before=None):
    """Print the best of `REPS` runs of `call`, in ms; return its last value."""
    took = float("inf")
    for _ in range(REPS):
        if before is not None:
            before()
        start = time.perf_counter()
        value = call()
        took = min(took, time.perf_counter() - start)
    print(f"  {label:<52} {took * 1000:9.1f} ms", flush=True)
    return value


def resolved_input(src):
    """The first claim of the source, paired with the codebook's first theme."""
    claim = src.stored_run.claims[0]
    book = src.codebook
    target = Target(
        source_run_id=src.stored_run.record.run_id,
        doc_id=claim.doc_id,
        claim_id=claim.claim_id,
        theme_id=book.themes[0].theme_id,
        codebook=CodebookReference(
            codebook_id=book.codebook_id,
            codebook_version=book.codebook_version,
            content_hash=book.content_hash,
        ),
    )
    resolved = resolve_target(
        src.stored_run,
        src.bundles,
        book,
        target,
        provenance_hash=src.provenance_hash,
    )
    assert isinstance(resolved, ResolvedInput)
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("docs", type=int, help="documents")
    parser.add_argument("paragraphs", type=int, help="paragraph elements per document")
    parser.add_argument("--themes", type=int, default=scaling.DEFAULT_THEMES)
    parser.add_argument(
        "--every",
        type=int,
        default=0,
        help="claim every N windows (default: about one claim per document)",
    )
    args = parser.parse_args()
    docs, paragraphs = args.docs, args.paragraphs
    book = scaling.codebook(args.themes)
    template = parse_template(
        Path("prompts/extraction/pointer-1.md").read_text("utf-8")
    )
    windows = max(1, paragraphs * 66 // 4000)
    start = time.perf_counter()
    src, requests = realsize.sources(
        book, template, docs, paragraphs, args.every or windows
    )
    print(
        f"build: docs={docs} paragraphs/doc={paragraphs} themes={len(book.themes)} "
        f"extraction_requests={requests} claims={len(src.stored_run.claims)} "
        f"quotes={len(src.stored_run.quotes)} {time.perf_counter() - start:.1f} s",
        flush=True,
    )
    resolved = resolved_input(src)
    scorer, panel = scaling.cases.make_support_parts()
    policy = scaling.support_policy()
    request = score_requests(resolved)[0][1]
    judge_request = render_judge(resolved, policy, Presentation.EVIDENCE_FIRST)
    with tempfile.TemporaryDirectory() as tmp:
        cache = SupportCache(Path(tmp) / "support-cache", "live")
        entry_key = judge_key(resolved, judge_request, panel[0].identity, policy)
        name = cache.put(entry_key, ModelReply(text="{}", model="scripted"))
        path = Path(tmp) / "support-cache" / name
        print(
            f"entry: {path.stat().st_size / 1e6:.2f} MB on disk, "
            f"one judge entry for one claim",
            flush=True,
        )
        print("phases for one key, best of 3 (floors, in ms):")
        key = best(
            "key build: scorer_key (fresh text)",
            lambda: scorer_key(resolved, request, scorer.identity, policy),
            before=forget_text_memos,
        )
        material = key.material
        print(f"  key material: {len(material.encode()) / 1e6:.2f} MB")
        best("SupportCacheKey(material)", lambda: SupportCacheKey(material))
        best(
            "_binding_once (fresh text)",
            lambda: cache_module._binding_once(str(key), material, "scorer"),
            before=forget_text_memos,
        )
        best(
            "_material_kind (fresh text)",
            lambda: cache_module._material_kind(material),
            before=forget_text_memos,
        )
        best(
            "artifact_hash, one judge entry (fresh text)",
            lambda: cache.artifact_hash(name),
            before=forget_text_memos,
        )
        best(
            "artifact_hash, one judge entry (text memos warm)",
            lambda: cache.artifact_hash(name),
        )
        best(
            "entry parse: SupportCacheEntry.model_validate_json",
            lambda: SupportCacheEntry.model_validate_json(path.read_bytes()),
        )
    sizes = {k: len(canonical_json(v)) for k, v in json.loads(material).items()}
    total = sum(sizes.values())
    print(f"top-level value sizes, bytes (sum {total}):")
    for field, size in sorted(sizes.items(), key=lambda item: -item[1]):
        print(f"  {field:<18} {size:>10} {100 * size / total:6.2f} %")


if __name__ == "__main__":
    main()
