"""Plugin: aktuelle Zeit und Datum."""

from datetime import datetime

from jarvis.plugins.base import JarvisPlugin

_WOCHENTAGE = [
    "Montag", "Dienstag", "Mittwoch", "Donnerstag",
    "Freitag", "Samstag", "Sonntag",
]


class ZeitPlugin(JarvisPlugin):
    name = "zeit"
    description = "Aktuelle Uhrzeit und heutiges Datum"
    commands = {
        "zeit": "Aktuelle Uhrzeit anzeigen",
        "datum": "Heutiges Datum anzeigen",
    }

    def execute(self, command: str, args: str) -> str:
        now = datetime.now()
        if command == "zeit":
            return f"Es ist {now.strftime('%H:%M:%S')} Uhr."
        wochentag = _WOCHENTAGE[now.weekday()]
        return f"Heute ist {wochentag}, der {now.strftime('%d.%m.%Y')}."
