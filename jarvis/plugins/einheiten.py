"""Plugin: Einheiten umrechnen - offline, für die gängigsten Fälle."""

from jarvis.plugins.base import JarvisPlugin

#: (von, nach) -> Funktion; Namen kleingeschrieben und ohne Umlaute
_UMRECHNUNGEN = {
    ("km", "meilen"): lambda v: (v * 0.621371, "Meilen"),
    ("meilen", "km"): lambda v: (v * 1.609344, "km"),
    ("m", "fuss"): lambda v: (v * 3.28084, "Fuß"),
    ("fuss", "m"): lambda v: (v / 3.28084, "m"),
    ("cm", "zoll"): lambda v: (v / 2.54, "Zoll"),
    ("zoll", "cm"): lambda v: (v * 2.54, "cm"),
    ("kg", "pfund"): lambda v: (v * 2.204623, "Pfund"),
    ("pfund", "kg"): lambda v: (v / 2.204623, "kg"),
    ("l", "gallonen"): lambda v: (v * 0.264172, "Gallonen"),
    ("gallonen", "l"): lambda v: (v / 0.264172, "l"),
    ("celsius", "fahrenheit"): lambda v: (v * 9 / 5 + 32, "°F"),
    ("fahrenheit", "celsius"): lambda v: ((v - 32) * 5 / 9, "°C"),
}

_ALIAS = {
    "kilometer": "km", "meile": "meilen", "mi": "meilen",
    "meter": "m", "fuß": "fuss", "ft": "fuss",
    "zentimeter": "cm", "inch": "zoll", "in": "zoll",
    "kilogramm": "kg", "kilo": "kg", "lbs": "pfund", "lb": "pfund",
    "liter": "l", "gallone": "gallonen", "gal": "gallonen",
    "c": "celsius", "°c": "celsius", "grad": "celsius",
    "f": "fahrenheit", "°f": "fahrenheit",
}


def _normalisiere(einheit: str) -> str:
    einheit = einheit.strip().lower().rstrip(".")
    return _ALIAS.get(einheit, einheit)


class EinheitenPlugin(JarvisPlugin):
    name = "einheiten"
    description = "Einheiten umrechnen (km/Meilen, kg/Pfund, °C/°F, ...)"
    commands = {
        "umrechnen": "z.B. /umrechnen 5 km in meilen",
    }

    def execute(self, command: str, args: str) -> str:
        teile = args.replace(",", ".").split()
        # erwartet: <zahl> <einheit> in <einheit>
        if len(teile) >= 4 and teile[-2].lower() in {"in", "nach", "zu"}:
            zahl_text, von, nach = teile[0], " ".join(teile[1:-2]), teile[-1]
        else:
            return ("Nutzung: /umrechnen <zahl> <einheit> in <einheit>\n"
                    "z.B. /umrechnen 5 km in meilen  |  /umrechnen 30 celsius in fahrenheit\n"
                    "Kann: km/meilen, m/fuss, cm/zoll, kg/pfund, l/gallonen, celsius/fahrenheit")
        try:
            wert = float(zahl_text)
        except ValueError:
            return f"'{zahl_text}' ist keine Zahl."
        paar = (_normalisiere(von), _normalisiere(nach))
        rechnung = _UMRECHNUNGEN.get(paar)
        if rechnung is None:
            return (f"Die Umrechnung {paar[0]} → {paar[1]} kenne ich nicht.\n"
                    "Kann: km/meilen, m/fuss, cm/zoll, kg/pfund, l/gallonen, "
                    "celsius/fahrenheit")
        ergebnis, einheit = rechnung(wert)
        return f"{args.strip()} = {ergebnis:,.2f} {einheit}".replace(",", "'")
