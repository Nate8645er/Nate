"""Echte Sprachausgabe für JARVIS über ElevenLabs (optional).

JARVIS spricht standardmäßig mit der Browser-Stimme (Web Speech API, kostenlos).
Ist ein ELEVENLABS_API_KEY gesetzt, nutzt er stattdessen eine echte, hochwertige
Stimme (Stimm-ID konfigurierbar). Ohne Key oder bei einem Fehler fällt die
Weboberfläche automatisch auf die Browser-Stimme zurück — es wird nichts
erfunden und nichts blockiert.

Key von elevenlabs.io. Stimm-ID über JARVIS_VOICE_ID oder den Dashboard-Button.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

# Standard-Stimme (vom Nutzer vorgegeben); über JARVIS_VOICE_ID überschreibbar.
DEFAULT_VOICE_ID = "hx3VHMzUAVVvishlV9u9"
API_BASE = "https://api.elevenlabs.io/v1/text-to-speech/"
# Mehrsprachiges Modell — spricht Deutsch natürlich.
MODEL_ID = "eleven_multilingual_v2"


def available() -> bool:
    return bool(os.environ.get("ELEVENLABS_API_KEY"))


def voice_id() -> str:
    return os.environ.get("JARVIS_VOICE_ID", DEFAULT_VOICE_ID)


def synthesize(text: str, timeout: int = 30) -> bytes | None:
    """Text -> MP3-Audio (bytes). None, wenn kein Key oder ein Fehler auftritt."""
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key or not text.strip():
        return None
    payload = {
        "text": text[:2000],
        "model_id": MODEL_ID,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    req = urllib.request.Request(
        API_BASE + voice_id(),
        data=json.dumps(payload).encode(),
        headers={"xi-api-key": key, "content-type": "application/json",
                 "accept": "audio/mpeg"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError:
        return None       # Key/Stimme/Guthaben-Problem -> Browser-Stimme greift
    except Exception:
        return None       # Netzwerk o. ä. -> ehrlicher Fallback
