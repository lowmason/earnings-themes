"""User-run Stage 11 smoke on one committed Stage 1 fixture; never a pilot reader."""

import argparse
import contextlib
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import tomllib
from earnings_core import canonical_json, digest, sha256_hex
from earnings_ingestion.canonical.serialize import from_fixture_json
from earnings_ingestion.fetch.store import write_new
from earnings_pipeline.model_runtime import (
    ChatModelFile,
    RuntimeManifest,
    build_runtime,
)
from earnings_pipeline.theme_config import confined_path
from earnings_themes.anchoring import Bundle
from earnings_themes.codebook import load_codebook
from earnings_themes.coding.cache import CodingCache
from earnings_themes.coding.records import CodingCeilings, CodingPolicy
from earnings_themes.coding.run import propose_run
from earnings_themes.extraction.cache import CachedAdapter
from earnings_themes.extraction.prompt import parse_template
from earnings_themes.extraction.records import Ceilings, ExtractionPolicy, Parameters
from earnings_themes.extraction.run import extract_run
from earnings_themes.extraction.store import StoredRun, write_run
from earnings_themes.records import Part, parse
from earnings_themes.support import assess_run, write_support_run
from earnings_themes.support.cache import SupportCache
from earnings_themes.support.records import (
    Presentation,
    SupportCeilings,
    SupportPolicy,
    SupportSources,
)

REASONS = frozenset(
    {
        "fixture_not_allowlisted",
        "fixture_not_committed",
        "output_exists",
        "judge_family_conflict",
        "extraction_incomplete_or_empty",
        "classification_incomplete_or_empty",
        "support_not_ready",
        "support_incomplete",
        "roles_not_exercised",
        "malformed_arguments",
        "smoke_failed",
    }
)


class SmokeRefused(ValueError):
    def __init__(self, reason):
        super().__init__(reason if reason in REASONS else "smoke_failed")


class Limits(Part):
    extraction_policy: ExtractionPolicy
    extraction_ceilings: Ceilings
    coding_parameters: Parameters
    coding_ceilings: CodingCeilings
    support_parameters: Parameters
    support_ceilings: SupportCeilings


def committed(repo, relative):
    path = confined_path(repo, relative)
    result = subprocess.run(
        ["git", "show", "HEAD:" + relative],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    data = path.read_bytes()
    if result.returncode != 0 or result.stdout != data:
        raise SmokeRefused("fixture_not_committed")
    return data


def panel(repo, manifest_path):
    manifest = parse(
        tomllib.loads(manifest_path.read_text()), RuntimeManifest, "runtime_manifest"
    )
    root = manifest_path.parent.relative_to(repo).as_posix()

    def chat(name):
        path = confined_path(repo, root + "/" + name, "config/models")
        return parse(tomllib.loads(path.read_text()), ChatModelFile, "chat_model")

    family = chat(manifest.extractor).family
    if chat(manifest.classifier).family != family:
        raise SmokeRefused("judge_family_conflict")
    judges = tuple(chat(name).family for name in manifest.judges)
    if len(set(judges)) != 2 or family in judges:
        raise SmokeRefused("judge_family_conflict")


class Measured:
    def __init__(self, delegate, role, calls, sink):
        self.delegate, self.role, self.calls, self.sink = delegate, role, calls, sink

    @property
    def identity(self):
        return self.delegate.identity

    def count_tokens(self, request):
        return self.delegate.count_tokens(request)

    def call(self, method, request):
        started = perf_counter()
        row = {"role": self.role, "call": len(self.calls) + 1}
        try:
            counted = (
                self.delegate.count_tokens(request)
                if hasattr(self.delegate, "count_tokens")
                else None
            )
            reply = getattr(self.delegate, method)(request)
            usage = getattr(reply, "usage", None)
            row.update(
                status="returned",
                local_input_tokens=counted,
                reported_input_tokens=(
                    usage.prompt_tokens
                    if usage
                    else getattr(reply, "input_tokens", None)
                ),
                reported_output_tokens=(usage.completion_tokens if usage else None),
            )
            return reply
        except Exception:
            row.update(status="failed")
            raise
        finally:
            row["elapsed_ms"] = max(0, round((perf_counter() - started) * 1000))
            self.calls.append(row)
            self.sink(row)

    def complete(self, request):
        return self.call("complete", request)

    def score(self, request):
        return self.call("score", request)


def smoke(
    repo,
    manifest,
    models_root,
    fixture_id,
    limits_path,
    run_id,
    *,
    builder=build_runtime,
    ready=None,
    sink=lambda row: None,
):
    repo = repo.resolve()
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", run_id) is None:
        raise SmokeRefused("malformed_arguments")
    allowed = tomllib.loads(
        committed(repo, "tests/fixtures/releases/manifest.toml").decode()
    )
    if fixture_id not in {row["fixture_id"] for row in allowed["fixtures"]}:
        raise SmokeRefused("fixture_not_allowlisted")
    fixture_rel = f"tests/fixtures/canonical/{fixture_id}.json"
    confined_path(repo, fixture_rel, "tests/fixtures/canonical")
    fixture = committed(repo, fixture_rel)
    manifest_path = confined_path(repo, manifest, "config/models")
    panel(repo, manifest_path)
    limits = Limits.model_validate_json(confined_path(repo, limits_path).read_bytes())
    output = confined_path(
        repo,
        "data/runs/stage11-fixture-smoke/" + run_id,
        "data/runs/stage11-fixture-smoke",
    )
    if output.exists():
        raise SmokeRefused("output_exists")
    extraction_text = committed(repo, "prompts/extraction/pointer-1.md").decode()
    coding_text = committed(repo, "prompts/coding/deductive-1.md").decode()
    support_text = committed(repo, "prompts/support/judge-1.md").decode()
    book_path = "codebooks/djia-pilot/codebook-v0.toml"
    book_bytes = committed(repo, book_path)
    book = load_codebook(repo / book_path)
    canonical = from_fixture_json(fixture.decode())
    bundle = Bundle(
        fixture_id, canonical.document, canonical.elements, canonical.masked.masks
    )
    software = {"lock_hash": sha256_hex(committed(repo, "uv.lock"))}
    started = datetime.now(timezone.utc)
    rt = builder(manifest_path, models_root)
    if len({j.identity.family for j in rt.workflow.judges}) != 2 or any(
        j.identity.family == rt.extractor_family for j in rt.workflow.judges
    ):
        raise SmokeRefused("judge_family_conflict")
    output.mkdir(parents=True, exist_ok=False)
    calls = []

    def measured(delegate, role):
        return Measured(delegate, role, calls, sink)

    identities = {
        "runtime_manifest": {
            "path": manifest,
            "sha256": sha256_hex(manifest_path.read_bytes()),
        },
        "extractor_family": rt.extractor_family,
        "extraction_identity": rt.workflow.extractor.identity.model_dump(mode="json"),
        "classifier_identity": rt.workflow.classifier.identity.model_dump(mode="json"),
        "scorer_identity": rt.workflow.scorer.identity.model_dump(mode="json"),
        "judge_identities": [
            j.identity.model_dump(mode="json") for j in rt.workflow.judges
        ],
        "alternative_scorer": rt.alternative_scorer.identity.model_dump(mode="json"),
    }
    write_new(output / "identities.json", canonical_json(identities))
    result = extract_run(
        (bundle,),
        CachedAdapter(
            measured(rt.workflow.extractor, "extractor"),
            output / "cache/extraction",
            "live",
        ),
        limits.extraction_policy,
        parse_template(extraction_text),
        limits.extraction_ceilings,
        run_id="stage11-fixture-extraction",
        started_at=started,
        software=software,
    )
    stored = StoredRun.of(result)
    write_run(output / "extraction", stored, (bundle,))
    if not stored.claims or any(
        d.outcome.value != "completed" for d in stored.documents
    ):
        raise SmokeRefused("extraction_incomplete_or_empty")
    sources = SupportSources(
        stored,
        (bundle,),
        book,
        digest(
            {
                "fixture_sha256": sha256_hex(fixture),
                "codebook_sha256": sha256_hex(book_bytes),
            }
        ),
    )
    proposal = propose_run(
        "stage11-fixture-classification",
        sources,
        tuple((claim.doc_id, claim.claim_id) for claim in stored.claims),
        measured(rt.workflow.classifier, "classifier"),
        CodingPolicy(
            prompt_text=coding_text,
            prompt_hash=sha256_hex(coding_text.encode()),
            parameters=limits.coding_parameters,
        ),
        limits.coding_ceilings,
        cache=CodingCache(output / "cache/coding", "live"),
        started_at=started,
        software=software,
    )
    if not proposal.targets or any(
        c.status != "completed" for c in proposal.classifications
    ):
        raise SmokeRefused("classification_incomplete_or_empty")
    if ready is None or not ready():
        raise SmokeRefused("support_not_ready")
    judges = tuple(
        measured(judge, role)
        for judge, role in zip(rt.workflow.judges, ("judge_a", "judge_b"), strict=True)
    )
    policy = SupportPolicy(
        support_version="semantic-support/1",
        prompt_text=support_text,
        prompt_hash=sha256_hex(support_text.encode()),
        parameters=limits.support_parameters,
    )
    primary = None
    for role, scorer in (
        ("minicheck", rt.workflow.scorer),
        ("deberta", rt.alternative_scorer),
    ):
        support = assess_run(
            "stage11-fixture-" + role,
            sources,
            proposal.targets,
            measured(scorer, role),
            judges,
            policy,
            limits.support_ceilings,
            extractor_family=rt.extractor_family,
            cache=SupportCache(output / "cache/support", "live"),
            started_at=started,
            software=software,
        )
        write_support_run(output / role, support, sources)
        if not support.assessments or any(
            a.outcome.status.value in {"incomplete", "refused"}
            for a in support.assessments
        ):
            raise SmokeRefused("support_incomplete")
        if role == "minicheck":
            primary = support
    expected = {
        (j.identity.family, presentation)
        for j in rt.workflow.judges
        for presentation in Presentation
    }
    actual = {
        (trial.identity.family, trial.presentation)
        for a in primary.assessments
        for trial in a.trials
        if trial.answer is not None
    }
    counts = Counter(row["role"] for row in calls if row["status"] == "returned")
    if not expected <= actual or set(counts) != {
        "extractor",
        "classifier",
        "judge_a",
        "judge_b",
        "minicheck",
        "deberta",
    }:
        raise SmokeRefused("roles_not_exercised")
    summary = {
        "status": "complete",
        "fixture_sha256": sha256_hex(fixture),
        "identities_sha256": sha256_hex(canonical_json(identities)),
        "role_calls": dict(sorted(counts.items())),
        "calls": calls,
    }
    write_new(output / "summary.json", canonical_json(summary))
    sink({key: value for key, value in summary.items() if key != "calls"})
    return summary


@contextlib.contextmanager
def private_diagnostics():
    """Suppress Python and native runtime output; only the explicit sink leaves."""
    sys.stdout.flush()
    sys.stderr.flush()
    saved = [os.dup(1), os.dup(2)]
    try:
        with (
            tempfile.TemporaryFile(mode="w+", encoding="utf-8") as diagnostics,
            contextlib.redirect_stdout(diagnostics),
            contextlib.redirect_stderr(diagnostics),
        ):
            os.dup2(diagnostics.fileno(), 1)
            os.dup2(diagnostics.fileno(), 2)
            try:
                yield
            finally:
                sys.stdout.flush()
                sys.stderr.flush()
    finally:
        for descriptor, original in zip((1, 2), saved, strict=True):
            os.dup2(original, descriptor)
            os.close(original)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise SmokeRefused("malformed_arguments")


def main(argv=None):
    with os.fdopen(os.dup(1), "w", buffering=1) as console:

        def sink(row):
            console.write(canonical_json(row).decode() + "\n")

        def ready():
            console.write("checkpoint: unload Gemma, load both judges; type ready\n")
            console.flush()
            return sys.stdin.readline().strip() == "ready"

        try:
            parser = Parser()
            for name in ("manifest", "models-root", "fixture-id", "limits", "run-id"):
                parser.add_argument("--" + name, required=True)
            args = parser.parse_args(argv)
            with private_diagnostics():
                smoke(
                    Path(__file__).resolve().parents[1],
                    args.manifest,
                    Path(args.models_root),
                    args.fixture_id,
                    args.limits,
                    args.run_id,
                    ready=ready,
                    sink=sink,
                )
            return 0
        except SmokeRefused as error:
            sink({"status": "refused", "reason": str(error)})
        except Exception:  # noqa: BLE001 - arbitrary runtime diagnostics must stay private
            sink({"status": "refused", "reason": "smoke_failed"})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
