# JARVIS headless API server image.
# GUI/voice/vision need host hardware and run natively; this image serves the
# HTTP/WebSocket API, agents, memory, plugins and browser automation.

FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    JARVIS_DATA_DIR=/data \
    JARVIS_API__HOST=0.0.0.0

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# uv for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY plugins ./plugins

RUN uv pip install --system --no-cache ".[vector]"

# Non-root runtime user.
RUN useradd --create-home jarvis \
    && mkdir -p /data \
    && chown -R jarvis:jarvis /data /app
USER jarvis

VOLUME ["/data"]
EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
    CMD curl -fsS http://127.0.0.1:8765/health || exit 1

CMD ["jarvis", "serve", "--host", "0.0.0.0"]
