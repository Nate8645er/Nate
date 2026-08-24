# Configuration reference

Precedence (low → high): built-in defaults → `<data_dir>/config.yaml` (or
`--config path`) → environment variables / `.env`.

Environment variables use the prefix `JARVIS_` and `__` for nesting:
`JARVIS_LLM__MAX_TOKENS=8192`, `JARVIS_VOICE__WAKE_WORD=friday`.
API keys use their conventional names (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
`GOOGLE_API_KEY`, `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, `MISTRAL_API_KEY`).

The data directory defaults to `~/.jarvis` (`JARVIS_DATA_DIR` overrides) and
holds `config.yaml`, `memory.db`, vector data, `permissions.yaml`, logs,
downloads and local plugins.

## Sections

### Top level
| Key | Default | Meaning |
|---|---|---|
| `assistant_name` | `JARVIS` | Name used in prompts and GUI |
| `user_name` | `Sir` | How the assistant addresses you |
| `language` | `en` | Default answer language |
| `log_level` | `INFO` | Root log level |

### `llm`
| Key | Default | Meaning |
|---|---|---|
| `default_provider` | `null` | Pin a provider; `null` = auto-routing |
| `default_model` | `null` | Pin a model of that provider |
| `temperature` / `max_tokens` | `0.7` / `4096` | Generation defaults |
| `prefer_local` | `false` | Strong routing bonus for local models |
| `max_cost_tier` | `3` | 0 local/free … 3 premium |
| `providers.<name>.api_key/base_url/default_model/timeout_seconds/extra_headers/enabled` | — | Per-provider overrides |

Provider names: `anthropic`, `openai`, `gemini`, `ollama`, `lmstudio`,
`openrouter`, `deepseek`, `mistral`, `local`.

### `memory`
| Key | Default | Meaning |
|---|---|---|
| `short_term_max_messages/chars` | `60` / `60000` | Conversation window |
| `vector_backend` | `auto` | `auto` (Chroma if installed) / `chroma` / `local` |
| `embedding_provider/model` | `null` | e.g. `openai` + `text-embedding-3-small`; `null` = offline hashing embedder |
| `rag_chunk_size/overlap/top_k` | `900/150/6` | RAG parameters |

### `voice`
| Key | Default | Meaning |
|---|---|---|
| `enabled` | `false` | Activate the subsystem |
| `wake_word` / `wake_word_threshold` | `jarvis` / `0.5` | openWakeWord settings |
| `stt_model` / `stt_device` / `stt_language` | `large-v3` / `auto` / `null` | faster-whisper |
| `tts_backend` | `auto` | `piper` → `xtts` → `none` fallback chain |
| `tts_voice` / `tts_speaker_wav` / `tts_emotion` | `null/null/neutral` | Voice model, XTTS cloning clip, emotion preset |
| `allow_interruption` | `true` | Barge-in while speaking |
| `sample_rate` / `input_device` / `output_device` | `16000/null/null` | Audio I/O |

### `vision`
`enabled`, `camera_index`, `ocr_languages` (`eng+deu`), `face_detection`,
`object_detection_model` (`yolov8n.pt`).

### `desktop`
`enabled`, `failsafe` (pyautogui corner abort), `action_pause_seconds`,
`terminal_timeout_seconds`, `allowed_directories` (empty = home only).

### `browser`
`enabled`, `headless`, `browser` (`chromium|firefox|webkit`),
`executable_path`, `downloads_dir`, `default_timeout_ms`, `user_agent`.

### `api`
`host` (`127.0.0.1`), `port` (`8765`), `cors_origins`, `auth_token`.

### `gui`
`theme`, `accent_color` (`#28c8ff`), `secondary_color` (`#ffb02e`),
`transparency` (`0.92`), `always_on_top`, `fps` (`60`), `monitor_index`.

### `security`
`default_policy` (`ask`), `audit_log` (`true`), `sandbox_python` (`true`),
`confirm_capabilities` (list forced to `ask`), `policy_file`.

### `plugins`
`enabled`, `directories`, `hot_reload`, `mcp_servers` (mapping), `rest_plugins`
(list of YAML descriptor paths). Relative paths resolve inside the data dir.

## Integration environment variables

Integrations activate automatically when their variables are present — see
[.env.example](../.env.example) for the full list (e-mail SMTP/IMAP, Spotify,
Discord, Telegram, GitHub, Notion, Google Drive/Calendar, OneDrive, WhatsApp
Business).
