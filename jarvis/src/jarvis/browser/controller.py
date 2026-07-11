"""Playwright-based browser controller.

Playwright is imported lazily inside :meth:`BrowserController.ensure_started`
so the module (and the whole browser subsystem) imports without the optional
dependency; a missing install surfaces as a :class:`BrowserError` with an
install hint. One browser + one context are shared across all tool calls.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
from pathlib import Path
from typing import Any, TypeVar
from urllib.parse import urlsplit

from jarvis.core.config import JarvisConfig
from jarvis.core.errors import BrowserError

T = TypeVar("T")

_INSTALL_HINT = (
    "playwright is not installed. Install it with: "
    "pip install 'jarvis-assistant[browser]' && playwright install chromium"
)


def _guard(description: str) -> Any:
    """Decorator: start the browser, translate failures into BrowserError."""

    def decorator(method: Any) -> Any:
        @functools.wraps(method)
        async def wrapper(self: BrowserController, *args: Any, **kwargs: Any) -> Any:
            await self.ensure_started()
            try:
                return await method(self, *args, **kwargs)
            except BrowserError:
                raise
            except Exception as exc:
                raise BrowserError(f"{description}: {exc}", cause=exc) from exc

        return wrapper

    return decorator


def _normalize_url(url: str) -> str:
    return url if urlsplit(url).scheme else f"https://{url}"


class BrowserController:
    """Owns one Playwright browser, one context and the current page."""

    def __init__(self, config: JarvisConfig) -> None:
        self._config = config.browser
        self._downloads_dir: Path = config.resolve_path(config.browser.downloads_dir)
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._page: Any = None
        self._lock = asyncio.Lock()

    @property
    def timeout_ms(self) -> int:
        """Default operation timeout in milliseconds (from config)."""
        return self._config.default_timeout_ms

    @property
    def downloads_dir(self) -> Path:
        """Directory that receives downloads and screenshots."""
        return self._downloads_dir

    # -- lifecycle -------------------------------------------------------------

    async def ensure_started(self) -> None:
        """Launch the configured browser on first use (idempotent)."""
        async with self._lock:
            if self._page is not None:
                return
            if self._context is not None:  # page was closed, context lives on
                self._page = await self._context.new_page()
                return
            try:
                from playwright.async_api import async_playwright
            except ImportError as exc:
                raise BrowserError(_INSTALL_HINT, cause=exc) from exc
            try:
                self._downloads_dir.mkdir(parents=True, exist_ok=True)
                self._playwright = await async_playwright().start()
                launcher = getattr(self._playwright, self._config.browser)
                launch_kwargs: dict[str, Any] = {
                    "headless": self._config.headless,
                    "downloads_path": str(self._downloads_dir),
                }
                if self._config.executable_path:
                    launch_kwargs["executable_path"] = self._config.executable_path
                self._browser = await launcher.launch(**launch_kwargs)
                context_kwargs: dict[str, Any] = {"accept_downloads": True}
                if self._config.user_agent:
                    context_kwargs["user_agent"] = self._config.user_agent
                self._context = await self._browser.new_context(**context_kwargs)
                self._context.set_default_timeout(self._config.default_timeout_ms)
                self._page = await self._context.new_page()
            except Exception as exc:
                await self._cleanup()
                raise BrowserError(f"Failed to start browser: {exc}", cause=exc) from exc

    async def aclose(self) -> None:
        """Shut down the page, context, browser and Playwright driver."""
        async with self._lock:
            await self._cleanup()

    async def _cleanup(self) -> None:
        for closable in (self._context, self._browser):
            if closable is not None:
                with contextlib.suppress(Exception):
                    await closable.close()
        if self._playwright is not None:
            with contextlib.suppress(Exception):
                await self._playwright.stop()
        self._page = self._context = self._browser = self._playwright = None

    # -- navigation --------------------------------------------------------------

    @_guard("Navigation failed")
    async def goto(self, url: str) -> dict[str, str]:
        """Navigate to *url* and return the resulting title and final URL."""
        await self._page.goto(_normalize_url(url), wait_until="domcontentloaded")
        return {"title": await self._page.title(), "url": self._page.url}

    @_guard("Could not navigate back")
    async def back(self) -> dict[str, str]:
        """Go back in the page history."""
        await self._page.go_back(wait_until="domcontentloaded")
        return {"title": await self._page.title(), "url": self._page.url}

    @_guard("Could not open a new page")
    async def new_page(self) -> str:
        """Open a fresh page (tab) and make it current."""
        self._page = await self._context.new_page()
        return "Opened a new page"

    async def close_page(self) -> str:
        """Close the current page; falls back to another open page if any."""
        if self._page is None:
            return "No page open"
        with contextlib.suppress(Exception):
            await self._page.close()
        pages = list(self._context.pages) if self._context is not None else []
        self._page = pages[-1] if pages else None
        return "Page closed"

    # -- reading -------------------------------------------------------------------

    @_guard("Could not read page text")
    async def page_text(self, max_chars: int = 8000) -> str:
        """Return the visible text of the current page (body inner_text)."""
        text = await self._page.inner_text("body")
        return " ".join(text.split())[:max_chars]

    @_guard("Could not read page HTML")
    async def page_html(self, max_chars: int = 20_000) -> str:
        """Return the current page HTML, truncated to *max_chars*."""
        return (await self._page.content())[:max_chars]

    @_guard("Could not list links")
    async def list_links(self, limit: int = 50) -> list[dict[str, str]]:
        """Return up to *limit* links on the current page as text/href pairs."""
        raw = await self._page.evaluate(
            "() => Array.from(document.querySelectorAll('a[href]'))"
            ".map(a => ({text: (a.innerText || '').trim(), href: a.href}))"
        )
        links = [
            {"text": item["text"][:120], "href": item["href"]}
            for item in raw
            if item.get("href")
        ]
        return links[:limit]

    @_guard("Screenshot failed")
    async def screenshot(self) -> bytes:
        """Take a PNG screenshot of the current viewport."""
        return await self._page.screenshot(type="png")

    # -- interaction ----------------------------------------------------------------

    async def click(self, target: str) -> str:
        """Click an element by CSS selector, falling back to visible text match."""
        await self.ensure_started()
        try:
            await self._page.click(target)
            return f"Clicked '{target}'"
        except BrowserError:
            raise
        except Exception:
            try:
                await self._page.get_by_text(target).first.click()
                return f"Clicked element containing text '{target}'"
            except Exception as exc:
                raise BrowserError(f"Could not click '{target}': {exc}", cause=exc) from exc

    @_guard("Could not fill field")
    async def fill(self, selector: str, value: str) -> str:
        """Fill a form field identified by CSS selector."""
        await self._page.fill(selector, value)
        return f"Filled '{selector}'"

    @_guard("Could not select option")
    async def select(self, selector: str, value: str) -> str:
        """Choose an option of a <select> element by value."""
        await self._page.select_option(selector, value)
        return f"Selected '{value}' in '{selector}'"

    @_guard("Could not submit")
    async def submit(self, selector: str = "") -> str:
        """Submit a form: click *selector* if given, otherwise press Enter."""
        if selector:
            await self._page.click(selector)
        else:
            await self._page.keyboard.press("Enter")
        with contextlib.suppress(Exception):
            await self._page.wait_for_load_state("domcontentloaded")
        return f"Submitted; now at {self._page.url}"

    @_guard("JavaScript evaluation failed")
    async def evaluate(self, script: str) -> Any:
        """Evaluate JavaScript in the page and return the (JSON-safe) result."""
        return await self._page.evaluate(script)

    # -- downloads --------------------------------------------------------------------

    @_guard("Download failed")
    async def download(self, url: str) -> str:
        """Download *url* using the browser context and return the saved path."""
        response = await self._context.request.get(_normalize_url(url))
        if not response.ok:
            raise BrowserError(f"Download failed with HTTP {response.status}: {url}")
        self._downloads_dir.mkdir(parents=True, exist_ok=True)
        name = Path(urlsplit(url).path).name or "download"
        target = self._downloads_dir / name
        counter = 1
        while target.exists():
            target = self._downloads_dir / f"{Path(name).stem}-{counter}{Path(name).suffix}"
            counter += 1
        target.write_bytes(await response.body())
        return str(target)
