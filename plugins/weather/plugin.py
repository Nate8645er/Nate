"""Weather plugin — reference implementation for the JARVIS plugin API.

A plugin exposes `setup(kernel)` (and optionally `teardown(kernel)`).
Skills can be registered directly on the kernel's skill registry; they are
automatically tagged with the plugin id and removed again when the plugin
is disabled or unloaded.
"""

from __future__ import annotations

from typing import Any

import httpx

from jarvis.core.approvals import Risk
from jarvis.skills.base import Skill

_WEATHER_CODES = {
    0: "klar", 1: "überwiegend klar", 2: "teils bewölkt", 3: "bedeckt",
    45: "Nebel", 51: "Nieselregen", 61: "Regen", 71: "Schnee",
    80: "Regenschauer", 95: "Gewitter",
}


async def get_weather(city: str) -> dict[str, Any]:
    """Current weather for a city via Open-Meteo geocoding + forecast."""
    async with httpx.AsyncClient(timeout=15) as client:
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "de"},
        )
        geo.raise_for_status()
        results = geo.json().get("results") or []
        if not results:
            return {"error": f"Ort nicht gefunden: {city}"}
        place = results[0]
        forecast = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,weather_code,wind_speed_10m",
            },
        )
        forecast.raise_for_status()
        current = forecast.json()["current"]
    return {
        "ort": place["name"],
        "temperatur_c": current["temperature_2m"],
        "wind_kmh": current["wind_speed_10m"],
        "zustand": _WEATHER_CODES.get(current["weather_code"], "unbekannt"),
    }


def setup(kernel) -> None:  # noqa: ANN001 - kernel type lives in the host app
    kernel.skills.register(
        Skill(
            name="get_weather",
            description="Aktuelles Wetter für eine Stadt (Open-Meteo).",
            category="web",
            risk=Risk.READ,
            func=get_weather,
            parameters={"city": {"type": "string"}},
        )
    )


def teardown(kernel) -> None:  # noqa: ANN001
    # Skills are removed automatically via unregister_source("weather").
    pass
