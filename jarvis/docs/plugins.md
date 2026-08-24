# Plugin development

JARVIS supports three plugin flavours. All of them end up as tools in the same
registry, usable by every agent and visible in `GET /tools`.

## 1. Python plugins (full power, hot reload)

A plugin is a directory inside a configured plugin folder
(`plugins.directories`, default `<data_dir>/plugins`; the repo ships examples
in `jarvis/plugins/`):

```
plugins/
  my_plugin/
    plugin.py        # required
    plugin.yaml      # optional manifest override
```

Minimal plugin:

```python
from jarvis.plugins.api import Plugin, PluginContext, PluginManifest

class MyPlugin(Plugin):
    manifest = PluginManifest(
        name="my_plugin", version="1.0.0",
        description="Says hello", author="you",
    )

    async def setup(self, context: PluginContext) -> None:
        context.register_tool(
            "hello",
            "Greet someone by name.",
            lambda name: f"Hello {name}!",
            parameters={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        )

    async def teardown(self) -> None:
        ...  # release sockets, files, tasks
```

`PluginContext` gives you, all tracked and cleaned up on unload/reload:

| Method | Effect |
|---|---|
| `register_tool(name, desc, handler, parameters=, tags=, capability=)` | Add an agent tool. Handlers may be sync (run in a worker thread) or async. Set `capability="integrations.send"`-style strings to route through the permission system. |
| `register_agent(agent)` | Add a `BaseAgent` to the orchestrator roster. |
| `subscribe(pattern, handler)` | Listen on the event bus (`"voice.*"`, `"*"`). |
| `register_api_router(router)` | Mount a FastAPI `APIRouter` under `/plugins/<name>`. |
| `context.config / events / router / memory / orchestrator` | Direct access to core services. |

**Hot reload** is on by default (`plugins.hot_reload`): saving any file in a
plugin directory reloads that plugin in place — tools are atomically replaced.
Reload manually with `POST /plugins/{name}/reload`.

## 2. REST plugins (declarative, zero code)

Describe an HTTP API in YAML and every endpoint becomes a tool. Register the
file in `plugins.rest_plugins`.

```yaml
name: openmeteo
base_url: "https://api.open-meteo.com"
tools:
  - name: current_weather
    description: "Current weather for coordinates"
    method: GET
    path: "/v1/forecast"
    query:
      latitude: "{latitude}"
      longitude: "{longitude}"
      current_weather: "true"
    parameters:
      type: object
      properties:
        latitude:  {type: number}
        longitude: {type: number}
      required: [latitude, longitude]
```

`{placeholders}` in `path`, `query`, `headers` and `body` are substituted from
tool arguments (full-string placeholders keep their native JSON type). Add
`capability:` per tool to gate it behind permissions.

## 3. MCP servers (Model Context Protocol)

Any MCP server becomes a set of tools named `mcp_<server>_<tool>`:

```yaml
plugins:
  mcp_servers:
    filesystem:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/me/docs"]
    remote:
      url: "https://example.com/mcp"
      headers: {Authorization: "Bearer ..."}
```

stdio servers are spawned as child processes (JSON-RPC 2.0 over newline-
delimited stdio); HTTP servers use the streamable-HTTP transport. MCP tools
carry the capability `mcp.<server>`, so you can set a policy per server.

## Bundled examples

| Plugin | Tools | Notes |
|---|---|---|
| `weather` | `weather_current`, `weather_forecast` | Open-Meteo, no API key |
| `system_info` | `system_overview`, `system_disk_usage` | psutil optional |
| `timer` | `timer_set`, `timer_list`, `timer_cancel` | announces via `timer.finished` event |

Copy them into your plugins directory (or point `plugins.directories` at the
repo folder) to activate.

## Testing plugins

```python
async def test_my_plugin(tmp_path):
    tools = ToolRegistry()
    loader = PluginLoader(
        lambda name: PluginContext(config=cfg, tools=tools, events=EventBus(),
                                   router=None, _plugin_name=name),
        [tmp_path],
    )
    await loader.load_all()
    assert await tools.execute("hello", {"name": "Nate"}) == "Hello Nate!"
```
