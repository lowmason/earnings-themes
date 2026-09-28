"""P6-3 over the committed corpus records (PR #6's review, F20; plan 8, P8-5): no
40-character window of any string in a corpus's event manifests, evidence records,
pilots, and overrides occurs in the text of a saved page.

- **Facts are allowed.** Each full date is masked, in the records and the pages
  alike, before the windows are cut. v1's ``overrides.toml`` says "for the quarter
  ended" and a date, as filings do, and that phrase is 40 characters. With dates
  masked, no 30-character window of v1 occurs in a saved page, so 40 leaves a
  margin, and still catches a phrase copied into a longer rationale, which a
  whole-string comparison misses.
- **The pages.** HTML is read as walker-1 text, and plain text as written; a page
  walker-1 cannot read, such as an image-only exhibit, has no text to quote. JSON
  responses, the submissions and companyfacts files, hold facts, not wording, and
  are not read.
- **Where it runs.** The real records are checked against Stage 5's saved store,
  which is local, so that test skips without it. A skip does not protect CI, so each
  freeze's gate runs this module with ``-rs`` and reads "passed". The synthetic
  corpus is checked against its committed pages, and a rationale that copies 40
  characters of one is caught.
"""

import json
import re
from pathlib import Path

import pytest
import tomllib
from earnings_ingestion.cohort.locators import ArtifactText, LocatorError
from earnings_ingestion.events.fixture import FIXTURE_DIR

REPO = Path(__file__).resolve().parents[2]
STORE = REPO / "data" / "raw" / "events" / "sec-edgar"
SYNTHETIC_STORE = REPO / FIXTURE_DIR / "raw" / "sec-edgar"
WIDTH = 40
RECORDS = ("events-v*.json", "pilot-v*.json", "*overrides.toml")
"""The event manifests with their evidence records, the pilots, and the overrides,
the event manifest's and acquisition's."""
MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?"
    r"|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
DATE = re.compile(rf"\b{MONTH}\.?\s+\d{{1,2}},?\s+\d{{4}}\b")


def records(corpus: Path) -> list[Path]:
    return sorted(path for pattern in RECORDS for path in corpus.glob(pattern))


def strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for item in value.values() for s in strings(item)]
    if isinstance(value, list):
        return [s for item in value for s in strings(item)]
    return []


def load(path: Path) -> object:
    text = path.read_text(encoding="utf-8")
    return tomllib.loads(text) if path.suffix == ".toml" else json.loads(text)


def masked(text: str) -> str:
    """``text`` with each full date replaced by a NUL, which no page's text holds."""
    return DATE.sub("\0", text)


def pages(root: Path) -> list[str]:
    """The masked text of each HTML and plain-text page saved under ``root``."""
    found = []
    for path in sorted([*root.glob("*.html"), *root.glob("*.txt")]):
        body = path.read_bytes()
        if path.suffix != ".html":
            text = body.decode("utf-8", errors="replace")
        else:
            try:
                text = ArtifactText(body, "text/html").canonical[0]
            except LocatorError:
                continue
        found.append(masked(text))
    return found


def quoted(paths: list[Path], root: Path) -> set[str]:
    """Each string in ``paths`` one of whose 40-character windows, dates masked,
    occurs in a page saved under ``root``."""
    windows: dict[str, str] = {}
    for path in paths:
        for string in strings(load(path)):
            text = masked(string)
            for start in range(len(text) - WIDTH + 1):
                windows.setdefault(text[start : start + WIDTH], string)
    found = set()
    for text in pages(root):
        for start in range(len(text) - WIDTH + 1):
            if (string := windows.get(text[start : start + WIDTH])) is not None:
                found.add(string)
    return found


def test_the_real_corpus_records_quote_no_saved_page() -> None:
    if not STORE.is_dir():
        pytest.skip(
            f"{STORE.relative_to(REPO)} is not saved here: each freeze's gate runs"
            " this test"
        )
    corpus = [
        path
        for directory in sorted((REPO / "config" / "corpus").iterdir())
        if directory.is_dir()
        for path in records(directory)
    ]
    assert corpus
    assert quoted(corpus, STORE) == set()


def test_the_synthetic_corpus_records_quote_no_saved_page() -> None:
    corpus = records(REPO / FIXTURE_DIR)
    assert [path.name for path in corpus] == [
        "events-v1.evidence.json",
        "events-v1.json",
        "overrides.toml",
        "pilot-v1.json",
    ]
    assert quoted(corpus, SYNTHETIC_STORE) == set()


@pytest.mark.parametrize(("width", "caught"), [(WIDTH, True), (WIDTH - 1, False)])
def test_a_rationale_that_copies_40_characters_is_caught(
    tmp_path, width: int, caught: bool
) -> None:
    """A rationale that copies 40 characters of a saved page, inside words of its
    own, is caught, and one that copies 39 is not: the window is 40."""
    text = next(text for text in pages(SYNTHETIC_STORE) if "announced" in text)
    start = text.index("announced")
    copied = f"Reviewed [{text[start : start + width]}] by hand."
    source = REPO / FIXTURE_DIR / "overrides.toml"
    lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    at = next(n for n, line in enumerate(lines) if line.startswith("rationale = "))
    lines[at] = f"rationale = {json.dumps(copied, ensure_ascii=False)}\n"
    overrides = tmp_path / "overrides.toml"
    overrides.write_text("".join(lines), encoding="utf-8")
    assert quoted([overrides], SYNTHETIC_STORE) == ({copied} if caught else set())
