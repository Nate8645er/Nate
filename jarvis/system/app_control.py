"""Programme auf dem PC öffnen und schließen.

Die bekannten Programme stehen in config/apps.json (Name -> Programm/URL).
Neue Programme: einfach dort eine Zeile ergänzen. Zusätzlich kann /oeffne
auch direkte Pfade, .exe-Namen und Webadressen öffnen.
"""

import json
import logging
import os
import platform
import shutil
import subprocess
import webbrowser
from pathlib import Path

logger = logging.getLogger("jarvis.system")

IS_WINDOWS = platform.system() == "Windows"


class AppController:
    """Öffnet und schließt Programme anhand der Registry in apps.json."""

    def __init__(self, apps_file: Path):
        self.apps_file = apps_file
        self.apps: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.apps_file.exists():
            logger.warning("Keine App-Liste gefunden (%s).", self.apps_file)
            return
        try:
            self.apps = json.loads(self.apps_file.read_text(encoding="utf-8"))
            logger.info("%d Programme in der App-Liste.", len(self.apps))
        except (OSError, json.JSONDecodeError) as e:
            logger.error("App-Liste konnte nicht geladen werden: %s", e)

    # ------------------------------------------------------------------
    # Öffnen
    # ------------------------------------------------------------------

    def open(self, target: str) -> str:
        """Öffnet ein Programm, einen Pfad oder eine Webadresse."""
        target = target.strip()
        if not target:
            return "Nutzung: /oeffne <programm> - /apps zeigt alle bekannten Programme."

        # Bekannter Name aus apps.json?
        resolved = self.apps.get(target.lower(), target)

        # Webadresse -> Standardbrowser
        if resolved.startswith(("http://", "https://")):
            webbrowser.open(resolved)
            logger.info("Webadresse geöffnet: %s", resolved)
            return f"Öffne {resolved} im Browser."

        if IS_WINDOWS:
            return self._open_windows(target, resolved)
        return self._open_other(target, resolved)

    def _open_windows(self, name: str, resolved: str) -> str:
        try:
            # os.startfile kann .exe, Dateien, Ordner und ms-settings: öffnen
            os.startfile(resolved)  # noqa: S606 - bewusste Nutzerfunktion
            logger.info("Programm gestartet: %s", resolved)
            return f"Öffne {name}."
        except FileNotFoundError:
            pass
        except OSError as e:
            logger.error("Start von '%s' fehlgeschlagen: %s", resolved, e)
            return f"'{name}' konnte nicht gestartet werden: {e}"

        # Zweiter Versuch: über PATH suchen (z.B. "code" für VS Code)
        path = shutil.which(resolved)
        if path:
            subprocess.Popen([path])
            logger.info("Programm über PATH gestartet: %s", path)
            return f"Öffne {name}."

        known = ", ".join(sorted(self.apps)) or "keine"
        return (f"'{name}' wurde nicht gefunden. Bekannte Programme: {known}. "
                f"Du kannst auch einen kompletten Pfad angeben.")

    def _open_other(self, name: str, resolved: str) -> str:
        """Nicht-Windows (z.B. Test-Umgebung): über PATH starten."""
        path = shutil.which(resolved)
        if path:
            subprocess.Popen([path])
            logger.info("Programm gestartet: %s", path)
            return f"Öffne {name}."
        return (f"'{name}' ist hier nicht verfügbar "
                f"(dieses Modul zielt auf Windows 11).")

    # ------------------------------------------------------------------
    # Schließen
    # ------------------------------------------------------------------

    def close(self, name: str) -> str:
        """Beendet ein Programm über seinen Prozessnamen (nur Windows)."""
        name = name.strip()
        if not name:
            return "Nutzung: /schliesse <programm> - z.B. /schliesse rechner"

        resolved = self.apps.get(name.lower(), name)
        if resolved.startswith(("http://", "https://", "ms-settings:")):
            return f"'{name}' ist keine App, die ich schließen kann."

        image = Path(resolved).name
        if not image.lower().endswith(".exe"):
            image += ".exe"

        if not IS_WINDOWS:
            return "Programme schließen funktioniert nur unter Windows."

        result = subprocess.run(
            ["taskkill", "/IM", image, "/F"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            logger.info("Programm beendet: %s", image)
            return f"{name} wurde geschlossen."
        logger.warning("taskkill für %s: %s", image, result.stderr.strip())
        return f"'{name}' läuft gerade nicht (oder heißt anders als '{image}')."

    # ------------------------------------------------------------------

    def overview(self) -> str:
        """Liste aller bekannten Programme für /apps."""
        if not self.apps:
            return f"Keine Programme registriert (Datei: {self.apps_file})."
        lines = [f"• {name}  →  {target}" for name, target in sorted(self.apps.items())]
        lines.append("\nNeue Programme kannst du in config/apps.json ergänzen.")
        return "\n".join(lines)
