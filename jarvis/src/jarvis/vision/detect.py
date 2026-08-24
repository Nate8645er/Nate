"""Face and object detection.

Faces use OpenCV's bundled Haar cascade. Objects prefer an Ultralytics YOLO
model and fall back to OpenCV's HOG person detector when ``ultralytics`` is
not installed. All heavy dependencies are imported lazily.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.core.errors import VisionError
from jarvis.core.logging import get_logger
from jarvis.vision.capture import require_cv2, require_numpy

logger = get_logger("vision.detect")

_FACE_CASCADE = "haarcascade_frontalface_default.xml"


def _decode_bgr(cv2: Any, np: Any, png_bytes: bytes) -> Any:
    """Decode PNG bytes into a BGR image array or raise a :class:`VisionError`."""
    buffer = np.frombuffer(png_bytes, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise VisionError("Could not decode the image data (not a valid PNG/JPEG?).")
    return image


def detect_faces(png_bytes: bytes) -> list[dict[str, int]]:
    """Detect frontal faces and return ``{x, y, w, h}`` bounding boxes."""
    cv2 = require_cv2()
    np = require_numpy()
    image = _decode_bgr(cv2, np, png_bytes)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade_path = Path(cv2.data.haarcascades) / _FACE_CASCADE
    cascade = cv2.CascadeClassifier(str(cascade_path))
    if cascade.empty():
        raise VisionError(f"Haar cascade '{_FACE_CASCADE}' not found at {cascade_path}.")
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return [{"x": int(x), "y": int(y), "w": int(w), "h": int(h)} for (x, y, w, h) in faces]


def detect_objects(png_bytes: bytes, model_path: str = "yolov8n.pt") -> list[dict[str, Any]]:
    """Detect objects and return ``{label, confidence, box}`` entries.

    Prefers an Ultralytics YOLO model (``model_path``); when ``ultralytics``
    is not installed, falls back to OpenCV's HOG-based person detector, in
    which case every detection is labelled ``"person"`` and ``confidence``
    is the (unnormalised, clamped) SVM weight.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.debug("ultralytics not installed; falling back to the HOG person detector")
        return _detect_people_hog(png_bytes)

    cv2 = require_cv2()
    np = require_numpy()
    image = _decode_bgr(cv2, np, png_bytes)
    try:
        model = YOLO(model_path)
        results = model(image, verbose=False)
    except Exception as exc:
        raise VisionError(f"YOLO inference with '{model_path}' failed: {exc}", cause=exc) from exc

    detections: list[dict[str, Any]] = []
    for result in results:
        names = result.names or {}
        for box in result.boxes:
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            class_id = int(box.cls[0])
            detections.append(
                {
                    "label": str(names.get(class_id, class_id)),
                    "confidence": round(float(box.conf[0]), 4),
                    "box": {"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1},
                }
            )
    return detections


def _detect_people_hog(png_bytes: bytes) -> list[dict[str, Any]]:
    """Detect people with OpenCV's default HOG descriptor (YOLO fallback)."""
    cv2 = require_cv2()
    np = require_numpy()
    image = _decode_bgr(cv2, np, png_bytes)
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    rects, weights = hog.detectMultiScale(image, winStride=(8, 8), padding=(8, 8), scale=1.05)
    detections: list[dict[str, Any]] = []
    for (x, y, w, h), weight in zip(rects, weights, strict=False):
        detections.append(
            {
                "label": "person",
                "confidence": round(min(1.0, float(weight)), 4),
                "box": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
            }
        )
    return detections
