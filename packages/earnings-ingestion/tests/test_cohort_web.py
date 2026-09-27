"""The cohort web client: registered hosts only, never SEC, robots.txt first, and
one per machine."""

import subprocess
import sys

import httpx
import pytest
from earnings_ingestion.cohort.web import (
    LOCK_NAME,
    RobotsRefusal,
    hosts_of,
    open_web_client,
)
from earnings_ingestion.fetch.client import AccessStop, machine_lock_dir

ENVIRON = {"SOURCE_IDENTITY": "Jane Doe earnings-themes research jane@example.org"}
ROBOTS = b"User-agent: *\nDisallow: /w/\n"


def opened(handler, hosts=("roster.example",)):
    return open_web_client(
        hosts,
        environ=ENVIRON,
        transport=httpx.MockTransport(handler),
        sleep=lambda seconds: None,
    )


def site(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/robots.txt":
        return httpx.Response(200, content=ROBOTS)
    return httpx.Response(
        200, content=b"<p>A roster.</p>", headers={"Content-Type": "text/html"}
    )


def test_an_allowed_page_is_fetched_after_robots() -> None:
    seen = []

    def handler(request):
        seen.append(request.url.path)
        return site(request)

    with opened(handler) as web:
        fetched = web.fetch("https://roster.example/wiki/Roster?oldid=1", {"text/html"})
    assert fetched.body == b"<p>A roster.</p>"
    assert seen == ["/robots.txt", "/wiki/Roster"]


def test_a_disallowed_page_is_refused_unrequested() -> None:
    seen = []

    def handler(request):
        seen.append(request.url.path)
        return site(request)

    with (
        opened(handler) as web,
        pytest.raises(RobotsRefusal, match="Disallow: /w/"),
    ):
        web.fetch("https://roster.example/w/index.php?oldid=1", {"text/html"})
    assert seen == ["/robots.txt"]


def test_an_unregistered_host_is_refused() -> None:
    with opened(site) as web, pytest.raises(AccessStop, match="outside"):
        web.fetch("https://elsewhere.example/page", {"text/html"})


@pytest.mark.parametrize(
    "sec", ["www.sec.gov", "www.sec.gov."], ids=["bare", "trailing-dot"]
)
def test_sec_hosts_belong_to_the_sec_client(sec) -> None:
    with (
        pytest.raises(ValueError, match="shared SEC client"),
        opened(site, hosts=("roster.example", sec)),
    ):
        pass


def test_an_identity_is_required() -> None:
    with (
        pytest.raises(AccessStop, match="SOURCE_IDENTITY"),
        open_web_client(["roster.example"], environ={}),
    ):
        pass


CHILD = """
import sys
from earnings_ingestion.cohort.web import open_web_client
from earnings_ingestion.fetch.client import AccessStop
try:
    with open_web_client(["roster.example"], environ={"SOURCE_IDENTITY": sys.argv[1]}):
        print("opened")
except AccessStop as stop:
    print(stop)
"""


def test_two_checkouts_share_one_lock(tmp_path, monkeypatch) -> None:
    """A second worktree or clone is another process in another directory. It finds
    the lock this one holds, in the machine's lock directory (plan 6's deferred item).
    """
    first, second = tmp_path / "checkout-a", tmp_path / "checkout-b"
    first.mkdir()
    second.mkdir()
    monkeypatch.chdir(first)
    with opened(site):
        child = subprocess.run(
            [sys.executable, "-c", CHILD, ENVIRON["SOURCE_IDENTITY"]],
            cwd=second,
            capture_output=True,
            text=True,
            check=True,
        )
    assert child.stdout.strip() == (
        f"another client holds {machine_lock_dir() / LOCK_NAME}"
    )


def test_hosts_come_from_urls() -> None:
    urls = ["https://roster.example/a", "https://index.example/b?x=1"]
    assert hosts_of(urls) == {"roster.example", "index.example"}
