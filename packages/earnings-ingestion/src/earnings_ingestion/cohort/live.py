"""The opt-in live verification (P-VL): re-read every source the cohort relies on.

- **Terms.** Each cited source's terms page is fetched and hashed the way the
  register hashes it. A different hash is ``changed``: a person rereads the terms,
  then records it in the register's ``terms_sha256`` and ``last_verified``.
- **Evidence.** Each curated snapshot and change page is fetched again. A page whose
  bytes differ from the saved artifact is ``changed``; the saved bytes remain the
  evidence, and the difference is for a person to read. A page that robots.txt
  disallows is ``refused``. A persistent 403 or block page is ``refused`` too, and the
  client that met it sends nothing more (A §404).
- **Rebuild.** The cohort is rebuilt from the saved artifacts, which parses the dated
  evidence and reconciles the official changes against the corroborating snapshots,
  and its content hash is compared with the latest frozen manifest's.

SEC hosts go through the shared SEC client and every other host through the web
client, and each check keeps its retrieval metadata. Each client is capped at the
count the user approved, and the record keeps the requests both sent (PR #6's review,
F35). Nothing here runs in the default suite.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from earnings_ingestion.cohort.acquire import HTML, PDF, terms_digest
from earnings_ingestion.cohort.build import COHORT_STORE, CohortError, build
from earnings_ingestion.cohort.config import UNIVERSE_DIR, load_cohort_config
from earnings_ingestion.cohort.freeze import frozen_manifests
from earnings_ingestion.cohort.records import LiveCheck, LiveVerification
from earnings_ingestion.cohort.register import (
    MEMBERSHIP_REGISTER,
    SEC_REGISTER,
    load_registers,
)
from earnings_ingestion.cohort.web import RobotsRefusal, open_web_client
from earnings_ingestion.fetch.client import AccessStop, Fetched, UnexpectedResponse
from earnings_ingestion.fetch.store import write_new
from earnings_ingestion.sec.client import open_sec_client
from earnings_ingestion.sec.urls import is_sec_host

Fetch = Callable[[str, frozenset[str]], Fetched]
LIVE_RUNS = Path("data") / "runs" / "cohort" / "live"
ANY = frozenset({"text/html", "text/plain", "application/json", "application/pdf"})


def _targets(
    repo: Path, options: Mapping[str, Path]
) -> list[tuple[str, str, str, str | None]]:
    """(source_id, purpose, url, expected hash) for every live request, in order."""
    config = load_cohort_config(repo / options["config_dir"])
    registers = load_registers(repo, options["register"], options["sec_register"])
    evidence = [*config.evidence.snapshots, *config.evidence.changes]
    sources = {item.source_id for item in evidence}
    sources |= {check.source_id for check in config.evidence.checks}
    if config.universe.etf_proxy is not None:
        sources.add(config.universe.etf_proxy.source_id)
    targets = []
    for source_id in sorted(sources):
        entry = registers.entry(source_id)
        if entry.terms_url is not None:
            targets.append((source_id, "terms", entry.terms_url, entry.terms_sha256))
    for item in sorted(evidence, key=lambda item: item.evidence_id):
        targets.append((item.source_id, "evidence", item.url, item.artifact_sha256))
    return targets


def verify_live(
    repo: Path,
    *,
    fetch_web: Fetch,
    fetch_sec: Fetch,
    now: datetime,
    options: Mapping[str, Path] | None = None,
) -> LiveVerification:
    """Run every live check, then rebuild; ``fetch_*`` carry the access policy."""
    options = options or default_options()
    checks = []
    stopped: set[str] = set()
    for source_id, purpose, url, expected in _targets(repo, options):
        client = "sec" if is_sec_host(urlsplit(url).hostname or "") else "web"
        fetch = fetch_sec if client == "sec" else fetch_web
        if client in stopped:
            checks.append(
                LiveCheck(
                    source_id=source_id,
                    purpose=purpose,
                    url=url,
                    outcome="failed",
                    detail="not requested: an earlier refusal stopped this client",
                    retrieval=None,
                )
            )
            continue
        try:
            fetched = fetch(url, ANY if purpose == "terms" else HTML | PDF)
        except RobotsRefusal as exc:
            outcome, detail, retrieval = "refused", str(exc), None
        except AccessStop as exc:
            stopped.add(client)
            outcome, detail, retrieval = "refused", str(exc), None
        except (UnexpectedResponse, httpx.HTTPError) as exc:
            outcome, detail, retrieval = "failed", str(exc), None
        else:
            retrieval = fetched.retrieval
            found = (
                terms_digest(fetched.body, retrieval.media_type)
                if purpose == "terms"
                else retrieval.sha256
            )
            outcome = "unchanged" if found == expected else "changed"
            detail = f"{purpose} hash {found}; recorded {expected}"
        checks.append(
            LiveCheck(
                source_id=source_id,
                purpose=purpose,
                url=url,
                outcome=outcome,
                detail=detail,
                retrieval=retrieval,
            )
        )

    config = load_cohort_config(repo / options["config_dir"])
    manifests = frozen_manifests(
        repo / options["config_dir"] / "manifests", config.universe.universe_id
    )
    frozen = manifests[-1].definition.content_hash if manifests else None
    try:
        rebuilt = build(repo, **options)
    except CohortError as exc:
        problems, content, blocking = tuple(exc.problems), None, ()
    else:
        problems, content = (), rebuilt.content_hash
        blocking = tuple(f.finding_id for f in rebuilt.report.blocking)
    return LiveVerification(
        checked_at=now,
        checks=tuple(checks),
        build_problems=problems,
        rebuilt_content_hash=content,
        frozen_content_hash=frozen,
        blocking_finding_ids=blocking,
    )


@dataclass
class Sent:
    """The requests a live run has sent so far, kept current as it stops."""

    count: int = 0


def default_options() -> dict[str, Path]:
    return {
        "config_dir": UNIVERSE_DIR,
        "store_root": COHORT_STORE,
        "register": MEMBERSHIP_REGISTER,
        "sec_register": SEC_REGISTER,
    }


def run_live(
    repo: Path,
    *,
    max_requests: int,
    environ: Mapping[str, str] | None = None,
    sent: Sent | None = None,
) -> tuple[LiveVerification, Path]:
    """Open both clients, each capped at ``max_requests``, verify, and save the result
    under data/runs/cohort/live/. ``sent`` keeps the count both clients sent, even
    when the run stops."""
    sent = Sent() if sent is None else sent
    options = default_options()
    hosts = {urlsplit(url).hostname or "" for _, _, url, _ in _targets(repo, options)}
    web_hosts = sorted(host for host in hosts if host and not is_sec_host(host))
    with (
        open_web_client(web_hosts, environ=environ, max_requests=max_requests) as web,
        open_sec_client(environ=environ, max_requests=max_requests) as sec,
    ):
        try:
            result = verify_live(
                repo,
                fetch_web=web.fetch,
                fetch_sec=sec.fetch,
                now=datetime.now(UTC),
                options=options,
            )
        finally:
            sent.count = web.client.throttle.count + sec.throttle.count
    result = result.model_copy(update={"requests_sent": sent.count})
    stamp = result.checked_at.strftime("%Y%m%dT%H%M%SZ")
    path = repo / LIVE_RUNS / f"{stamp}.json"
    write_new(path, result.model_dump_json(indent=1).encode("utf-8") + b"\n")
    return result, path
