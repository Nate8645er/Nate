---
name: graphify-setup
description: "Install and verify the graphify CLI so /graphify actually works in this environment. Use when graphify is not installed, when 'graphify: command not found' appears, when the user asks to set up graphify, or before the first /graphify run in a fresh session or container."
---

# graphify-setup

Makes the graphify CLI available and proves it works before the main `graphify` skill runs. The skill file alone is only the instruction layer — the CLI is the engine. Without this step, `/graphify` fails on any fresh machine.

## Step 1 — check whether it is already installed

```bash
graphify --version
```

If a version prints (e.g. `graphify 0.9.29`), skip to Step 3.

## Step 2 — install (try in this order)

```bash
pip install graphifyy          # works in most sandboxes and containers
```

Fallbacks if pip is unavailable or fails:

```bash
uv tool install graphifyy      # if uv exists
pipx install graphifyy         # if pipx exists
```

Notes:
- The PyPI package name is `graphifyy` (double y). The command it installs is `graphify`.
- Behind a corporate or agent proxy, pip already respects `HTTPS_PROXY`. Never disable TLS verification to force an install.
- No API key is needed for code graphs. `GEMINI_API_KEY` or `GOOGLE_API_KEY` are optional and only improve the semantic pass over docs, PDFs and images.

## Step 3 — self-test on a tiny folder

Run the deterministic code extraction (no LLM, nothing leaves the machine):

```bash
graphify update <small-code-folder>
```

Expected output: a line like `Rebuilt: N nodes, M edges, K communities` and a `graphify-out/` directory inside the target folder containing `graph.json`, `graph.html` and `GRAPH_REPORT.md`.

Verify the query side:

```bash
graphify explain "<any-node-id-from-graph.json>" --graph <folder>/graphify-out/graph.json
```

## Step 4 — hand over

Setup is done when both commands above succeed. For the full pipeline (docs, papers, images, GitHub URLs, merging, wiki, Neo4j export) continue with the main `graphify` skill — it orchestrates the semantic pass and the report.

## Troubleshooting

- `command not found` right after install: the scripts directory is not on PATH. Find it with `pip show -f graphifyy | grep -i location` and call the binary by absolute path, or add the directory to PATH.
- `unknown command 'build'`: there is no build subcommand. Code-only rebuilds use `graphify update <path>`; the full multi-format pipeline is driven by the AI assistant through the main `graphify` skill.
- Rebuild reports fewer nodes after a refactor that deleted files: rerun with `--force`.
