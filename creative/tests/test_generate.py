"""Tests der Creative-Pipeline — reine Funktionen, kein Browser, keine Credits."""
import pathlib

import generate as g

HERE = pathlib.Path(__file__).resolve().parent.parent


def test_esc_escapes_xml():
    assert g.esc('a & b <c> "d"') == "a &amp; b &lt;c&gt; &quot;d&quot;"


def test_card_svg_wellformed_and_contains_content():
    t = {"name": "Pro", "price_display": "CHF 49.00 / Monat", "audience": "KMU",
         "features": ["10 Agenten", "10 Mio. Tokens/Monat"]}
    svg = g.card_svg(t, "KI-Plattform", "inkl. MwSt", 1080, 1080)
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    assert "Pro" in svg
    assert "CHF 49.00 / Monat" in svg
    assert "10 Agenten" in svg
    assert "inkl. MwSt" in svg


def test_card_svg_escapes_injection():
    t = {"name": "<script>", "price_display": "&", "audience": "", "features": []}
    svg = g.card_svg(t, "B", "v", 1080, 1080)
    assert "<script>" not in svg
    assert "&lt;script&gt;" in svg


def test_all_formats_defined():
    assert set(g.FORMATS) == {"1x1", "4x5", "9x16"}
    assert g.FORMATS["9x16"] == (1080, 1920)


def test_build_all_writes_every_tariff_and_format(tmp_path):
    data = g.load_tariffs(HERE / "tariffs.json")
    written = g.build_all(data, tmp_path)
    assert len(written) == len(data["tariffs"]) * len(g.FORMATS)
    for p in written:
        assert p.exists() and p.read_text().startswith("<svg")
    assert (tmp_path / "index.html").exists()


def test_real_tariffs_has_five():
    data = g.load_tariffs(HERE / "tariffs.json")
    codes = {t["code"] for t in data["tariffs"]}
    assert codes == {"free", "starter", "pro", "business", "enterprise"}


# --- Hintergrundbilder (MuAPI) + deterministischer Text-Overlay ---

def test_no_backdrop_produces_plain_gradient():
    """Ohne Hintergrundbild bleibt alles wie bisher — die Pipeline
    funktioniert vollstaendig ohne bezahlte Bildgenerierung."""
    t = {"name": "Pro", "price_display": "CHF 49.00", "audience": "KMU", "features": []}
    svg = g.card_svg(t, "Marke", "inkl. MwSt", 1080, 1080)
    assert "<image" not in svg
    assert 'fill="url(#bg)"' in svg


def test_backdrop_is_embedded_with_scrim():
    """Mit Hintergrundbild: Bild eingebunden UND Abdunkelung darueber,
    damit der Text lesbar bleibt."""
    t = {"name": "Pro", "price_display": "CHF 49.00", "audience": "KMU", "features": []}
    svg = g.card_svg(t, "Marke", "inkl. MwSt", 1080, 1080,
                     backdrop_href="../backdrops/pro.png")
    assert '<image href="../backdrops/pro.png"' in svg
    assert 'fill="url(#scrim)"' in svg
    assert 'id="scrim"' in svg


def test_price_text_is_always_rendered_by_us_not_the_image():
    """Kernregel (Schweizer PBV): Preis und Pflichtangabe stehen IMMER als
    echter SVG-Text im Dokument — auch mit Hintergrundbild. Sie duerfen nie
    aus einem generativen Bildmodell stammen."""
    t = {"name": "Pro", "price_display": "CHF 49.00 / Monat", "audience": "KMU",
         "features": ["10 Agenten"]}
    for href in (None, "../backdrops/pro.png"):
        svg = g.card_svg(t, "Marke", "inkl. MwSt", 1080, 1350, backdrop_href=href)
        assert "CHF 49.00 / Monat" in svg
        assert "inkl. MwSt" in svg
        assert 'class="price"' in svg


def test_backdrop_prompts_forbid_text():
    """Jeder Bild-Prompt muss die Text-Verbotsklausel enthalten — sonst
    schreibt das Modell Pseudo-Text ins Bild, der mit dem echten Preis
    kollidiert."""
    import muapi_backdrop as mb
    assert "no text" in mb.NO_TEXT_CLAUSE.lower()
    assert "no letters" in mb.NO_TEXT_CLAUSE.lower()
    assert "no numbers" in mb.NO_TEXT_CLAUSE.lower()
    # Alle Tarife haben ein Motiv, und keines beschreibt Text/Zahlen.
    assert set(mb.BACKDROPS) == {"free", "starter", "pro", "business", "enterprise"}
    for code, prompt in mb.BACKDROPS.items():
        low = prompt.lower()
        for verboten in ("text", "logo", "price", "chf", "word"):
            assert verboten not in low, f"{code}: Prompt erwaehnt '{verboten}'"


def test_find_backdrop_returns_none_when_missing(tmp_path):
    assert g.find_backdrop("gibtsnicht", tmp_path) is None
