"""LLM-based image analysis.

:class:`VisionAnalyzer` turns a captured frame into a vision-model request:
downscale the PNG, base64-encode it, attach it to a user message and route
it through the :class:`~jarvis.llm.router.ModelRouter` with
``needs_vision=True`` so a multimodal model is selected.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

from jarvis.llm.base import ImageContent, Message
from jarvis.llm.router import ModelRouter, TaskRequirements
from jarvis.vision.capture import DEFAULT_MAX_DIM, downscale_png, to_base64

if TYPE_CHECKING:
    from jarvis.core.config import VisionConfig

DESCRIBE_SCREEN_PROMPT = "Describe what is currently visible on the screen, concisely."
DESCRIBE_WEBCAM_PROMPT = "Describe what the webcam currently sees, concisely."


class VisionAnalyzer:
    """Answers natural-language questions about images via a vision LLM."""

    def __init__(self, router: ModelRouter, *, max_dim: int = DEFAULT_MAX_DIM) -> None:
        self._router = router
        self._max_dim = max_dim

    async def analyze(
        self,
        png_bytes: bytes,
        question: str,
        config: VisionConfig | None = None,
    ) -> str:
        """Answer ``question`` about the given PNG image.

        ``config`` is accepted for pipeline symmetry and future tuning; the
        current :class:`VisionConfig` fields do not affect LLM analysis.
        """
        image = downscale_png(png_bytes, self._max_dim)
        message = Message.user(
            question,
            images=[ImageContent(media_type="image/png", data_base64=to_base64(image))],
        )
        response = await self._router.chat(
            [message], requirements=TaskRequirements(needs_vision=True)
        )
        return response.content

    async def describe_screen(
        self,
        capture: Callable[[], bytes],
        question: str = DESCRIBE_SCREEN_PROMPT,
        config: VisionConfig | None = None,
    ) -> str:
        """Capture the screen via ``capture()`` (run in a thread) and analyze it."""
        png_bytes = await asyncio.to_thread(capture)
        return await self.analyze(png_bytes, question, config)

    async def describe_webcam(
        self,
        capture: Callable[[], bytes],
        question: str = DESCRIBE_WEBCAM_PROMPT,
        config: VisionConfig | None = None,
    ) -> str:
        """Capture a webcam frame via ``capture()`` (run in a thread) and analyze it."""
        png_bytes = await asyncio.to_thread(capture)
        return await self.analyze(png_bytes, question, config)
