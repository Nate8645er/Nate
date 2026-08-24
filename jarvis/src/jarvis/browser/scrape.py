"""Lightweight page fetching and HTML text/link extraction without a browser.

Uses httpx for fetching and selectolax for parsing when available; otherwise
falls back to small stdlib :class:`html.parser.HTMLParser` implementations.
"""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx

from jarvis.browser.search import USER_AGENT
from jarvis.core.errors import BrowserError

_SKIP_TAGS = {"script", "style", "noscript", "template", "head"}
_IGNORED_SCHEMES = ("javascript:", "mailto:", "tel:", "#")


class _TextExtractor(HTMLParser):
    """Stdlib fallback: visible text with script/style stripped."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data.strip():
            self._chunks.append(data)

    def text(self) -> str:
        return " ".join(" ".join(self._chunks).split())


class _LinkExtractor(HTMLParser):
    """Stdlib fallback: collect anchor href/text pairs."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._href = href
                self._text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append(
                {"text": " ".join("".join(self._text).split()), "href": self._href}
            )
            self._href = None

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)


async def fetch_page(url: str) -> str:
    """Fetch *url* (redirects followed, 30s timeout) and return the raw HTML."""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=30.0, follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as exc:
        raise BrowserError(f"Could not fetch '{url}': {exc}", cause=exc) from exc


def extract_text(html: str, max_chars: int = 8000) -> str:
    """Extract readable text from *html*: scripts/styles stripped, whitespace collapsed."""
    try:
        from selectolax.parser import HTMLParser as SelectolaxParser
    except ImportError:
        parser = _TextExtractor()
        parser.feed(html)
        parser.close()
        text = parser.text()
    else:
        tree = SelectolaxParser(html)
        for node in tree.css("script, style, noscript, template"):
            node.decompose()
        body = tree.body or tree.root
        text = " ".join((body.text(separator=" ") if body is not None else "").split())
    return text[:max_chars]


def extract_links(html: str, base_url: str, limit: int = 100) -> list[dict[str, str]]:
    """Extract anchors from *html* with hrefs resolved against *base_url*."""
    raw: list[dict[str, str]]
    try:
        from selectolax.parser import HTMLParser as SelectolaxParser
    except ImportError:
        parser = _LinkExtractor()
        parser.feed(html)
        parser.close()
        raw = parser.links
    else:
        tree = SelectolaxParser(html)
        raw = [
            {
                "text": " ".join(node.text().split()),
                "href": node.attributes.get("href") or "",
            }
            for node in tree.css("a[href]")
        ]
    links: list[dict[str, str]] = []
    for item in raw:
        href = item["href"].strip()
        if not href or href.startswith(_IGNORED_SCHEMES):
            continue
        links.append({"text": item["text"][:120], "href": urljoin(base_url, href)})
        if len(links) >= limit:
            break
    return links
