"""Einrichtung: API-Schlüssel sicher eintragen und ElevenLabs-Stimme wählen.

Start:  python einrichten.py

Der Assistent fragt die Schlüssel für Claude (Anthropic), Deepgram und
ElevenLabs ab - die Eingabe bleibt unsichtbar wie bei einem Passwort -
prüft jeden Schlüssel direkt beim Anbieter und speichert alles in
config/secrets.json (steht in .gitignore, landet nie auf GitHub).

Ist ein ElevenLabs-Schlüssel da, listet der Assistent deine Stimmen auf
und trägt die gewählte Voice-ID in config/config.json ein. Danach hört
Jarvis mit Deepgram und spricht mit deiner ElevenLabs-Stimme - ganz ohne
Änderungen am Code.
"""

import json
from getpass import getpass
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).parent
SECRETS_PATH = PROJECT_ROOT / "config" / "secrets.json"
CONFIG_PATH = PROJECT_ROOT / "config" / "config.json"


def check_anthropic(key: str) -> bool:
    response = requests.get(
        "https://api.anthropic.com/v1/models",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
        timeout=15,
    )
    return response.status_code == 200


def check_deepgram(key: str) -> bool:
    response = requests.get(
        "https://api.deepgram.com/v1/projects",
        headers={"Authorization": f"Token {key}"},
        timeout=15,
    )
    return response.status_code == 200


def check_elevenlabs(key: str) -> bool:
    response = requests.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": key},
        timeout=15,
    )
    return response.status_code == 200


def fetch_elevenlabs_voices(key: str) -> list[dict]:
    """Holt die verfügbaren Stimmen (Name + Voice-ID) des Kontos."""
    response = requests.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": key},
        timeout=15,
    )
    response.raise_for_status()
    return [
        {"name": v.get("name", "?"), "id": v.get("voice_id", "")}
        for v in response.json().get("voices", [])
    ]


PROVIDERS = [
    ("anthropic_api_key", "Claude (Anthropic)", check_anthropic),
    ("deepgram_api_key", "Deepgram (Spracherkennung)", check_deepgram),
    ("elevenlabs_api_key", "ElevenLabs (Stimme)", check_elevenlabs),
]


def _load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _ask_key(label: str, already_there: bool) -> str | None:
    """Fragt einen Schlüssel ab. Leere Eingabe = überspringen/behalten."""
    hint = "Enter = vorhandenen behalten" if already_there else "Enter = überspringen"
    value = getpass(f"  {label} - Schlüssel eingeben ({hint}): ").strip()
    return value or None


def _choose_voice(key: str, current: str) -> str | None:
    """Listet die ElevenLabs-Stimmen auf und lässt eine auswählen."""
    try:
        voices = fetch_elevenlabs_voices(key)
    except requests.RequestException as e:
        print(f"  (Stimmen konnten nicht geladen werden: {e})")
        return None
    if not voices:
        print("  (Keine Stimmen im Konto gefunden - lege eine auf elevenlabs.io an.)")
        return None

    print("\n  Deine ElevenLabs-Stimmen:")
    for number, voice in enumerate(voices, start=1):
        marker = "  <- aktuell" if voice["id"] == current else ""
        print(f"    {number}. {voice['name']}  ({voice['id']}){marker}")
    choice = input(
        "  Nummer der gewünschten Stimme (Enter = nichts ändern): "
    ).strip()
    if not choice:
        return None
    if not choice.isdigit() or not 1 <= int(choice) <= len(voices):
        print("  (Keine gültige Nummer - Voice-ID bleibt unverändert.)")
        return None
    selected = voices[int(choice) - 1]
    print(f"  Gewählt: {selected['name']}")
    return selected["id"]


def main() -> None:
    print(__doc__.split("\n")[0])
    print("=" * 60)

    try:
        secrets = _load_json(SECRETS_PATH)
    except json.JSONDecodeError:
        print(f"FEHLER: {SECRETS_PATH} ist kein gültiges JSON - bitte prüfen.")
        return

    for name, label, check in PROVIDERS:
        already_there = bool(secrets.get(name))
        status = "vorhanden" if already_there else "fehlt"
        print(f"\n{label}  [{status}]")
        value = _ask_key(label, already_there)
        if value is None:
            continue
        print("  Prüfe den Schlüssel beim Anbieter ...", end=" ", flush=True)
        try:
            ok = check(value)
        except requests.RequestException as e:
            print(f"nicht erreichbar ({e}).")
            ok = False
        else:
            print("gültig!" if ok else "ABGELEHNT.")
        if not ok:
            keep = input("  Trotzdem speichern? (j/n): ").strip().lower()
            if keep not in {"j", "ja", "y", "yes"}:
                print("  Nicht gespeichert.")
                continue
        secrets[name] = value

    _save_json(SECRETS_PATH, secrets)
    print(f"\nGespeichert: {SECRETS_PATH}  (steht in .gitignore)")

    # Stimme auswählen, sobald ein ElevenLabs-Schlüssel da ist
    if secrets.get("elevenlabs_api_key"):
        config = _load_json(CONFIG_PATH)
        speech = config.setdefault("speech", {})
        voice_id = _choose_voice(
            secrets["elevenlabs_api_key"], speech.get("elevenlabs_voice_id", "")
        )
        if voice_id:
            speech["elevenlabs_voice_id"] = voice_id
            _save_json(CONFIG_PATH, config)
            print(f"  Voice-ID eingetragen in {CONFIG_PATH}.")

    print("\nFertig! Starte Jarvis mit:  python main.py   (dann /sprechen)")
    print("Oder im Browser testen:     python jarvis_web.py")


if __name__ == "__main__":
    main()
