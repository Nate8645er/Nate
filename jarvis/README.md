# JARVIS — Personal AI Assistant

A production-grade, open-source personal AI assistant inspired by Tony Stark's JARVIS:
multi-provider LLM brain with automatic model selection, a multi-agent system, voice
(wake word → Whisper → neural TTS, interruptible), vision (screen, webcam, OCR,
detection), desktop and browser automation, long-term memory with RAG, a hot-reloadable
plugin system with MCP support — and an animated Iron-Man-style HUD built in PySide6.

```
     ╭──────────────╮      ╭──────────────────────────────╮
     │  HUD (Qt)    │◄────►│                              │
     ├──────────────┤      │        JarvisApp             │
     │  Voice loop  │◄────►│  Router ── 9 LLM providers   │
     ├──────────────┤      │  Orchestrator ── 9 agents    │
     │  HTTP/WS API │◄────►│  Memory (STM/LTM/Vector/RAG) │
     ╰──────────────╯      │  Tools + Permissions         │
                           │  Plugins / MCP / REST        │
                           ╰──────────────────────────────╯
```

## Features

| Area | What you get |
|---|---|
| **LLM** | Claude, OpenAI, Gemini, Ollama, LM Studio, OpenRouter, DeepSeek, Mistral, any OpenAI-compatible local server. Streaming, tool calling, vision input. Automatic best-model routing by capability, quality, cost and locality. |
| **Agents** | Planner, Research, Vision, Coding, Desktop, Browser, Automation, Voice, Memory. Plan → execute → synthesise orchestration on a typed state graph (LangGraph-compatible export). |
| **Voice** | "Jarvis" wake word (openWakeWord), faster-whisper (large-v3) STT, Piper/XTTS-v2/Coqui TTS with emotion presets, sentence-streamed speech, barge-in interruption. |
| **Vision** | Screen capture, webcam, OCR (Tesseract), face detection, object detection (YOLO with HOG fallback), window listing, LLM image analysis. |
| **Desktop** | App launch/close, mouse & keyboard control, sandboxed file management with trash-delete, PDF/Excel/Word/PowerPoint read & write, async terminal, Windows API helpers. |
| **Browser** | Playwright automation (navigate, read, click, forms, downloads, screenshots), keyless web search, HTTP scraping with clean text extraction. |
| **Integrations** | E-mail (SMTP/IMAP), calendar (local ICS + Google), Spotify, Discord, Telegram, WhatsApp Business, GitHub, Notion, Google Drive, OneDrive. Tools appear only when configured. |
| **Memory** | Short-term window, SQLite long-term store with FTS5, vector database (ChromaDB or built-in offline store), RAG with citations, user profile, tasks & reminders. |
| **Plugins** | Python plugins with hot reload, declarative REST plugins (YAML → tools), MCP client (stdio + HTTP) that turns any MCP server into agent tools. |
| **Security** | Capability-based permissions (allow/ask/deny), interactive confirmations, persistent policies, JSONL audit log, sandboxed Python execution, optional API bearer auth. |
| **GUI** | Frameless translucent HUD: animated arc reactor, holographic rings, circular voice visualizer, particle field, live status readouts, streaming chat. |

## Quick start

```bash
git clone https://github.com/Nate8645er/Nate.git
cd Nate/jarvis

# guided install (detects GPU/CUDA, uses uv when available)
python scripts/install.py            # default: core + GUI + vector memory
python scripts/install.py --all      # everything (voice, vision, desktop, browser)
python scripts/install.py --check    # environment report only

cp .env.example .env                 # add an API key — or just run Ollama locally

jarvis status    # providers, agents, tools
jarvis chat      # terminal chat (streaming)
jarvis gui       # the HUD
jarvis voice     # always-on voice assistant
jarvis serve     # HTTP/WebSocket API on :8765
```

No API key? Install [Ollama](https://ollama.com), `ollama pull llama3.2`, done — JARVIS
auto-detects it. With `uv`: `uv pip install -e ".[all]"`.

### Docker

```bash
docker compose -f docker/docker-compose.yml up -d   # API + bundled Ollama
curl localhost:8765/health
```

## Configuration

Three layers, later wins: defaults → `~/.jarvis/config.yaml` → environment (`.env`).
See [`config.example.yaml`](config.example.yaml) and
[docs/configuration.md](docs/configuration.md). Examples:

```bash
JARVIS_LLM__DEFAULT_PROVIDER=ollama     # pin a provider
JARVIS_LLM__PREFER_LOCAL=true           # favour local models in auto-routing
JARVIS_VOICE__ENABLED=true
JARVIS_API__AUTH_TOKEN=change-me
```

## Extending JARVIS

Everything is open for extension without touching the core:

* **Plugin** — drop a folder with `plugin.py` into the plugins directory; it hot-reloads.
  Register tools, agents, event handlers, even FastAPI routes. [docs/plugins.md](docs/plugins.md)
* **MCP server** — add it to `plugins.mcp_servers` in the config; its tools appear automatically.
* **REST API** — describe endpoints in YAML (`plugins.rest_plugins`); each becomes a tool.
* **LLM provider** — subclass `LLMProvider` (or `OpenAICompatProvider`) and call
  `register_provider()`. [docs/architecture.md](docs/architecture.md)
* **Agent** — subclass `BaseAgent` with a persona and tool tags; register it with the
  orchestrator. [docs/agents.md](docs/agents.md)

## Documentation

* [Architecture](docs/architecture.md) — layers, data flow, design decisions
* [Agents & orchestration](docs/agents.md)
* [Plugin development](docs/plugins.md)
* [HTTP/WebSocket API](docs/api.md)
* [Configuration reference](docs/configuration.md)
* [Voice pipeline](docs/voice.md)
* [Security model](docs/security.md)

## Development

```bash
uv pip install -e ".[dev]"
ruff check src tests        # lint
mypy src/jarvis             # types
pytest -q                   # tests (no network, no hardware needed)
```

CI (GitHub Actions) runs lint, mypy, the test matrix (3.11–3.13) and a Docker build.

## Honest limitations

* Cloud providers need your own API keys; local quality depends on your hardware.
* Voice/vision/desktop features need real hardware and their optional extras installed —
  every subsystem degrades gracefully when missing.
* WhatsApp uses the official Business Cloud API (personal WhatsApp Web automation is
  deliberately not included).
* The Python sandbox is process-level isolation; for hard containment run the Docker image.

## License

MIT
