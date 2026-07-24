/**
 * Unit-Tests für die Blitz-Werkzeuge (lib/blitz.ts) – reine, deterministische
 * Funktionen (IBAN, Rechnung, Marge, Stundensatz, Slug, Passwort, Escaping).
 */
import { describe, expect, it } from "vitest";
import {
  ibanPruefen,
  passwortErzeugen,
  rechnungSumme,
  rechnungHtml,
  chf,
  marge,
  stundensatz,
  signaturHtml,
  slug,
} from "../lib/blitz";

describe("ibanPruefen", () => {
  it("erkennt eine gültige Schweizer IBAN (mit Leerzeichen) und formatiert sie", () => {
    const r = ibanPruefen("CH93 0076 2011 6238 5295 7");
    expect(r.valid).toBe(true);
    expect(r.land).toBe("CH");
    expect(r.formatiert).toBe("CH93 0076 2011 6238 5295 7");
  });
  it("weist eine IBAN mit falscher Prüfziffer ab", () => {
    expect(ibanPruefen("CH94 0076 2011 6238 5295 7").valid).toBe(false);
  });
  it("weist Unsinn/zu kurze Eingaben ab", () => {
    expect(ibanPruefen("HALLO").valid).toBe(false);
    expect(ibanPruefen("").valid).toBe(false);
  });
});

describe("rechnungSumme & chf", () => {
  it("rechnet Netto/MwSt/Brutto korrekt (CH 8.1%)", () => {
    const s = rechnungSumme([{ text: "A", menge: 2, einzelpreis: 100 }], 8.1);
    expect(s.netto).toBe(200);
    expect(s.mwst).toBe(16.2);
    expect(s.brutto).toBe(216.2);
  });
  it("summiert mehrere Positionen und behandelt fehlende Werte als 0", () => {
    const s = rechnungSumme(
      [
        { text: "A", menge: 3, einzelpreis: 10 },
        { text: "B", menge: 0, einzelpreis: 999 },
      ],
      0,
    );
    expect(s.netto).toBe(30);
    expect(s.mwst).toBe(0);
    expect(s.brutto).toBe(30);
  });
  it("formatiert Beträge im Schweizer Format mit Hochkomma", () => {
    expect(chf(1234.5)).toBe("1'234.50");
    expect(chf(216.2)).toBe("216.20");
    expect(chf(1234567.89)).toBe("1'234'567.89");
    expect(chf(0)).toBe("0.00");
  });
});

describe("marge & stundensatz", () => {
  it("berechnet Gewinn, Marge% und Aufschlag%", () => {
    const m = marge(100, 150);
    expect(m.gewinn).toBe(50);
    expect(m.margeProz).toBe(33.3);
    expect(m.aufschlagProz).toBe(50);
  });
  it("marge ist robust bei 0 (keine Division durch 0)", () => {
    const m = marge(0, 0);
    expect(m.margeProz).toBe(0);
    expect(m.aufschlagProz).toBe(0);
  });
  it("kostendeckender Stundensatz inkl. Zielmarge", () => {
    expect(stundensatz(120000, 1200, 20)).toBe(125);
  });
  it("stundensatz = 0 ohne fakturierbare Stunden", () => {
    expect(stundensatz(120000, 0, 20)).toBe(0);
  });
});

describe("slug", () => {
  it("wandelt Umlaute/Sonderzeichen in einen sauberen Slug + Titel", () => {
    const r = slug("Offerte für Zürich");
    expect(r.slug).toBe("offerte-fuer-zuerich");
    expect(r.titel).toBe("Offerte Für Zürich");
  });
  it("entfernt führende/mehrfache Bindestriche", () => {
    expect(slug("  Hallo   Welt!!!  ").slug).toBe("hallo-welt");
  });
});

describe("passwortErzeugen", () => {
  it("erzeugt ein Passwort in der geforderten Länge nur aus gewählten Zeichen", () => {
    const pw = passwortErzeugen({ laenge: 20, gross: true, klein: false, zahlen: true, zeichen: false });
    expect(pw).toHaveLength(20);
    expect(pw).toMatch(/^[A-Z2-9]+$/);
  });
  it("begrenzt die Länge (min 4, max 64) und liefert '' ohne Zeichenauswahl", () => {
    expect(passwortErzeugen({ laenge: 1, gross: true, klein: true, zahlen: true, zeichen: true }).length).toBe(4);
    expect(passwortErzeugen({ laenge: 999, gross: true, klein: true, zahlen: true, zeichen: true }).length).toBe(64);
    expect(passwortErzeugen({ laenge: 16, gross: false, klein: false, zahlen: false, zeichen: false })).toBe("");
  });
});

describe("HTML-Erzeugung escapt Eingaben", () => {
  it("rechnungHtml escapt gefährliche Zeichen in Feldern", () => {
    const html = rechnungHtml({
      absender: "Firma <b>",
      empfaenger: "<script>alert(1)</script>",
      nummer: "R-1",
      datum: "01.01.2026",
      positionen: [{ text: "Beratung & Co", menge: 1, einzelpreis: 100 }],
      mwstSatz: 8.1,
      frist: "30",
    });
    expect(html).not.toContain("<script>alert(1)</script>");
    expect(html).toContain("&lt;script&gt;");
    expect(html).toContain("Beratung &amp; Co");
  });
  it("signaturHtml escapt den Namen", () => {
    const html = signaturHtml({ name: "<i>Max</i>", rolle: "", firma: "", tel: "", mail: "", web: "" });
    expect(html).toContain("&lt;i&gt;Max&lt;/i&gt;");
    expect(html).not.toContain("<i>Max</i>");
  });
});
