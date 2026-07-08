"""Plugin: Zufall - Würfel, Münzwurf und Entscheidungshilfe."""

import random

from jarvis.plugins.base import JarvisPlugin


class ZufallPlugin(JarvisPlugin):
    name = "zufall"
    description = "Würfeln, Münze werfen, zwischen Optionen entscheiden"
    commands = {
        "wuerfel": "Würfeln, z.B. /wuerfel oder /wuerfel 20 (für W20)",
        "muenze": "Münzwurf: Kopf oder Zahl",
        "entscheide": "Zufällig wählen: /entscheide Pizza, Pasta, Salat",
    }

    def execute(self, command: str, args: str) -> str:
        if command == "wuerfel":
            seiten = 6
            if args.strip():
                if not args.strip().isdigit() or int(args) < 2:
                    return "Nutzung: /wuerfel oder /wuerfel <seiten> (mindestens 2)"
                seiten = int(args)
            wurf = random.randint(1, seiten)
            return f"🎲 Der W{seiten} zeigt: {wurf}"

        if command == "muenze":
            return f"🪙 {random.choice(['Kopf', 'Zahl'])}!"

        # /entscheide
        optionen = [o.strip() for o in args.split(",") if o.strip()]
        if len(optionen) < 2:
            return ("Nutzung: /entscheide <option1>, <option2>, ... - "
                    "z.B. /entscheide Pizza, Pasta, Salat")
        return f"Ich habe entschieden: {random.choice(optionen)}"
