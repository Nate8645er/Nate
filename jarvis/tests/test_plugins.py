"""Tests for the plugin system: loader, REST plugins, MCP content rendering."""

from __future__ import annotations

import textwrap
from pathlib import Path

import httpx
import respx

from jarvis.agents.tools import ToolRegistry
from jarvis.core.config import JarvisConfig
from jarvis.core.events import EventBus
from jarvis.plugins.api import PluginContext
from jarvis.plugins.loader import PluginLoader
from jarvis.plugins.mcp import _render_content
from jarvis.plugins.rest import RestPluginLoader, _substitute


def _write_plugin(directory: Path, name: str, body: str) -> Path:
    plugin_dir = directory / name
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.py").write_text(textwrap.dedent(body), encoding="utf-8")
    return plugin_dir


def _make_loader(config: JarvisConfig, tools: ToolRegistry, directory: Path) -> PluginLoader:
    def factory(name: str) -> PluginContext:
        return PluginContext(
            config=config, tools=tools, events=EventBus(), router=None, _plugin_name=name
        )

    return PluginLoader(factory, [directory])


PLUGIN_SRC = """
    from jarvis.plugins.api import Plugin, PluginContext, PluginManifest

    class GreeterPlugin(Plugin):
        manifest = PluginManifest(name="greeter", version="1.0.0", description="greets")

        async def setup(self, context: PluginContext) -> None:
            context.register_tool(
                "greet", "Say hello", lambda name: f"Hello {name}!",
                parameters={"type": "object", "properties": {"name": {"type": "string"}},
                            "required": ["name"]},
            )
"""


class TestPluginLoader:
    async def test_load_execute_unload(self, config: JarvisConfig, tmp_path) -> None:
        tools = ToolRegistry()
        _write_plugin(tmp_path, "greeter", PLUGIN_SRC)
        loader = _make_loader(config, tools, tmp_path)
        names = await loader.load_all()
        assert names == ["greeter"]
        assert await tools.execute("greet", {"name": "Nate"}) == "Hello Nate!"
        assert await loader.unload("greeter")
        assert tools.get("greet") is None

    async def test_reload_replaces_tools(self, config: JarvisConfig, tmp_path) -> None:
        tools = ToolRegistry()
        plugin_dir = _write_plugin(tmp_path, "greeter", PLUGIN_SRC)
        loader = _make_loader(config, tools, tmp_path)
        await loader.load_all()
        (plugin_dir / "plugin.py").write_text(
            (plugin_dir / "plugin.py").read_text().replace("Hello", "Servus"), encoding="utf-8"
        )
        await loader.reload("greeter")
        assert await tools.execute("greet", {"name": "Nate"}) == "Servus Nate!"

    async def test_broken_plugin_skipped(self, config: JarvisConfig, tmp_path) -> None:
        tools = ToolRegistry()
        _write_plugin(tmp_path, "broken", "import nonexistent_module_xyz\n")
        _write_plugin(tmp_path, "greeter", PLUGIN_SRC)
        loader = _make_loader(config, tools, tmp_path)
        names = await loader.load_all()
        assert names == ["greeter"]

    async def test_manifest_yaml_override(self, config: JarvisConfig, tmp_path) -> None:
        tools = ToolRegistry()
        plugin_dir = _write_plugin(tmp_path, "greeter", PLUGIN_SRC)
        (plugin_dir / "plugin.yaml").write_text("version: '2.0.0'\n", encoding="utf-8")
        loader = _make_loader(config, tools, tmp_path)
        await loader.load_all()
        assert loader.loaded["greeter"].instance.manifest.version == "2.0.0"


class TestRestPlugins:
    def test_substitute(self) -> None:
        assert _substitute("{lat}", {"lat": 47.4}) == 47.4
        assert _substitute("point={lat},{lon}", {"lat": 1, "lon": 2}) == "point=1,2"
        assert _substitute({"q": "{term}"}, {"term": "x"}) == {"q": "x"}

    @respx.mock
    async def test_load_and_call(self, tmp_path) -> None:
        respx.get("https://api.example.com/v1/echo").mock(
            return_value=httpx.Response(200, json={"echo": "hello"})
        )
        descriptor = tmp_path / "echo.yaml"
        descriptor.write_text(
            textwrap.dedent(
                """
                name: example
                base_url: "https://api.example.com"
                tools:
                  - name: echo
                    description: "Echo endpoint"
                    method: GET
                    path: "/v1/echo"
                    query:
                      message: "{message}"
                    parameters:
                      type: object
                      properties:
                        message: {type: string}
                      required: [message]
                """
            ),
            encoding="utf-8",
        )
        tools = ToolRegistry()
        loader = RestPluginLoader(tools)
        count = await loader.load_file(descriptor)
        assert count == 1
        result = await tools.execute("example_echo", {"message": "hello"})
        assert "echo" in result
        await loader.aclose()


class TestMcpRendering:
    def test_render_text_blocks(self) -> None:
        result = _render_content(
            {"content": [{"type": "text", "text": "line1"}, {"type": "text", "text": "line2"}]}
        )
        assert result == "line1\nline2"

    def test_render_error(self) -> None:
        result = _render_content(
            {"isError": True, "content": [{"type": "text", "text": "bad input"}]}
        )
        assert result.startswith("Error:")

    def test_render_empty(self) -> None:
        assert _render_content({}) == "OK"
