"""Produkt A — Backend-Einstiegspunkt (FastAPI).

Bindet die Routen zusammen und stellt Health-/Migrations-Endpunkte bereit.
Ein Modell, ein Mandant, ein Chat — lauffaehig (Phase-2-Ziel).
"""
from __future__ import annotations

import contextlib
import os
import pathlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import close_pool, get_pool, migrate
from .routes import admin, agents, chat, conversations, models, usage


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-Migration nur, wenn ausdruecklich gewuenscht (z.B. lokal/Compose).
    # In Produktion migriert man kontrolliert per `python -m app.migrate`.
    if os.environ.get("AUTO_MIGRATE", "").lower() in {"1", "true", "yes"}:
        migrate()
    try:
        yield
    finally:
        close_pool()


app = FastAPI(title="Platform Backend (Produkt A)", version="0.1.0", lifespan=lifespan)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(chat.router)
app.include_router(usage.router)
app.include_router(admin.router)
app.include_router(models.router)
app.include_router(conversations.router)
app.include_router(agents.router)


@app.get("/health")
async def health():
    """Liveness + DB-Erreichbarkeit."""
    db_ok = True
    try:
        with get_pool().connection() as conn:
            conn.execute("SELECT 1")
    except Exception:  # noqa: BLE001 — Health darf nie werfen
        db_ok = False
    return {"status": "ok", "db": db_ok}


# Statisches Chat-UI zuletzt mounten (die API-Routen oben haben Vorrang).
_static = pathlib.Path(__file__).resolve().parent.parent / "static"
if _static.is_dir():
    app.mount("/", StaticFiles(directory=str(_static), html=True), name="ui")
