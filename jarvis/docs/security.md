# Security model

## Capabilities & policies

Side-effecting tools declare a *capability* string:

| Capability | Guards |
|---|---|
| `files.write` / `files.delete` | writing / deleting files (delete goes to a trash folder) |
| `desktop.input` | mouse & keyboard control, window focus |
| `desktop.apps` | launching / terminating programs |
| `desktop.terminal` | shell command execution |
| `code.execute` | sandboxed Python execution |
| `browser.forms` / `browser.download` | form submission / downloads |
| `integrations.send` | anything outbound: e-mail, chat messages, issue creation, uploads |
| `vision.webcam` | camera access |
| `voice.listen` | on-demand microphone recording |
| `mcp.<server>` | all tools of one MCP server |

Per capability the policy is `allow`, `ask` or `deny`:

* **ask** routes through the registered *confirmer* — a GUI dialog, the
  terminal prompt in `jarvis chat`, or (headless, no confirmer attached)
  an automatic **deny**. Fail-closed by default.
* Prefix wildcards work: `desktop.*`, `*`.
* Decisions persist in `<data_dir>/permissions.yaml` and are editable live via
  `PUT /permissions`.
* `security.default_policy` (default `ask`) covers unlisted capabilities.

## Audit log

Every permission decision is appended to `<data_dir>/logs/audit.jsonl`:

```json
{"ts": "...", "capability": "desktop.terminal", "description": "terminal_run({\"command\": \"ls\"})", "outcome": "allowed"}
```

## Sandboxing

`run_python` executes snippets in a fresh interpreter: isolated mode (`-I`),
empty environment, throw-away working directory, hard timeout, truncated
output. This is process-level isolation — for hostile-code containment use the
Docker deployment, where the whole assistant runs as a non-root user in a
container.

## Secrets

* API keys come from the environment / `.env` (git-ignored); they are held as
  pydantic `SecretStr` and never logged.
* `integrations_status` reports *which* integrations are configured, never
  their values.
* The HTTP API supports bearer-token auth (`api.auth_token`) and binds to
  `127.0.0.1` by default; CORS origins are an explicit allowlist.

## File-system sandbox

Desktop file tools resolve every path and require it to be inside
`desktop.allowed_directories` (default: the user's home). Deletions are moves
into `<data_dir>/.jarvis-trash`, so they are reversible.
