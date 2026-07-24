# Gehaertetes Image fuer das Platform-Backend (Produkt A).
# Die CI (.github/workflows/platform-backend-release.yml) baut aus diesem
# Kontext und pusht nach GHCR mit provenance + sbom.
FROM python:3.12-slim AS base

# Sicherheits-Grundlagen: kein Cache, kein root zur Laufzeit.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Abhaengigkeiten zuerst (bessere Layer-Caches).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode + Migrationen + statisches UI.
COPY app ./app
COPY migrations ./migrations
COPY static ./static

# Nicht-root-Nutzer.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8080/health').status==200 else sys.exit(1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
