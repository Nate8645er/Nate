"""Weather plugin using the free Open-Meteo API (no API key required)."""

from __future__ import annotations

from typing import Any

import httpx

from jarvis.plugins.api import Plugin, PluginContext, PluginManifest

_WMO_CODES: dict[int, str] = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "light snow",
    73: "moderate snow",
    75: "heavy snow",
    80: "rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "thunderstorm with heavy hail",
}


class WeatherPlugin(Plugin):
    manifest = PluginManifest(
        name="weather",
        version="1.0.0",
        description="Current weather and forecasts via Open-Meteo (keyless)",
        author="JARVIS",
        tags=["weather", "utility"],
    )

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def setup(self, context: PluginContext) -> None:
        self._client = httpx.AsyncClient(timeout=20.0)
        context.register_tool(
            "weather_current",
            "Get the current weather for a city (temperature, wind, condition).",
            self.current_weather,
            parameters={
                "type": "object",
                "properties": {"city": {"type": "string", "description": "City name"}},
                "required": ["city"],
            },
            tags={"weather", "utility"},
        )
        context.register_tool(
            "weather_forecast",
            "Get a daily forecast (max/min temperature, precipitation) for a city.",
            self.forecast,
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "days": {"type": "integer", "description": "1-7 days", "default": 3},
                },
                "required": ["city"],
            },
            tags={"weather", "utility"},
        )

    async def _geocode(self, city: str) -> tuple[float, float, str]:
        assert self._client is not None
        response = await self._client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "format": "json"},
        )
        response.raise_for_status()
        results = response.json().get("results") or []
        if not results:
            raise ValueError(f"Unknown city: {city}")
        top = results[0]
        label = ", ".join(filter(None, [top.get("name"), top.get("country")]))
        return top["latitude"], top["longitude"], label

    async def current_weather(self, city: str) -> str:
        assert self._client is not None
        lat, lon, label = await self._geocode(city)
        response = await self._client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current_weather": "true"},
        )
        response.raise_for_status()
        current: dict[str, Any] = response.json().get("current_weather", {})
        condition = _WMO_CODES.get(int(current.get("weathercode", -1)), "unknown conditions")
        return (
            f"{label}: {current.get('temperature')}°C, {condition}, "
            f"wind {current.get('windspeed')} km/h"
        )

    async def forecast(self, city: str, days: int = 3) -> str:
        assert self._client is not None
        days = max(1, min(int(days), 7))
        lat, lon, label = await self._geocode(city)
        response = await self._client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
                "forecast_days": days,
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        daily = response.json().get("daily", {})
        lines = [f"Forecast for {label}:"]
        for i, date in enumerate(daily.get("time", [])):
            condition = _WMO_CODES.get(int(daily["weathercode"][i]), "unknown")
            lines.append(
                f"{date}: {daily['temperature_2m_min'][i]}–{daily['temperature_2m_max'][i]}°C, "
                f"{condition}, precipitation {daily['precipitation_sum'][i]} mm"
            )
        return "\n".join(lines)

    async def teardown(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
