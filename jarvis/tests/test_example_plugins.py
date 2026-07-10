"""Tests for the bundled example plugins (loaded from the repo plugins/ dir)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from jarvis.agents.tools import ToolRegistry
from jarvis.core.config import JarvisConfig
from jarvis.core.events import EventBus
from jarvis.plugins.api import PluginContext
from jarvis.plugins.loader import PluginLoader

REPO_PLUGINS = Path(__file__).resolve().parent.parent / "plugins"


@pytest.fixture()
async def loaded(config: JarvisConfig):
    tools = ToolRegistry()
    events = EventBus()

    def factory(name: str) -> PluginContext:
        return PluginContext(
            config=config, tools=tools, events=events, router=None, _plugin_name=name
        )

    loader = PluginLoader(factory, [REPO_PLUGINS])
    names = await loader.load_all()
    yield names, tools, events, loader
    await loader.unload_all()


class TestExamplePlugins:
    async def test_all_examples_load(self, loaded) -> None:
        names, tools, _, _ = loaded
        assert {"weather", "system_info", "timer"} <= set(names)
        tool_names = {t.name for t in tools.all()}
        assert {"weather_current", "system_overview", "timer_set"} <= tool_names

    async def test_system_overview_runs(self, loaded) -> None:
        _, tools, _, _ = loaded
        result = await tools.execute("system_overview", {})
        assert "OS:" in result

    async def test_timer_lifecycle_and_event(self, loaded) -> None:
        _, tools, events, _ = loaded
        finished = asyncio.Event()
        events.subscribe("timer.finished", lambda e: finished.set())
        result = await tools.execute("timer_set", {"seconds": 1, "label": "tea"})
        assert "Timer #" in result
        assert "tea" in await tools.execute("timer_list", {})
        await asyncio.wait_for(finished.wait(), timeout=5)
        assert "No timers" in await tools.execute("timer_list", {})

    async def test_timer_cancel_and_validation(self, loaded) -> None:
        _, tools, _, _ = loaded
        await tools.execute("timer_set", {"seconds": 60, "label": "long"})
        listing = await tools.execute("timer_list", {})
        timer_id = int(listing.split("#")[1].split(":")[0])
        assert "cancelled" in await tools.execute("timer_cancel", {"timer_id": timer_id})
        assert "must be between" in await tools.execute("timer_set", {"seconds": 0})
