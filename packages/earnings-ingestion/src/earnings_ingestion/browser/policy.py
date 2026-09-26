"""Capture policy ``isolated/1`` (B7): a saved filing is untrusted data.

- **Profile.** chromedriver's fresh temporary profile, headless, with no extension,
  sync, or first-run state.
- **JavaScript.** Document JavaScript is disabled through CDP before navigation.
  WebDriver's own scripts, which read text and layout, still run.
- **Requests.** CDP Fetch interception pauses every request. It lets through only
  the saved file itself; everything else fails and is recorded, navigations
  included. CDP's ``Network.setBlockedURLs`` is not enough: frame and object
  documents and a meta refresh escape it (plan 5, PB-2).
- **Defense in depth.** Every connection goes to a dead proxy and every host name
  fails to resolve, and network prediction is off, so a WebSocket or a speculative
  preconnect, which CDP cannot see, never leaves the machine.
- **Files.** The saved bytes are copied alone into an empty temporary directory and
  loaded from there.
- **Bounds.** Startup, navigation, capture, and shutdown are each bounded.

One limitation: Chrome's crash handler keeps its database in the user's
``Library/Application Support/Google/Chrome for Testing/Crashpad``, outside the
temporary profile. It holds crash reports only, and it exits with the browser.
"""

from dataclasses import dataclass

CAPTURE_POLICY = "isolated"
CAPTURE_POLICY_VERSION = "1"

SAVED_NAME = "document.html"
"""The saved file's name in its temporary directory."""


@dataclass(frozen=True)
class CapturePolicy:
    """Everything a capture under one policy version fixes."""

    name: str
    version: str
    arguments: tuple[str, ...]
    preferences: tuple[tuple[str, int], ...]
    viewport_width: int
    viewport_height: int
    device_scale_factor: int
    locale: str
    timezone: str
    startup_seconds: float
    navigation_seconds: float
    capture_seconds: float
    shutdown_seconds: float
    required_resource_types: frozenset[str]
    """CDP resource types whose absence makes a capture ``partial``."""


ISOLATED_1 = CapturePolicy(
    name=CAPTURE_POLICY,
    version=CAPTURE_POLICY_VERSION,
    arguments=(
        "--headless",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-sync",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-default-apps",
        "--mute-audio",
        "--hide-scrollbars",
        "--proxy-server=http://127.0.0.1:9",
        "--proxy-bypass-list=<-loopback>",
        "--host-resolver-rules=MAP * ~NOTFOUND",
        "--window-size=1280,1024",
        "--force-device-scale-factor=1",
        "--lang=en-US",
    ),
    preferences=(("net.network_prediction_options", 2),),
    viewport_width=1280,
    viewport_height=1024,
    device_scale_factor=1,
    locale="en-US",
    timezone="UTC",
    startup_seconds=30.0,
    navigation_seconds=30.0,
    capture_seconds=60.0,
    shutdown_seconds=10.0,
    required_resource_types=frozenset({"Stylesheet", "Font"}),
)
