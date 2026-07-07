from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.config import Settings
from jarvis.kernel import Kernel


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        data_dir=tmp_path / "data",
        plugins_dir=tmp_path / "plugins",
        workflows_dir=tmp_path / "workflows",
        voice_enabled=False,
        vector_backend="naive",
        llm_provider="echo",
        approval_threshold=3,  # tests never block on approvals unless they opt in
        approval_timeout_seconds=0.5,
    )


@pytest.fixture
async def kernel(test_settings: Settings) -> Kernel:
    k = Kernel(test_settings)
    await k.start()
    yield k
    await k.stop()
