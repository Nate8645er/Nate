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
