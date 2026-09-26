"""The pinned Chrome for Testing: its manifest, the setup command's install, and lookup.

``chrome-for-testing.toml`` beside this module pins one version, and for each platform
the URL, size, and SHA-256 of the browser and driver archives (B3, B8). ``install``
is the setup command's work and the only code in the project that downloads a
binary: it checks each archive's size and hash before extracting it, keeps the
archive's symlinks and executable bits, and moves the finished tree into place in one
rename, so a half-installed tree never looks installed. A capture only ever calls
``installed``, which downloads nothing.
"""

import hashlib
import os
import platform
import shutil
import stat
import subprocess
import tempfile
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from importlib import resources
from pathlib import Path, PurePosixPath

import httpx
import tomllib

MANIFEST = "chrome-for-testing.toml"
CACHE_VARIABLE = "EARNINGS_BROWSER_CACHE"


@dataclass(frozen=True)
class Archive:
    """One archive of the pinned build for one platform."""

    name: str
    url: str
    size: int
    sha256: str
    executable: str
    """The executable's path inside the extracted archive."""


@dataclass(frozen=True)
class Pin:
    """The pinned version and, for one platform, its two archives."""

    version: str
    platform: str
    browser: Archive
    driver: Archive


@dataclass(frozen=True)
class Binaries:
    """The pinned browser and driver executables, and the version both must report."""

    browser: Path
    driver: Path
    version: str

    def present(self) -> bool:
        return self.browser.is_file() and self.driver.is_file()


def platform_name() -> str | None:
    """Chrome for Testing's name for this machine, where the manifest may pin one."""
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        return "mac-arm64"
    return None


def load_pin(name: str | None = None, text: str | None = None) -> Pin | None:
    """The manifest's pin for platform ``name`` (this machine's by default), or
    ``None`` when the manifest pins no build for it."""
    name = platform_name() if name is None else name
    if text is None:
        text = (
            resources.files(__package__).joinpath(MANIFEST).read_text(encoding="utf-8")
        )
    manifest = tomllib.loads(text)
    archives = {
        entry["name"]: Archive(
            name=entry["name"],
            url=entry["url"],
            size=entry["size"],
            sha256=entry["sha256"],
            executable=entry["executable"],
        )
        for entry in manifest["archives"]
        if entry["platform"] == name
    }
    if name is None or set(archives) != {"chrome", "chromedriver"}:
        return None
    return Pin(manifest["version"], name, archives["chrome"], archives["chromedriver"])


def default_cache() -> Path:
    """``$EARNINGS_BROWSER_CACHE`` if set, else the user's cache directory; either way
    outside the repository. The version check still applies to whatever it holds."""
    override = os.environ.get(CACHE_VARIABLE)
    if override:
        return Path(override)
    return Path.home() / "Library" / "Caches" / "earnings-themes" / "chrome-for-testing"


def installed(cache: Path | None = None, pin: Pin | None = None) -> Binaries | None:
    """The installed pinned binaries, or ``None``; never downloads anything."""
    pin = load_pin() if pin is None else pin
    if pin is None:
        return None
    root = (default_cache() if cache is None else cache) / pin.version / pin.platform
    binaries = Binaries(
        browser=root / pin.browser.executable,
        driver=root / pin.driver.executable,
        version=pin.version,
    )
    return binaries if binaries.present() else None


Fetch = Callable[[Archive, Path], None]
"""Writes one archive's bytes to a path; ``download`` in the setup command, a local
copy in tests."""


def install(pin: Pin, cache: Path, fetch: Fetch) -> Binaries:
    """Download, check, and extract both archives; return the installed binaries.

    Raises ``ValueError`` when an archive's size or hash is not the manifest's, or an
    extracted executable does not report the pinned version.
    """
    done = installed(cache, pin)
    if done is not None:
        return done
    target = cache / pin.version / pin.platform
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent, prefix=".install-") as scratch:
        staging = Path(scratch) / "tree"
        staging.mkdir()
        for archive in (pin.browser, pin.driver):
            path = Path(scratch) / f"{archive.name}.zip"
            fetch(archive, path)
            _check(archive, path)
            safe_extract(path, staging)
        binaries = Binaries(
            browser=staging / pin.browser.executable,
            driver=staging / pin.driver.executable,
            version=pin.version,
        )
        for executable in (binaries.browser, binaries.driver):
            reported = reported_version(executable)
            if reported != pin.version:
                raise ValueError(
                    f"{executable.name} reports {reported!r}, not {pin.version}"
                )
        if target.exists():
            shutil.rmtree(target)
        os.rename(staging, target)
    done = installed(cache, pin)
    assert done is not None
    return done


def _check(archive: Archive, path: Path) -> None:
    size = path.stat().st_size
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1 << 20):
            digest.update(chunk)
    if size != archive.size or digest.hexdigest() != archive.sha256:
        raise ValueError(
            f"{archive.name}: got {size} bytes with SHA-256 {digest.hexdigest()};"
            f" the manifest pins {archive.size} bytes with {archive.sha256}"
        )


def safe_extract(archive: Path, destination: Path) -> None:
    """Extract ``archive`` into ``destination``, keeping symlinks and executable bits.

    Each of these raises ``ValueError``: an absolute entry, or one with a ``..``
    segment; an entry that would land outside ``destination`` through a link already
    there; and a link whose target is absolute, holds a ``..`` segment, or resolves
    outside. Links may only descend, so no two of them can compose a way out. The
    hash already vouches for the archive: this is the second line of defence.
    """
    destination = destination.resolve()
    with zipfile.ZipFile(archive) as zipped:
        for info in zipped.infolist():
            name = PurePosixPath(info.filename)
            if name.is_absolute() or ".." in name.parts:
                raise ValueError(f"unsafe entry {info.filename!r}")
            target = destination.joinpath(*name.parts)
            if not target.resolve().is_relative_to(destination):
                raise ValueError(f"unsafe entry {info.filename!r}: it lands outside")
            mode = info.external_attr >> 16
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if stat.S_ISLNK(mode):
                link = zipped.read(info).decode("utf-8")
                pointer = PurePosixPath(link)
                if (
                    pointer.is_absolute()
                    or ".." in pointer.parts
                    or not (target.parent / link).resolve().is_relative_to(destination)
                ):
                    raise ValueError(f"unsafe link {info.filename!r} -> {link!r}")
                os.symlink(link, target)
                continue
            with zipped.open(info) as source, target.open("wb") as out:
                shutil.copyfileobj(source, out, 1 << 20)
            os.chmod(target, 0o755 if mode & 0o111 else 0o644)


def reported_version(executable: Path) -> str:
    """The version an executable prints for ``--version``: its first word that starts
    with a digit, such as ``154.0.8037.57``."""
    completed = subprocess.run(
        [str(executable), "--version"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    words = [word for word in completed.stdout.split() if word[:1].isdigit()]
    return words[0] if words else ""


def download(archive: Archive, path: Path) -> None:
    """Stream one archive over HTTPS; the setup command's ``Fetch``."""
    with httpx.stream(
        "GET", archive.url, timeout=60.0, follow_redirects=False
    ) as reply:
        reply.raise_for_status()
        with path.open("wb") as out:
            for chunk in reply.iter_bytes(1 << 20):
                out.write(chunk)
