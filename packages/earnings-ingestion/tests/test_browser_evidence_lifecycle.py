"""Invented SDK doubles in a child; no optional browser import at collection."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "case",
    ["url", "proxy", "frame", "fetch", "remote-http", "remote-ws", "process"],
    ids=["url", "proxy", "frame", "fetch", "remote-http", "remote-ws", "process"],
)
def test_lifecycle_is_bounded_and_clean(case):
    child = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), case],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert child.returncode == 0
    result = json.loads(child.stdout)
    assert result["safe"]
    assert result["clean"]


def exercise(case):
    import importlib
    import io
    import types

    # These module doubles exist only in this child and vanish at process exit.
    for name in (
        "selenium",
        "selenium.webdriver",
        "selenium.common",
        "selenium.common.exceptions",
        "selenium.webdriver.chrome",
        "selenium.webdriver.chrome.service",
        "websocket",
    ):
        sys.modules[name] = types.ModuleType(name)
    sys.modules["selenium"].__version__ = "invented"
    sys.modules["selenium"].webdriver = sys.modules["selenium.webdriver"]
    sys.modules["selenium.common.exceptions"].TimeoutException = type(
        "TimeoutException", (Exception,), {}
    )
    sys.modules["selenium.webdriver.chrome.service"].Service = object
    module = importlib.import_module("earnings_ingestion.browser.selenium_capture")
    from earnings_ingestion.browser import ISOLATED_1

    cleaned = []
    if case == "process":

        class Process:
            pid = 12345

            def poll(self):
                return None

            def wait(self, timeout):
                cleaned.append("wait")

        class Driver:
            def quit(self):
                cleaned.append("quit")
                raise RuntimeError("invented sentinel")

        browser = module._Browser.__new__(module._Browser)
        browser._service = types.SimpleNamespace(process=Process())
        browser.driver = Driver()
        module.os.killpg = lambda pid, sig: cleaned.append("kill")
        browser.close(0.2)
        return {"safe": cleaned == ["quit", "kill", "wait"], "clean": True}
    if case == "url":

        class Driver:
            @property
            def capabilities(self):
                return {"goog:chromeOptions": {"debuggerAddress": "127.0.0.1:9123"}}

            def execute_cdp_cmd(self, *args):
                pass

            def set_page_load_timeout(self, *args):
                pass

            def set_script_timeout(self, *args):
                pass

            def get(self, *args):
                pass

            @property
            def current_url(self):
                raise RuntimeError("invented private sentinel")

        class Browser:
            def __init__(self, *args):
                pass

            def start(self):
                return Driver()

            def kill(self):
                cleaned.append("kill")

            def close(self, *args):
                cleaned.append("browser")

        class Interceptor:
            def __init__(self, *args):
                pass

            def close(self):
                cleaned.append("interceptor")

        module._Browser = Browser
        module._Interceptor = Interceptor
        binaries = types.SimpleNamespace(version="invented", present=lambda: True)
        renderer = module.SeleniumRenderer(binaries)
        renderer._check_versions = lambda _: None
        try:
            result = renderer.capture(
                b"<p>Invented</p>", ISOLATED_1, source_document_id="invented"
            )
            safe = (
                result.status.value == "failed"
                and result.reason.value == "document_load_failure"
            )
        except Exception:  # noqa: BLE001 - invented child diagnostics never escape
            safe = False
        return {"safe": safe, "clean": cleaned == ["browser", "interceptor"]}

    inherited = []
    openers = []

    def reply():
        return io.BytesIO(
            json.dumps(
                [
                    {
                        "type": "page",
                        "webSocketDebuggerUrl": (
                            "ws://example.invalid:9123/devtools/page/invented"
                            if case == "remote-ws"
                            else "ws://127.0.0.1:9123/devtools/page/invented"
                        ),
                    }
                ]
            ).encode()
        )

    def inherited_open(*args, **kwargs):
        inherited.append(True)
        return reply()

    def build_opener(handler):
        openers.append(handler.proxies)
        return types.SimpleNamespace(open=lambda *a, **k: reply())

    module.urllib.request.urlopen = inherited_open
    module.urllib.request.build_opener = build_opener
    import os

    os.environ["HTTP_PROXY"] = "http://proxy.example.invalid:8888"

    class Socket:
        def close(self):
            cleaned.append("socket")

        def settimeout(self, *args):
            pass

    connections = []

    def connect(*args, **kwargs):
        connections.append(True)
        return Socket()

    module.websocket.create_connection = connect

    def call(self, method, params):
        if method == ("Fetch.enable" if case == "fetch" else "Page.getFrameTree"):
            raise RuntimeError("invented private sentinel")
        return {"frameTree": {"frame": {"id": "invented"}}}

    module._Interceptor._call = call
    try:
        module._Interceptor(
            "example.invalid:9123" if case == "remote-http" else "127.0.0.1:9123",
            "file:///invented.html",
            frozenset(),
        )
    except Exception:  # noqa: BLE001 - invented child diagnostics never escape
        failed = True
    else:
        failed = False
    if case == "remote-http":
        return {
            "safe": failed and not inherited and not openers,
            "clean": not connections,
        }
    if case == "remote-ws":
        return {"safe": failed and openers == [{}], "clean": not connections}
    if case == "proxy":
        return {"safe": openers == [{}] and not inherited, "clean": True}

    class Browser:
        def __init__(self, *args):
            pass

        def start(self):
            return types.SimpleNamespace(
                capabilities={
                    "goog:chromeOptions": {"debuggerAddress": "127.0.0.1:9123"}
                }
            )

        def kill(self):
            cleaned.append("kill")

        def close(self, *args):
            cleaned.append("browser")

    module._Browser = Browser
    renderer = module.SeleniumRenderer(
        types.SimpleNamespace(version="invented", present=lambda: True)
    )
    renderer._check_versions = lambda _: None
    result = renderer.capture(
        b"<p>Invented</p>", ISOLATED_1, source_document_id="invented"
    )
    return {
        "safe": failed
        and result.status.value == "failed"
        and result.reason.value == "startup_failure",
        "clean": cleaned == ["socket", "socket", "browser"],
    }


if __name__ == "__main__":
    try:
        print(json.dumps(exercise(sys.argv[1])))
    except BaseException:  # noqa: BLE001 - metadata only across the child boundary
        print(json.dumps({"safe": False, "clean": False}))
