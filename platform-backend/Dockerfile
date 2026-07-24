# syntax=docker/dockerfile:1
# Multi-Stage-Build des platform-backend (Phase 9 · Containerisierung).
# Gehärtet passend zum k8s-securityContext (deploy/k8s/backend.yaml):
# non-root (uid 10001), readOnlyRootFilesystem-tauglich (schreibt nur nach /tmp),
# keine Build-Toolchain im finalen Image.

# ---------- Stage 1: Abhängigkeiten in ein venv bauen ----------
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
# Nur die Requirements zuerst kopieren → Layer-Cache bleibt gültig, solange sie
# sich nicht ändern.
COPY requirements.txt ./
# Optionaler CA-Mount: In Umgebungen mit TLS-inspizierendem Proxy kann eine
# CA-Bundle als BuildKit-Secret 'proxyca' eingereicht werden (required=false →
# in normaler CI ohne Proxy einfach weggelassen, dann baut pip direkt).
RUN --mount=type=secret,id=proxyca,required=false \
    sh -eu -c '\
      if [ -f /run/secrets/proxyca ]; then \
        export PIP_CERT=/run/secrets/proxyca REQUESTS_CA_BUNDLE=/run/secrets/proxyca; \
      fi; \
      python -m venv /opt/venv; \
      /opt/venv/bin/pip install --upgrade pip; \
      /opt/venv/bin/pip install -r requirements.txt'

# ---------- Stage 2: schlankes Laufzeit-Image ----------
FROM python:3.11-slim AS runtime

# Nicht-Root-Benutzer (uid muss zum runAsUser im Deployment passen: 10001).
RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLATFORM_ENV=production

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
# Nur den Anwendungscode (kein Test-/Deploy-Ballast — siehe .dockerignore).
COPY app ./app

USER 10001
EXPOSE 8000

# Container-natives Liveness-Signal (ergänzt die k8s-Probe).
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live').status==200 else 1)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
