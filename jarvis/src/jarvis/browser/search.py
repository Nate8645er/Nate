"""Web search via the DuckDuckGo HTML endpoint (no API key, no browser).

Results are parsed with selectolax when available, otherwise with a small
stdlib :class:`html.parser.HTMLParser` fallback, and DuckDuckGo redirect
links (``/l/?uddg=...``) are unwrapped to the real target URLs.
"""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

import httpx

from jarvis.core.errors import BrowserError

SEARCH_URL = "https://html.duckduckgo.com/html/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img",
    "input", "link", "meta", "source", "track", "wbr",
}


def _clean(text: str) -> str:
    return " ".join(text.split())


def unwrap_redirect(href: str) -> str:
    """Resolve a DuckDuckGo redirect link (``//duckduckgo.com/l/?uddg=...``)."""
    if href.startswith("//"):
        href = f"https:{href}"
    parts = urlsplit(href)
    if parts.netloc.endswith("duckduckgo.com") and parts.path.startswith("/l/"):
        target = parse_qs(parts.query).get("uddg")
        if target:
            return target[0]
    return href


class _DdgHtmlParser(HTMLParser):
    """Stdlib fallback parser for DuckDuckGo's HTML results page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.results: list[dict[str, str]] = []
        self._capture: str | None = None  # "title" | "snippet"
        self._depth = 0
        self._href = ""
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _VOID_TAGS:
            return
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        if self._capture is None:
            if tag == "a" and "result__a" in classes:
                self._capture, self._depth = "title", 1
                self._href = attributes.get("href") or ""
                self._text = []
            elif "result__snippet" in classes:
                self._capture, self._depth = "snippet", 1
                self._text = []
        else:
            self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._capture is None or tag in _VOID_TAGS:
            return
        self._depth -= 1
        if self._depth > 0:
            return
        text = _clean("".join(self._text))
        if self._capture == "title":
            self.results.append(
                {"title": text, "url": unwrap_redirect(self._href), "snippet": ""}
            )
        elif self.results:
            self.results[-1]["snippet"] = text
        self._capture = None

    def handle_data(self, data: str) -> None:
        if self._capture is not None:
            self._text.append(data)


def _parse_with_selectolax(html: str, tree_cls: type) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    tree = tree_cls(html)
    for block in tree.css("div.result"):
        anchor = block.css_first("a.result__a")
        if anchor is None:
            continue
        snippet = block.css_first(".result__snippet")
        results.append(
            {
                "title": _clean(anchor.text()),
                "url": unwrap_redirect(anchor.attributes.get("href") or ""),
                "snippet": _clean(snippet.text()) if snippet is not None else "",
            }
        )
    return results


def parse_results(html: str, max_results: int = 5) -> list[dict[str, str]]:
    """Parse DuckDuckGo HTML into ``[{"title", "url", "snippet"}]``."""
    try:
        from selectolax.parser import HTMLParser as SelectolaxParser
    except ImportError:
        parser = _DdgHtmlParser()
        parser.feed(html)
        parser.close()
        results = parser.results
    else:
        results = _parse_with_selectolax(html, SelectolaxParser)
    return [r for r in results if r["url"]][: max(1, max_results)]


async def web_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search the web via DuckDuckGo and return title/url/snippet results."""
    if not query.strip():
        raise BrowserError("Cannot search: empty query")
    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=20.0, follow_redirects=True
        ) as client:
            response = await client.get(SEARCH_URL, params={"q": query})
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise BrowserError(f"Web search failed: {exc}", cause=exc) from exc
    return parse_results(response.text, max_results=max_results)
