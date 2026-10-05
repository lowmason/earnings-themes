"""One fixture end to end through the local model (the Stage 7 spec, §Verification;
R14.1, R14.6): extracted live into a fresh cache, stored, read back, every quote
verified again, and replayed from the cache with no request.

It runs once, at plan B's gate, by its node ID with ``-m live``, after ADR 0004 and
``config/models/local-model.toml`` record the model. It skips visibly when no model
is configured or no server answers. It prints counts and IDs only (GS13)."""

import importlib.metadata
import platform
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from earnings_core import VerifiedSpan, reverify_span
from earnings_themes.extraction.cache import CachedAdapter, CacheMode
from earnings_themes.extraction.local import (
    LocalAdapter,
    load_local_config,
    loopback_url,
)
from earnings_themes.extraction.records import (
    Ceilings,
    ExtractionPolicy,
    Parameters,
    WindowOutcome,
)
from earnings_themes.extraction.run import RunResult, extract_run
from earnings_themes.extraction.store import StoredRun, read_run, write_run

pytestmark = pytest.mark.live

REPO = Path(__file__).resolve().parents[3]
CONFIG = REPO / "config" / "models" / "local-model.toml"
FIXTURE = "0000877860-13-000100_ex-99-1"
"""The fixture with the fewest units: 45, in 2 windows."""
CEILINGS = Ceilings(requests_per_document=4, requests_per_run=4, tokens_per_run=100_000)
"""2 windows, at most 2 attempts each."""


def test_one_fixture_runs_end_to_end_through_the_local_model(
    fixtures, template, tmp_path: Path
) -> None:
    if not CONFIG.is_file():
        pytest.skip(f"no local model is configured at {CONFIG.relative_to(REPO)}")
    config = load_local_config(CONFIG)
    try:
        with httpx.Client(timeout=5, trust_env=False) as client:
            client.get(f"{loopback_url(config.base_url)}/models").raise_for_status()
    except httpx.HTTPError:
        pytest.skip(f"no server answers at {config.base_url}")
    bundle = fixtures[FIXTURE]
    policy = ExtractionPolicy(parameters=Parameters(structured=config.structured))
    software = {
        "earnings-themes": importlib.metadata.version("earnings-themes"),
        "httpx": httpx.__version__,
        "python": platform.python_version(),
    }

    def run(mode: CacheMode) -> RunResult:
        adapter = CachedAdapter(LocalAdapter(config), tmp_path / "cache", mode)
        return extract_run(
            [bundle],
            adapter,
            policy,
            template,
            CEILINGS,
            run_id=f"live-{mode}",
            started_at=datetime.now(UTC),
            software=software,
        )

    live = run(CacheMode.LIVE)
    stored = StoredRun.of(live)
    again = read_run(write_run(tmp_path / "run", stored, [bundle]))
    assert again == stored
    for quote in again.quotes:
        verified = reverify_span(bundle.document, bundle.elements, quote.span)
        assert isinstance(verified, VerifiedSpan)
    record = live.record
    assert (record.windows, record.units, record.exhausted) == (2, 45, False)
    assert {w.outcome for w in live.windows} == {WindowOutcome.COMPLETED}
    replayed = run(CacheMode.REPLAY)

    def content(result: RunResult) -> list[tuple[str, str, tuple[str, ...]]]:
        return [(c.window_id, c.claim, c.quote_ids) for c in result.claims]

    assert (replayed.record.requests, replayed.quotes) == (0, live.quotes)
    assert content(replayed) == content(live)
    print(
        f"{FIXTURE}: windows {record.windows}, requests {record.requests},"
        f" prompt tokens {record.prompt_tokens}, completion tokens"
        f" {record.completion_tokens}, unreported {record.unreported},"
        f" quotes {record.quotes}, claims {record.claims},"
        f" rejections {record.rejections_by_reason}"
    )
