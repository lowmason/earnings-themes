# /// script
# requires-python = ">=3.14"
# dependencies = ["httpx==0.28.1"]
# ///
"""Fetch the SEC pages that docs/source-register.toml quotes, and verify the quotes.

    uv run --locked --script expirements/parser-fidelity/fetch_policy_pages.py fetch --live
    uv run --locked --script expirements/parser-fidelity/fetch_policy_pages.py verify

``fetch`` saves each page under data/raw/register/ and prints the sentences that state
the SEC's reuse and access policies. Copy the sentences verbatim into the register.
``verify`` checks that every register quote occurs in its saved page.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import tomllib
from pf_decode import decode_html_bytes
from pf_fetch import (
    EdgarFetcher,
    LiveLock,
    LivePolicyStop,
    Throttle,
    UnexpectedResponse,
    read_meta,
    require_identity,
)
from pf_paths import DATA_RAW, LIVE_LOCK, REGISTER
from pf_space import primary_space
from pf_text import extract_document_text

REGISTER_PAGES = DATA_RAW / "register"
PAGES = {
    "reuse": (
        (
            "https://www.sec.gov/privacy.htm",
            "https://www.sec.gov/about/privacy-information",
        ),
        re.compile(
            r"public information|further distribut|copied|reproduc", re.IGNORECASE
        ),
    ),
    "access": (
        ("https://www.sec.gov/os/accessing-edgar-data",),
        re.compile(r"user[- ]agent|requests? per second|automated tool", re.IGNORECASE),
    ),
}
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def page_text(raw: bytes) -> str:
    return " ".join(
        extract_document_text(decode_html_bytes(raw).text, joiner=" ").split()
    )


def policy_sentences(text: str, pattern: re.Pattern[str]) -> list[str]:
    return [
        sentence for sentence in _SENTENCE_END.split(text) if pattern.search(sentence)
    ]


def quote_found(quote: str, text: str) -> bool:
    """Whitespace-insensitive: the primary matching space deletes whitespace."""
    return bool(primary_space(quote)) and primary_space(quote) in primary_space(text)


def fetch(fetcher: EdgarFetcher) -> None:
    for key, (urls, pattern) in PAGES.items():
        for url in urls:
            dest = REGISTER_PAGES / f"{key}.html"
            try:
                saved = fetcher.fetch_and_save(url, dest, {"text/html"})
            except UnexpectedResponse as exc:
                print(f"[{key}] {exc}")
                continue
            print(f"[{key}] saved {saved.url} ({saved.retrieved_at})")
            for sentence in policy_sentences(page_text(dest.read_bytes()), pattern):
                print(f"  - {sentence}")
            break
        else:
            print(
                f"[{key}] no candidate URL answered; locate the page from sec.gov's footer links"
            )


def verify(register_path: Path = REGISTER, pages: Path = REGISTER_PAGES) -> list[str]:
    entry = tomllib.loads(register_path.read_text(encoding="utf-8"))["sources"][
        "sec-edgar"
    ]
    problems = []
    checked = []
    for key, table, field in (
        ("reuse", "reuse_policy", "quote"),
        ("access", "access", "access_quote"),
    ):
        saved = pages / f"{key}.html"
        if not saved.exists():
            problems.append(f"{saved} is missing; run `fetch --live` first")
            continue
        meta = read_meta(saved)
        if meta.url != entry[table]["url"]:
            problems.append(f"{table}.url differs from the saved page's URL {meta.url}")
        if str(entry[table]["checked_on"]) != meta.retrieved_at[:10]:
            problems.append(
                f"{table}.checked_on differs from the retrieval date {meta.retrieved_at[:10]}"
            )
        if not quote_found(entry[table][field], page_text(saved.read_bytes())):
            problems.append(f"{table}.{field} does not occur verbatim in {saved}")
        checked.append(str(entry[table]["checked_on"]))
    if checked and str(entry["last_verified"]) != max(checked):
        problems.append("last_verified must equal the latest checked_on date")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("fetch").add_argument("--live", action="store_true")
    sub.add_parser("verify")
    args = parser.parse_args(argv)
    if args.command == "verify":
        problems = verify()
        for problem in problems:
            print(problem)
        print(
            "register quotes verified"
            if not problems
            else f"{len(problems)} problem(s)"
        )
        return 1 if problems else 0
    if not args.live:
        parser.error("fetch makes live requests; pass --live to confirm")
    throttle = Throttle(max_requests=10)
    fetcher = EdgarFetcher(require_identity(), throttle=throttle)
    try:
        with LiveLock(LIVE_LOCK):
            fetch(fetcher)
    except LivePolicyStop as exc:
        print(f"STOPPED: {exc}", file=sys.stderr)
        return 1
    finally:
        fetcher.close()
        print(f"requests made: {throttle.count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
