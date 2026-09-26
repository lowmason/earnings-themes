"""The pinned manifest, the setup command's install, and lookup, with no download.

The archives here are tiny zips whose "browser" and "driver" are shell scripts that
print a version, so every path runs offline in milliseconds.
"""

import hashlib
import stat
import zipfile
from pathlib import Path

import pytest
from earnings_ingestion.browser.install import (
    Archive,
    Pin,
    install,
    installed,
    load_pin,
    safe_extract,
)

BROWSER = "chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
DRIVER = "chromedriver-mac-arm64/chromedriver"


def script(version_line: str) -> bytes:
    return f"#!/bin/sh\necho '{version_line}'\n".encode("ascii")


def make_zip(path: Path, files: dict[str, bytes], links: dict[str, str] = {}) -> Path:  # noqa: B006
    with zipfile.ZipFile(path, "w") as zipped:
        for name, data in files.items():
            info = zipfile.ZipInfo(name)
            info.external_attr = (stat.S_IFREG | 0o755) << 16
            zipped.writestr(info, data)
        for name, target in links.items():
            info = zipfile.ZipInfo(name)
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            zipped.writestr(info, target)
    return path


def archive_for(path: Path, name: str, executable: str) -> Archive:
    data = path.read_bytes()
    return Archive(
        name=name,
        url=f"https://example.invalid/{path.name}",
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        executable=executable,
    )


def pinned(tmp_path: Path, browser_says: str = "154.0.8037.57") -> tuple[Pin, dict]:
    browser_zip = make_zip(
        tmp_path / "chrome.zip",
        {BROWSER: script(f"Google Chrome for Testing {browser_says}")},
        {"chrome-mac-arm64/Google Chrome for Testing.app/Contents/Current": "MacOS"},
    )
    driver_zip = make_zip(
        tmp_path / "chromedriver.zip",
        {
            DRIVER: script(
                "ChromeDriver 154.0.8037.57 (abc-refs/branch-heads/8037@{#1})"
            )
        },
    )
    pin = Pin(
        version="154.0.8037.57",
        platform="mac-arm64",
        browser=archive_for(browser_zip, "chrome", BROWSER),
        driver=archive_for(driver_zip, "chromedriver", DRIVER),
    )
    return pin, {"chrome": browser_zip, "chromedriver": driver_zip}


def test_the_committed_manifest_pins_one_version_for_mac_arm64() -> None:
    pin = load_pin("mac-arm64")
    assert pin is not None
    assert pin.version == "154.0.8037.57"
    assert pin.browser.url.endswith("/154.0.8037.57/mac-arm64/chrome-mac-arm64.zip")
    assert pin.driver.url.endswith(
        "/154.0.8037.57/mac-arm64/chromedriver-mac-arm64.zip"
    )
    assert (pin.browser.size, pin.driver.size) == (191429663, 9302980)


def test_no_build_is_pinned_for_other_platforms() -> None:
    assert load_pin("linux64") is None


def test_nothing_is_installed_in_an_empty_cache(tmp_path: Path) -> None:
    pin, _ = pinned(tmp_path)
    assert installed(tmp_path / "cache", pin) is None


def test_install_checks_extracts_and_finds_the_binaries(tmp_path: Path) -> None:
    pin, zips = pinned(tmp_path)
    fetched: list[str] = []

    def fetch(archive: Archive, path: Path) -> None:
        fetched.append(archive.name)
        path.write_bytes(zips[archive.name].read_bytes())

    cache = tmp_path / "cache"
    binaries = install(pin, cache, fetch)
    assert binaries == installed(cache, pin)
    assert binaries.browser == cache / "154.0.8037.57" / "mac-arm64" / BROWSER
    link = binaries.browser.parents[1] / "Current"
    assert link.is_symlink() and link.readlink() == Path("MacOS")
    assert install(pin, cache, fetch) == binaries
    assert fetched == ["chrome", "chromedriver"]


def test_an_archive_that_is_not_the_pinned_one_is_refused(tmp_path: Path) -> None:
    pin, zips = pinned(tmp_path)

    def fetch(archive: Archive, path: Path) -> None:
        path.write_bytes(zips[archive.name].read_bytes() + b"tampered")

    with pytest.raises(ValueError, match="the manifest pins"):
        install(pin, tmp_path / "cache", fetch)
    assert installed(tmp_path / "cache", pin) is None


def test_a_binary_reporting_another_version_is_refused(tmp_path: Path) -> None:
    pin, zips = pinned(tmp_path, browser_says="153.0.0.0")

    def fetch(archive: Archive, path: Path) -> None:
        path.write_bytes(zips[archive.name].read_bytes())

    with pytest.raises(ValueError, match="reports '153.0.0.0'"):
        install(pin, tmp_path / "cache", fetch)
    assert installed(tmp_path / "cache", pin) is None


@pytest.mark.parametrize(
    ("files", "links", "message"),
    [
        ({"../escape": b"x"}, {}, "unsafe entry"),
        ({"/absolute": b"x"}, {}, "unsafe entry"),
        ({}, {"inside/link": "../../outside"}, "unsafe link"),
        ({}, {"inside/link": "/etc/passwd"}, "unsafe link"),
    ],
)
def test_extraction_never_writes_outside_its_directory(
    tmp_path: Path, files: dict, links: dict, message: str
) -> None:
    archive = make_zip(tmp_path / "bad.zip", files, links)
    destination = tmp_path / "out"
    destination.mkdir()
    with pytest.raises(ValueError, match=message):
        safe_extract(archive, destination)
