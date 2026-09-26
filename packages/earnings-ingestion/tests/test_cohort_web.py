"""The cohort web client: registered hosts only, never SEC, robots.txt first."""

import httpx
import pytest
from earnings_ingestion.cohort.web import (
    RobotsRefusal,
    hosts_of,
    open_web_client,
)
from earnings_ingestion.fetch.client import AccessStop

ENVIRON = {"SOURCE_IDENTITY": "Jane Doe earnings-themes research jane@example.org"}
ROBOTS = b"User-agent: *\nDisallow: /w/\n"


def opened(tmp_path, handler, hosts=("roster.example",)):
    return open_web_client(
        tmp_path,
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


def test_an_allowed_page_is_fetched_after_robots(tmp_path) -> None:
    seen = []

    def handler(request):
        seen.append(request.url.path)
        return site(request)

    with opened(tmp_path, handler) as web:
        fetched = web.fetch("https://roster.example/wiki/Roster?oldid=1", {"text/html"})
    assert fetched.body == b"<p>A roster.</p>"
    assert seen == ["/robots.txt", "/wiki/Roster"]


def test_a_disallowed_page_is_refused_unrequested(tmp_path) -> None:
    seen = []

    def handler(request):
        seen.append(request.url.path)
        return site(request)

    with (
        opened(tmp_path, handler) as web,
        pytest.raises(RobotsRefusal, match="Disallow: /w/"),
    ):
        web.fetch("https://roster.example/w/index.php?oldid=1", {"text/html"})
    assert seen == ["/robots.txt"]


def test_an_unregistered_host_is_refused(tmp_path) -> None:
    with opened(tmp_path, site) as web, pytest.raises(AccessStop, match="outside"):
        web.fetch("https://elsewhere.example/page", {"text/html"})


def test_sec_hosts_belong_to_the_sec_client(tmp_path) -> None:
    with (
        pytest.raises(ValueError, match="shared SEC client"),
        opened(tmp_path, site, hosts=("roster.example", "www.sec.gov")),
    ):
        pass


def test_an_identity_is_required(tmp_path) -> None:
    with (
        pytest.raises(AccessStop, match="SOURCE_IDENTITY"),
        open_web_client(tmp_path, ["roster.example"], environ={}),
    ):
        pass


def test_hosts_come_from_urls() -> None:
    urls = ["https://roster.example/a", "https://index.example/b?x=1"]
    assert hosts_of(urls) == {"roster.example", "index.example"}
