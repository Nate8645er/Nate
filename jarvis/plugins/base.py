"""Basisklasse für alle Jarvis-Plugins.

Ein Plugin stellt einen oder mehrere Chat-Befehle bereit (z.B. /zeit).
Neue Plugins: einfach eine .py-Datei in jarvis/plugins/ ablegen, die eine
Unterklasse von JarvisPlugin enthält - sie wird automatisch geladen.
"""


class JarvisPlugin:
    """Basisklasse. Unterklassen setzen name, description und commands."""

    #: Eindeutiger Plugin-Name
    name: str = ""
    #: Kurzbeschreibung für /plugins
    description: str = ""
    #: Befehle des Plugins: {"befehl": "Beschreibung"} (ohne führenden /)
    commands: dict = {}

    def execute(self, command: str, args: str) -> str:
        """Führt einen Befehl aus und gibt die Antwort als Text zurück.

        Args:
            command: Der Befehl ohne führenden Slash (z.B. "zeit").
            args: Alles, was der Nutzer hinter dem Befehl eingegeben hat.
        """
        raise NotImplementedError
