"""Tests for the browser subsystem (no network, no Playwright required)."""

from __future__ import annotations

from types import SimpleNamespace

from jarvis.agents.tools import ToolRegistry
from jarvis.browser.scrape import extract_links, extract_text
from jarvis.browser.search import parse_results, unwrap_redirect
from jarvis.core.config import JarvisConfig
from jarvis.core.container import ServiceContainer
from jarvis.core.events import EventBus
from jarvis.core.security import PermissionManager

DDG_FIXTURE = """
<html><body>
<div class="result results_links results_links_deep web-result">
  <h2 class="result__title">
    <a rel="nofollow" class="result__a"
       href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fjarvis&amp;rut=abc">
      JARVIS assistant — official site</a>
  </h2>
  <a class="result__snippet" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fjarvis">
    An open source <b>JARVIS</b> style assistant.</a>
</div>
<div class="result web-result">
  <h2 class="result__title">
    <a rel="nofollow" class="result__a" href="https://other.org/page">Second result</a>
  </h2>
  <a class="result__snippet" href="https://other.org/page">Another snippet here.</a>
</div>
</body></html>
"""

SAMPLE_HTML = """
<html><head><title>t</title><style>body{color:red}</style>
<script>var ignored = 1;</script></head>
<body><h1>Arc  Reactor</h1><p>Powers the   suit.</p>
<a href="/docs">Docs</a><a href="https://abs.example.com/x">Abs</a></body></html>
"""


class TestSearchParsing:
    def test_unwrap_redirect(self) -> None:
        wrapped = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fjarvis&rut=abc"
        assert unwrap_redirect(wrapped) == "https://example.com/jarvis"
        assert unwrap_redirect("https://plain.org/x") == "https://plain.org/x"

    def test_parse_results_fixture(self) -> None:
        results = parse_results(DDG_FIXTURE, max_results=5)
        assert len(results) == 2
        assert results[0]["title"].startswith("JARVIS assistant")
        assert results[0]["url"] == "https://example.com/jarvis"
        assert "assistant" in results[0]["snippet"].lower() or results[0]["snippet"]
        assert results[1]["url"] == "https://other.org/page"

    def test_parse_results_limit(self) -> None:
        assert len(parse_results(DDG_FIXTURE, max_results=1)) == 1


class TestScrape:
    def test_extract_text_strips_script_and_style(self) -> None:
        text = extract_text(SAMPLE_HTML)
        assert "Arc Reactor" in text
        assert "Powers the suit." in text
        assert "ignored" not in text
        assert "color:red" not in text

    def test_extract_text_truncation(self) -> None:
        assert len(extract_text(SAMPLE_HTML, max_chars=10)) <= 10

    def test_extract_links_resolves_relative(self) -> None:
        links = extract_links(SAMPLE_HTML, "https://example.com/base/")
        hrefs = {link["href"] for link in links}
        assert "https://example.com/docs" in hrefs
        assert "https://abs.example.com/x" in hrefs


class TestRegister:
    async def test_register_tools_and_graceful_playwright_error(self, config: JarvisConfig) -> None:
        import jarvis.browser as browser_pkg

        permissions = PermissionManager(config)
        tools = ToolRegistry(permissions)
        app = SimpleNamespace(
            config=config,
            tools=tools,
            events=EventBus(),
            container=ServiceContainer(),
            permissions=permissions,
        )
        browser_pkg.register(app)
        names = {t.name for t in tools.all()}
        assert {
            "web_search",
            "web_fetch",
            "browser_goto",
            "browser_read_page",
            "browser_click",
            "browser_fill",
            "browser_submit",
            "browser_screenshot",
            "browser_download",
            "browser_links",
            "browser_back",
        } <= names
        # Form tools are permission-gated.
        fill_tool = tools.get("browser_fill")
        assert fill_tool is not None and fill_tool.capability == "browser.forms"
        # Without Playwright installed the tool reports a helpful error string.
        result = await tools.execute("browser_goto", {"url": "https://example.com"})
        assert isinstance(result, str)
        assert result.lower().startswith("error") or "playwright" in result.lower()
