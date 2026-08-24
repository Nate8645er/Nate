"""Plugin system: Python plugins, hot reload, MCP servers, REST descriptors."""

from jarvis.plugins.api import Plugin, PluginContext, PluginManifest
from jarvis.plugins.loader import LoadedPlugin, PluginLoader
from jarvis.plugins.mcp import McpHttpClient, McpManager, McpStdioClient
from jarvis.plugins.rest import RestPluginLoader

__all__ = [
    "LoadedPlugin",
    "McpHttpClient",
    "McpManager",
    "McpStdioClient",
    "Plugin",
    "PluginContext",
    "PluginLoader",
    "PluginManifest",
    "RestPluginLoader",
]
