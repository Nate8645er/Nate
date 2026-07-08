"""Tests für die satzweise Zerlegung gestreamter Antworten."""

from jarvis.utils.sentences import SentenceStream, split_sentences


def stream_in_pieces(text: str, size: int = 3) -> list[str]:
    """Simuliert einen Token-Stream: Text in kleinen Häppchen einspeisen."""
    splitter = SentenceStream()
    sentences = []
    for i in range(0, len(text), size):
        sentences.extend(splitter.feed(text[i:i + size]))
    sentences.extend(splitter.flush())
    return sentences


def test_einfache_saetze():
    assert split_sentences("Hallo Nate. Wie geht es dir? Gut!") == [
        "Hallo Nate.", "Wie geht es dir?", "Gut!",
    ]


def test_streaming_liefert_gleiche_saetze_wie_ganzer_text():
    text = "Der Termin steht. Ich habe ihn eingetragen. Sonst noch etwas?"
    assert stream_in_pieces(text, size=1) == split_sentences(text)
    assert stream_in_pieces(text, size=7) == split_sentences(text)


def test_abkuerzungen_beenden_keinen_satz():
    text = "Nimm z.B. den Zug. Das ist bzw. wäre schneller."
    assert split_sentences(text) == [
        "Nimm z.B. den Zug.", "Das ist bzw. wäre schneller.",
    ]


def test_dr_und_initialen():
    text = "Frag Dr. Meier danach. Auch J. Schmidt weiß Bescheid."
    assert split_sentences(text) == [
        "Frag Dr. Meier danach.", "Auch J. Schmidt weiß Bescheid.",
    ]


def test_ordnungszahlen_bleiben_im_satz():
    text = "Wir treffen uns am 3. Oktober um 14 Uhr. Passt das?"
    assert split_sentences(text) == [
        "Wir treffen uns am 3. Oktober um 14 Uhr.", "Passt das?",
    ]


def test_dezimalzahlen_bleiben_im_satz():
    text = "Pi ist ungefähr 3.14 und mehr. Reicht das?"
    assert split_sentences(text) == [
        "Pi ist ungefähr 3.14 und mehr.", "Reicht das?",
    ]


def test_zeilenumbruch_trennt_listenpunkte():
    text = "Das brauchst du:\n- Eier und Mehl\n- Milch und Zucker\nFertig!"
    assert split_sentences(text) == [
        "Das brauchst du:", "- Eier und Mehl", "- Milch und Zucker", "Fertig!",
    ]


def test_anfuehrungszeichen_nach_satzzeichen():
    text = 'Er sagte "Bis morgen!" Und ging nach Hause.'
    assert split_sentences(text) == [
        'Er sagte "Bis morgen!"', "Und ging nach Hause.",
    ]


def test_rest_ohne_satzzeichen_kommt_beim_flush():
    splitter = SentenceStream()
    assert splitter.feed("Alles klar. Bis spä") == ["Alles klar."]
    assert splitter.flush() == ["Bis spä"]


def test_kein_vorschneller_schnitt_am_puffer_ende():
    # "z.B" könnte der Anfang von "z.B." sein - erst mehr Text abwarten.
    splitter = SentenceStream()
    assert splitter.feed("Nimm z.B") == []
    assert splitter.feed(". den Zug. Gut so?") == ["Nimm z.B. den Zug."]
    assert splitter.flush() == ["Gut so?"]


def test_leerer_text():
    assert split_sentences("") == []
    assert split_sentences("   \n  ") == []
