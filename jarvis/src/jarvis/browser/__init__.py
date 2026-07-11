"""Browser subsystem: Playwright control, web search and lightweight scraping.

:func:`register` wires the browser tools into the application. Playwright is
imported lazily by the controller, so this package always imports; tools that
need a real browser return a clear error string when Playwright is missing.
``web_search`` and ``web_fetch`` only need httpx and work everywhere.
"""

from __future__ import annotations

import functools
from datetime import datetime
from typing import TYPE_CHECKING, Any

from jarvis.browser import scrape, search
from jarvis.browser.controller import BrowserController
from jarvis.core.errors import BrowserError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from jarvis.app import JarvisApp

__all__ = ["BrowserController", "register"]

_STR = {"type": "string"}
_INT = {"type": "integer"}


def _params(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def _safe(handler: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """Turn :class:`BrowserError` raised by *handler* into a readable string."""

    @functools.wraps(handler)
    async def wrapper(**kwargs: Any) -> Any:
        try:
            return await handler(**kwargs)
        except BrowserError as exc:
            return f"Error: {exc.message}"

    return wrapper


def register(app: JarvisApp) -> None:
    """Register the browser controller and all browser tools on *app*."""
    controller = BrowserController(app.config)
    app.container.register_instance(BrowserController, controller)
    app.container.on_close(controller.aclose)
    container = app.container
    tools = app.tools

    def _controller() -> BrowserController:
        return container.resolve(BrowserController)

    # -- browserless research tools -------------------------------------------

    async def web_search(query: str, max_results: int = 5) -> Any:
        return await search.web_search(query, max_results=max_results)

    tools.register_function(
        "web_search",
        "Search the web (DuckDuckGo) and return results as title, url and snippet.",
        _safe(web_search),
        parameters=_params({"query": _STR, "max_results": _INT}, ["query"]),
        tags={"browser", "search"},
        source="browser",
    )

    async def web_fetch(url: str, max_chars: int = 8000) -> str:
        html = await scrape.fetch_page(url)
        return scrape.extract_text(html, max_chars=max_chars) or "(page has no visible text)"

    tools.register_function(
        "web_fetch",
        "Fetch a web page over HTTP and return its readable text (no browser needed).",
        _safe(web_fetch),
        parameters=_params({"url": _STR, "max_chars": _INT}, ["url"]),
        tags={"browser", "search"},
        source="browser",
    )

    # -- interactive browser tools ----------------------------------------------

    async def browser_goto(url: str) -> Any:
        return await _controller().goto(url)

    tools.register_function(
        "browser_goto",
        "Open a URL in the controlled browser; returns the page title and final URL.",
        _safe(browser_goto),
        parameters=_params({"url": _STR}, ["url"]),
        tags={"browser"},
        source="browser",
    )

    async def browser_read_page(max_chars: int = 8000) -> str:
        return await _controller().page_text(max_chars=max_chars)

    tools.register_function(
        "browser_read_page",
        "Read the visible text of the current browser page.",
        _safe(browser_read_page),
        parameters=_params({"max_chars": _INT}),
        tags={"browser"},
        source="browser",
    )

    async def browser_click(target: str) -> str:
        return await _controller().click(target)

    tools.register_function(
        "browser_click",
        "Click an element on the current page by CSS selector or visible text.",
        _safe(browser_click),
        parameters=_params({"target": _STR}, ["target"]),
        tags={"browser"},
        source="browser",
    )

    async def browser_fill(selector: str, value: str) -> str:
        return await _controller().fill(selector, value)

    tools.register_function(
        "browser_fill",
        "Fill a form field (CSS selector) with a value.",
        _safe(browser_fill),
        parameters=_params({"selector": _STR, "value": _STR}, ["selector", "value"]),
        tags={"browser"},
        capability="browser.forms",
        source="browser",
    )

    async def browser_submit(selector: str = "") -> str:
        return await _controller().submit(selector)

    tools.register_function(
        "browser_submit",
        "Submit a form: click the given selector, or press Enter if none is given.",
        _safe(browser_submit),
        parameters=_params({"selector": _STR}),
        tags={"browser"},
        capability="browser.forms",
        source="browser",
    )

    async def browser_screenshot() -> str:
        ctl = _controller()
        data = await ctl.screenshot()
        ctl.downloads_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = ctl.downloads_dir / f"screenshot-{stamp}.png"
        target.write_bytes(data)
        return f"Screenshot saved to {target}"

    tools.register_function(
        "browser_screenshot",
        "Take a PNG screenshot of the current browser page and save it to disk.",
        _safe(browser_screenshot),
        tags={"browser"},
        source="browser",
    )

    async def browser_download(url: str) -> str:
        saved = await _controller().download(url)
        return f"Downloaded to {saved}"

    tools.register_function(
        "browser_download",
        "Download a file from a URL into the downloads directory.",
        _safe(browser_download),
        parameters=_params({"url": _STR}, ["url"]),
        tags={"browser"},
        capability="browser.download",
        source="browser",
    )

    async def browser_links(limit: int = 50) -> Any:
        return await _controller().list_links(limit=limit)

    tools.register_function(
        "browser_links",
        "List the links (text and href) on the current browser page.",
        _safe(browser_links),
        parameters=_params({"limit": _INT}),
        tags={"browser"},
        source="browser",
    )

    async def browser_back() -> Any:
        return await _controller().back()

    tools.register_function(
        "browser_back",
        "Go back one step in the browser history.",
        _safe(browser_back),
        tags={"browser"},
        source="browser",
    )
