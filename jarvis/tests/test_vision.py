"""Vision subsystem tests.

These tests must pass without the optional vision dependencies
(opencv-python, mss, pytesseract, Pillow) installed: they exercise the
pure-stdlib helpers, the psutil window fallback, graceful degradation of
the registered tools, and the analyzer against a fake model router.
"""

from __future__ import annotations

import base64
import importlib.util
import struct
import zlib
from types import SimpleNamespace
from typing import Any

import pytest

import jarvis.vision as vision
from jarvis.agents.tools import ToolRegistry
from jarvis.core.config import VisionConfig
from jarvis.llm.base import ChatResponse, Message
from jarvis.vision import windows as vision_windows
from jarvis.vision.analyzer import VisionAnalyzer
from jarvis.vision.capture import downscale_png, to_base64

EXPECTED_TOOLS = {
    "vision_screenshot",
    "vision_webcam",
    "vision_ocr",
    "vision_detect_faces",
    "vision_detect_objects",
    "vision_list_windows",
    "vision_analyze",
}


def _png_1x1() -> bytes:
    """Build a valid 1x1 RGB PNG from scratch (no imaging library needed)."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data))
        )

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)  # 1x1, 8-bit, RGB
    idat = zlib.compress(b"\x00\x00\x00\x00")  # filter byte + one black pixel
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", idat)
        + chunk(b"IEND", b"")
    )


def _stub_app() -> SimpleNamespace:
    return SimpleNamespace(
        config=SimpleNamespace(vision=VisionConfig()),
        tools=ToolRegistry(),
        router=object(),
        events=None,
        container=None,
    )


class FakeRouter:
    """Records the chat call and returns a canned vision answer."""

    def __init__(self) -> None:
        self.messages: list[Message] | None = None
        self.requirements: Any = None

    async def chat(
        self,
        messages: list[Message],
        *,
        tools: Any = None,
        options: Any = None,
        requirements: Any = None,
    ) -> ChatResponse:
        self.messages = messages
        self.requirements = requirements
        return ChatResponse(content="a single black pixel")


# -- capture helpers ---------------------------------------------------------------


def test_to_base64_roundtrip() -> None:
    png = _png_1x1()
    encoded = to_base64(png)
    assert isinstance(encoded, str)
    assert base64.b64decode(encoded) == png


def test_downscale_png_returns_original_for_tiny_or_no_pillow() -> None:
    # Without Pillow: passthrough. With Pillow: a 1x1 image is below max_dim,
    # so the original bytes are returned either way.
    png = _png_1x1()
    assert downscale_png(png, max_dim=64) == png


def test_downscale_png_rejects_non_positive_max_dim() -> None:
    with pytest.raises(ValueError):
        downscale_png(_png_1x1(), max_dim=0)


# -- window listing ----------------------------------------------------------------


def test_process_fallback_shape() -> None:
    entries = vision_windows._process_fallback()
    assert entries, "expected at least the test process itself"
    for entry in entries:
        assert set(entry) == {"title", "handle_or_pid", "source"}
        assert entry["source"] == "processes"
        assert isinstance(entry["handle_or_pid"], int)
        assert isinstance(entry["title"], str) and entry["title"]


def test_list_windows_returns_valid_entries() -> None:
    entries = vision_windows.list_windows()
    assert isinstance(entries, list)
    for entry in entries:
        assert set(entry) == {"title", "handle_or_pid", "source"}
        assert entry["source"] in {"pygetwindow", "wmctrl", "processes"}


# -- tool registration -------------------------------------------------------------


def test_register_adds_all_vision_tools() -> None:
    app = _stub_app()
    vision.register(app)
    registered = {tool.name for tool in app.tools.all()}
    assert registered >= EXPECTED_TOOLS
    for tool in app.tools.all():
        assert tool.tags == {"vision"}
        assert tool.source == "vision"
    webcam_tool = app.tools.get("vision_webcam")
    assert webcam_tool is not None
    assert webcam_tool.capability == "vision.webcam"


async def test_vision_screenshot_degrades_gracefully_without_mss() -> None:
    app = _stub_app()
    vision.register(app)
    result = await app.tools.execute("vision_screenshot", {})
    assert isinstance(result, str)
    if importlib.util.find_spec("mss") is None:
        # The handler must return a helpful hint, not a crash/traceback string.
        assert "mss" in result
        assert "pip install" in result
        assert not result.startswith("Error:")
    else:  # pragma: no cover - environment with vision extras installed
        assert "captured" in result or "unavailable" in result


# -- LatestFrames cache ------------------------------------------------------------


def test_latest_frames_tracks_most_recent_source() -> None:
    cache = vision.LatestFrames()
    assert cache.get("last") is None
    cache.store("screen", b"screen-frame")
    cache.store("webcam", b"webcam-frame")
    assert cache.get("screen") == b"screen-frame"
    assert cache.get("webcam") == b"webcam-frame"
    assert cache.get("last") == b"webcam-frame"


# -- analyzer ----------------------------------------------------------------------


async def test_analyzer_requests_vision_model_and_returns_answer() -> None:
    router = FakeRouter()
    analyzer = VisionAnalyzer(router)  # type: ignore[arg-type]
    png = _png_1x1()

    answer = await analyzer.analyze(png, "What is in this image?", VisionConfig())

    assert answer == "a single black pixel"
    assert router.requirements is not None
    assert router.requirements.needs_vision is True
    assert router.messages is not None and len(router.messages) == 1
    message = router.messages[0]
    assert message.content == "What is in this image?"
    assert len(message.images) == 1
    assert message.images[0].media_type == "image/png"
    assert base64.b64decode(message.images[0].data_base64) == png


async def test_analyzer_describe_screen_uses_capture_callable() -> None:
    router = FakeRouter()
    analyzer = VisionAnalyzer(router)  # type: ignore[arg-type]
    png = _png_1x1()

    answer = await analyzer.describe_screen(lambda: png)

    assert answer == "a single black pixel"
    assert router.messages is not None
    assert base64.b64decode(router.messages[0].images[0].data_base64) == png
