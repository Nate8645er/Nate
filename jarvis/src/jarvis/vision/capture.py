"""Screen and webcam capture.

All third-party dependencies (``mss``, ``opencv-python``, ``Pillow``) are
imported lazily so the module can always be imported; helpful
:class:`~jarvis.core.errors.VisionError` messages with install hints are
raised only when a capture is actually attempted without the dependency.
"""

from __future__ import annotations

import base64
import io
from typing import Any

from jarvis.core.errors import VisionError
from jarvis.core.logging import get_logger

logger = get_logger("vision.capture")

#: Default longest-edge size used when downscaling frames for LLM analysis.
DEFAULT_MAX_DIM = 1568

_INSTALL_HINT = "Install the vision extras: pip install 'jarvis-assistant[vision]'"


def require_mss() -> Any:
    """Import and return the ``mss`` package or raise a :class:`VisionError`."""
    try:
        import mss
        import mss.tools
    except ImportError as exc:
        raise VisionError(
            f"Screen capture needs the 'mss' package. {_INSTALL_HINT} (or: pip install mss).",
            cause=exc,
        ) from exc
    return mss


def require_cv2() -> Any:
    """Import and return OpenCV (``cv2``) or raise a :class:`VisionError`."""
    try:
        import cv2
    except ImportError as exc:
        raise VisionError(
            f"This feature needs OpenCV. {_INSTALL_HINT} (or: pip install opencv-python).",
            cause=exc,
        ) from exc
    return cv2


def require_numpy() -> Any:
    """Import and return ``numpy`` or raise a :class:`VisionError`."""
    try:
        import numpy
    except ImportError as exc:
        raise VisionError(
            f"This feature needs numpy. {_INSTALL_HINT} (or: pip install numpy).",
            cause=exc,
        ) from exc
    return numpy


class ScreenCapture:
    """Captures screenshots of one monitor (or all combined) as PNG bytes."""

    def list_monitors(self) -> list[dict[str, int]]:
        """Return available monitors as ``{index, left, top, width, height}``.

        Index 0 is the virtual monitor spanning all displays; physical
        monitors start at index 1 (mss convention).
        """
        mss_mod = require_mss()
        try:
            with mss_mod.mss() as sct:
                return [{"index": i, **monitor} for i, monitor in enumerate(sct.monitors)]
        except VisionError:
            raise
        except Exception as exc:
            raise VisionError(f"Could not enumerate monitors: {exc}", cause=exc) from exc

    def capture(self, monitor_index: int = 0) -> bytes:
        """Capture ``monitor_index`` (0 = all monitors combined) as PNG bytes."""
        mss_mod = require_mss()
        try:
            with mss_mod.mss() as sct:
                monitors = sct.monitors
                if not 0 <= monitor_index < len(monitors):
                    raise VisionError(
                        f"Monitor index {monitor_index} out of range "
                        f"(0..{len(monitors) - 1} available)."
                    )
                shot = sct.grab(monitors[monitor_index])
                return mss_mod.tools.to_png(shot.rgb, shot.size)
        except VisionError:
            raise
        except Exception as exc:
            raise VisionError(f"Screen capture failed: {exc}", cause=exc) from exc


class WebcamCapture:
    """Grabs single frames from a webcam as PNG bytes."""

    def capture(self, camera_index: int = 0) -> bytes:
        """Capture one frame from camera ``camera_index`` and return PNG bytes."""
        cv2 = require_cv2()
        cam = cv2.VideoCapture(camera_index)
        try:
            if not cam.isOpened():
                raise VisionError(
                    f"Cannot open camera {camera_index}. "
                    "Check that a webcam is connected and not in use by another application."
                )
            ok, frame = cam.read()
            if not ok or frame is None:
                raise VisionError(f"Camera {camera_index} did not deliver a frame.")
            ok, buffer = cv2.imencode(".png", frame)
            if not ok:
                raise VisionError("PNG encoding of the webcam frame failed.")
            return bytes(buffer.tobytes())
        except VisionError:
            raise
        except Exception as exc:
            raise VisionError(f"Webcam capture failed: {exc}", cause=exc) from exc
        finally:
            cam.release()


def to_base64(png_bytes: bytes) -> str:
    """Encode PNG bytes as an ASCII base64 string (for LLM image content)."""
    return base64.b64encode(png_bytes).decode("ascii")


def downscale_png(png_bytes: bytes, max_dim: int = DEFAULT_MAX_DIM) -> bytes:
    """Downscale a PNG so its longest edge is at most ``max_dim`` pixels.

    Uses Pillow when available; when Pillow is missing or the image cannot
    be processed, the original bytes are returned unchanged (best effort —
    analysis should still proceed with the full-size image).
    """
    if max_dim <= 0:
        raise ValueError("max_dim must be a positive number of pixels")
    try:
        from PIL import Image
    except ImportError:
        logger.debug("Pillow not installed; skipping downscaling")
        return png_bytes
    try:
        with Image.open(io.BytesIO(png_bytes)) as image:
            if max(image.size) <= max_dim:
                return png_bytes
            image.thumbnail((max_dim, max_dim))
            out = io.BytesIO()
            image.save(out, format="PNG")
            return out.getvalue()
    except Exception:
        logger.debug("Downscaling failed; using the original image", exc_info=True)
        return png_bytes
