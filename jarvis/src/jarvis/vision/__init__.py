"""Vision subsystem: screen/webcam capture, OCR, detection and LLM analysis.

Exposes the standard subsystem hook :func:`register`, which adds the
``vision_*`` tools to the application's tool registry. All optional
third-party dependencies are imported lazily inside the individual modules,
so registration always succeeds and tool calls return helpful install hints
instead of crashing when a dependency is missing.
"""

from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING, Any

from jarvis.core.errors import VisionError
from jarvis.core.logging import get_logger

if TYPE_CHECKING:
    from jarvis.app import JarvisApp

logger = get_logger("vision")

_SOURCES = ("screen", "webcam", "last")


class LatestFrames:
    """Thread-safe cache of the most recent capture per source.

    Tool handlers run in worker threads, so access is guarded by a lock.
    ``get("last")`` returns whichever frame was stored most recently.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._frames: dict[str, bytes] = {}
        self._last_source: str | None = None

    def store(self, source: str, png_bytes: bytes) -> None:
        """Remember ``png_bytes`` as the latest frame from ``source``."""
        with self._lock:
            self._frames[source] = png_bytes
            self._last_source = source

    def get(self, source: str = "last") -> bytes | None:
        """Return the cached frame for ``source`` (or the most recent one)."""
        with self._lock:
            key = self._last_source if source == "last" else source
            return self._frames.get(key) if key else None


#: Module-level cache shared by all vision tools of this process.
frames = LatestFrames()


def register(app: JarvisApp) -> None:
    """Register the vision tools on the application (subsystem hook)."""
    from jarvis.vision import detect, ocr, windows
    from jarvis.vision.analyzer import VisionAnalyzer
    from jarvis.vision.capture import ScreenCapture, WebcamCapture

    cfg = app.config.vision
    screen = ScreenCapture()
    webcam = WebcamCapture()
    analyzer = VisionAnalyzer(app.router)

    def _fresh_frame(source: str) -> bytes:
        """Capture a new frame from ``source`` and cache it."""
        if source == "screen":
            png_bytes = screen.capture()
        elif source == "webcam":
            png_bytes = webcam.capture(cfg.camera_index)
        else:
            raise VisionError(f"Unknown capture source '{source}' (use 'screen' or 'webcam').")
        frames.store(source, png_bytes)
        return png_bytes

    def _frame_for(source: str) -> bytes:
        """Return the cached frame for 'last', otherwise capture a fresh one."""
        if source == "last":
            png_bytes = frames.get("last")
            if png_bytes is None:
                raise VisionError(
                    "No frame captured yet. Take a screenshot or webcam photo first."
                )
            return png_bytes
        if source not in _SOURCES:
            raise VisionError(f"Unknown source '{source}' (use one of {', '.join(_SOURCES)}).")
        return _fresh_frame(source)

    # -- tool handlers (never raise for missing optional dependencies) -------------

    def vision_screenshot(monitor_index: int = 0) -> str:
        try:
            png_bytes = screen.capture(monitor_index)
        except VisionError as exc:
            return f"Screenshot unavailable: {exc.message}"
        frames.store("screen", png_bytes)
        return (
            f"Screenshot of monitor {monitor_index} captured ({len(png_bytes)} bytes). "
            "Stored as the latest frame for OCR, detection and analysis."
        )

    def vision_webcam(camera_index: int | None = None) -> str:
        index = cfg.camera_index if camera_index is None else camera_index
        try:
            png_bytes = webcam.capture(index)
        except VisionError as exc:
            return f"Webcam capture unavailable: {exc.message}"
        frames.store("webcam", png_bytes)
        return (
            f"Webcam frame from camera {index} captured ({len(png_bytes)} bytes). "
            "Stored as the latest frame for OCR, detection and analysis."
        )

    def vision_ocr(source: str = "screen", languages: str | None = None) -> str:
        try:
            png_bytes = _frame_for(source)
            text = ocr.extract_text(png_bytes, languages or cfg.ocr_languages)
        except VisionError as exc:
            return f"OCR unavailable: {exc.message}"
        return text or "No text detected in the image."

    def vision_detect_faces(source: str = "screen") -> Any:
        if not cfg.face_detection:
            return "Face detection is disabled in the configuration (vision.face_detection)."
        try:
            faces = detect.detect_faces(_frame_for(source))
        except VisionError as exc:
            return f"Face detection unavailable: {exc.message}"
        return faces or "No faces detected."

    def vision_detect_objects(source: str = "screen", model_path: str | None = None) -> Any:
        try:
            objects = detect.detect_objects(
                _frame_for(source), model_path or cfg.object_detection_model
            )
        except VisionError as exc:
            return f"Object detection unavailable: {exc.message}"
        return objects or "No objects detected."

    def vision_list_windows() -> Any:
        try:
            return windows.list_windows()
        except VisionError as exc:
            return f"Window listing unavailable: {exc.message}"

    async def vision_analyze(question: str, source: str = "screen") -> str:
        try:
            png_bytes = await asyncio.to_thread(_frame_for, source)
            return await analyzer.analyze(png_bytes, question, cfg)
        except VisionError as exc:
            return f"Vision analysis unavailable: {exc.message}"

    # -- registration ----------------------------------------------------------------

    source_param = {
        "type": "string",
        "enum": list(_SOURCES),
        "description": "Image source: fresh 'screen'/'webcam' capture, or the cached 'last' frame.",
        "default": "screen",
    }

    app.tools.register_function(
        "vision_screenshot",
        "Take a screenshot and cache it as the latest frame for OCR, detection and analysis.",
        vision_screenshot,
        parameters={
            "type": "object",
            "properties": {
                "monitor_index": {
                    "type": "integer",
                    "description": "Monitor to capture (0 = all monitors combined).",
                    "default": 0,
                }
            },
        },
        tags={"vision"},
        source="vision",
    )
    app.tools.register_function(
        "vision_webcam",
        "Capture a webcam photo and cache it as the latest frame for OCR, detection and analysis.",
        vision_webcam,
        parameters={
            "type": "object",
            "properties": {
                "camera_index": {
                    "type": "integer",
                    "description": "Camera to use (defaults to the configured camera).",
                }
            },
        },
        tags={"vision"},
        capability="vision.webcam",
        source="vision",
    )
    app.tools.register_function(
        "vision_ocr",
        "Extract text from the latest frame or a fresh screenshot via Tesseract OCR.",
        vision_ocr,
        parameters={
            "type": "object",
            "properties": {
                "source": source_param,
                "languages": {
                    "type": "string",
                    "description": "Tesseract language spec, e.g. 'eng' or 'eng+deu' "
                    "(defaults to the configured languages).",
                },
            },
        },
        tags={"vision"},
        source="vision",
    )
    app.tools.register_function(
        "vision_detect_faces",
        "Detect faces in the latest frame or a fresh capture; returns bounding boxes.",
        vision_detect_faces,
        parameters={"type": "object", "properties": {"source": source_param}},
        tags={"vision"},
        source="vision",
    )
    app.tools.register_function(
        "vision_detect_objects",
        "Detect objects (YOLO, or HOG person detector fallback) in the latest frame "
        "or a fresh capture.",
        vision_detect_objects,
        parameters={
            "type": "object",
            "properties": {
                "source": source_param,
                "model_path": {
                    "type": "string",
                    "description": "YOLO model path/name (defaults to the configured model).",
                },
            },
        },
        tags={"vision"},
        source="vision",
    )
    app.tools.register_function(
        "vision_list_windows",
        "List open windows (or running processes as a fallback) with titles and handles/PIDs.",
        vision_list_windows,
        parameters={"type": "object", "properties": {}},
        tags={"vision"},
        source="vision",
    )
    app.tools.register_function(
        "vision_analyze",
        "Answer a question about the screen, webcam or last captured frame using a vision LLM.",
        vision_analyze,
        parameters={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "What to determine or describe about the image.",
                },
                "source": source_param,
            },
            "required": ["question"],
        },
        tags={"vision"},
        source="vision",
    )
    logger.info("Vision subsystem registered (7 tools)")
