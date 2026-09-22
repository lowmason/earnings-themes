import json

from fetch_policy_pages import PAGES, page_text, policy_sentences, quote_found, verify

PAGE = b"""<html><head><title>Policies</title></head><body>
<h2>Dissemination</h2><p>Information on this site is public information and may be
copied.  Credit is requested.</p><p>Unrelated text.</p></body></html>"""


def test_policy_sentences_pick_the_reuse_statement():
    text = page_text(PAGE)
    assert policy_sentences(text, PAGES["reuse"][1]) == [
        "Dissemination Information on this site is public information and may be copied."
    ]


def test_quote_found_ignores_whitespace_differences():
    text = page_text(PAGE)
    assert quote_found("public information and may be\n copied.", text)
    assert not quote_found("public information and may not be copied.", text)


def _register(tmp_path, reuse_quote, checked_on="2026-09-23"):
    register = tmp_path / "register.toml"
    register.write_text(
        f"[sources.sec-edgar]\nlast_verified = {checked_on}\n"
        f'[sources.sec-edgar.reuse_policy]\nurl = "https://www.sec.gov/p"\n'
        f'checked_on = {checked_on}\nquote = "{reuse_quote}"\n'
        f'[sources.sec-edgar.access]\nurl = "https://www.sec.gov/a"\n'
        f'checked_on = {checked_on}\naccess_quote = "Declare your user agent."\n'
    )
    return register


def _save(pages, key, url, body):
    pages.mkdir(exist_ok=True)
    (pages / f"{key}.html").write_bytes(body)
    meta = {
        "url": url,
        "retrieved_at": "2026-09-23T10:00:00Z",
        "http_status": 200,
        "content_type": "text/html",
        "bytes": len(body),
        "sha256": "x",
    }
    (pages / f"{key}.html.meta.json").write_text(json.dumps(meta))


def test_verify_accepts_matching_quotes_urls_and_dates(tmp_path):
    pages = tmp_path / "pages"
    _save(pages, "reuse", "https://www.sec.gov/p", PAGE)
    _save(pages, "access", "https://www.sec.gov/a", b"<p>Declare your user agent.</p>")
    register = _register(tmp_path, "public information and may be copied.")
    assert verify(register, pages) == []


def test_verify_reports_missing_pages_wrong_quotes_and_dates(tmp_path):
    pages = tmp_path / "pages"
    _save(pages, "reuse", "https://www.sec.gov/p", PAGE)
    register = _register(tmp_path, "may never be copied.", checked_on="2026-09-24")
    problems = verify(register, pages)
    assert any("access.html is missing" in p for p in problems)
    assert any("reuse_policy.quote does not occur" in p for p in problems)
    assert any("checked_on differs" in p for p in problems)
