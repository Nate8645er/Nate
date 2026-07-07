FROM python:3.11-slim

WORKDIR /app

# Install the package first for layer caching.
COPY pyproject.toml README.md ./
COPY jarvis ./jarvis
RUN pip install --no-cache-dir .

COPY web ./web
COPY plugins ./plugins
COPY workflows ./workflows

ENV JARVIS_HOST=0.0.0.0 \
    JARVIS_PORT=8765 \
    JARVIS_DATA_DIR=/data \
    JARVIS_VOICE_ENABLED=true

VOLUME ["/data"]
EXPOSE 8765

CMD ["python", "-m", "jarvis"]
