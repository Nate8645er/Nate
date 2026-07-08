"""Zerlegt gestreamten Text schrittweise in sprechfertige Sätze.

Der SentenceStream bekommt die Antwort des Modells stückweise (feed) und
gibt jeden Satz zurück, sobald er vollständig ist - damit die Sprachausgabe
mit dem ersten Satz beginnen kann, während das Modell noch am zweiten
schreibt. flush() liefert am Ende den Rest, der kein Satzzeichen mehr hat.

Deutsche Stolperfallen sind berücksichtigt: Abkürzungen wie "z.B." oder
"Dr." und Ordnungszahlen wie "am 3. Oktober" beenden keinen Satz.
"""

# Abkürzungen (kleingeschrieben, ohne den letzten Punkt), nach denen der
# Satz weitergeht. Neue Fälle einfach ergänzen - eine Zeile pro Fundstück.
ABBREVIATIONS = {
    "z.b", "d.h", "u.a", "u.u", "o.ä", "usw", "etc", "bzw", "ca", "vgl",
    "ggf", "evtl", "inkl", "exkl", "mind", "max", "min", "sog", "bspw",
    "dr", "prof", "nr", "abs", "art", "st", "str", "tel",
}

#: Anführungszeichen, die direkt nach dem Satzzeichen noch zum Satz gehören
_CLOSING_QUOTES = "\"'”“»«)]"


class SentenceStream:
    """Sammelt Text-Häppchen und gibt fertige Sätze heraus."""

    def __init__(self, min_chars: int = 4):
        # Sehr kurze Bruchstücke (z.B. ein übersehenes "1.") werden nicht
        # einzeln gesprochen, sondern mit dem nächsten Satz zusammengelegt.
        self.min_chars = min_chars
        self._buffer = ""

    def feed(self, delta: str) -> list[str]:
        """Nimmt ein Text-Stück auf und gibt alle fertigen Sätze zurück."""
        self._buffer += delta
        sentences = []
        while True:
            cut = self._find_cut()
            if cut is None:
                break
            sentence = self._buffer[:cut].strip()
            self._buffer = self._buffer[cut:].lstrip()
            if sentence:
                sentences.append(sentence)
        return sentences

    def flush(self) -> list[str]:
        """Gibt den restlichen Text zurück (Antwort ist zu Ende)."""
        rest = self._buffer.strip()
        self._buffer = ""
        return [rest] if rest else []

    def _find_cut(self) -> int | None:
        """Sucht die erste sichere Satzgrenze im Puffer."""
        buf = self._buffer
        for i, char in enumerate(buf):
            if char == "\n":
                # Zeilenumbrüche (Listen, Absätze) beenden den Abschnitt.
                if len(buf[:i].strip()) >= self.min_chars:
                    return i + 1
                continue
            if char not in ".!?":
                continue
            # Erst entscheiden, wenn das nächste Zeichen da ist - sonst
            # würde "z.B." mitten im Stream fälschlich zerschnitten.
            j = i + 1
            while j < len(buf) and buf[j] in _CLOSING_QUOTES:
                j += 1
            if j >= len(buf):
                return None  # auf mehr Text warten (flush erledigt den Rest)
            if not buf[j].isspace():
                continue  # z.B. "3.14" oder "z.B." - kein Satzende
            if char == "." and self._is_abbreviation_or_ordinal(buf, i):
                continue
            if len(buf[:j].strip()) < self.min_chars:
                continue
            return j
        return None

    @staticmethod
    def _is_abbreviation_or_ordinal(buf: str, dot_index: int) -> bool:
        """Prüft das Wort vor dem Punkt: Abkürzung oder Zahl (Ordnungszahl)?"""
        start = dot_index
        while start > 0 and not buf[start - 1].isspace():
            start -= 1
        word = buf[start:dot_index].lower().lstrip("(\"'„“»«")
        if not word:
            return False
        if word.isdigit():
            return True  # "am 3. Oktober"
        if len(word) == 1 and word.isalpha():
            return True  # Initialen wie "J."
        return word in ABBREVIATIONS


def split_sentences(text: str, min_chars: int = 4) -> list[str]:
    """Zerlegt einen fertigen Text in Sätze (gleiche Regeln wie der Stream)."""
    stream = SentenceStream(min_chars=min_chars)
    return stream.feed(text) + stream.flush()
