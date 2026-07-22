/**
 * Blitz-Werkzeuge – echte, deterministische Funktionen, die SOFORT (ohne
 * KI, ohne Netz) ein fertiges Ergebnis liefern. Das ist die "in Sekunden
 * erledigte Arbeit": reine Berechnung/Erzeugung im Browser, in Millisekunden.
 *
 * Alle Funktionen sind pur (keine Seiteneffekte) und einzeln testbar.
 */

/* --------------------------- IBAN-Prüfung -------------------------------- */

/** Prüft eine IBAN nach ISO 13616 (Modulo-97). Formatiert bei Erfolg. */
export function ibanPruefen(input: string): { valid: boolean; formatiert: string; land: string } {
  const iban = input.replace(/\s+/g, "").toUpperCase();
  const land = iban.slice(0, 2);
  if (!/^[A-Z]{2}[0-9A-Z]{13,32}$/.test(iban)) {
    return { valid: false, formatiert: iban, land };
  }
  // Erste 4 Zeichen ans Ende, Buchstaben -> Zahlen (A=10 … Z=35).
  const umgestellt = iban.slice(4) + iban.slice(0, 4);
  let rest = 0;
  for (const ch of umgestellt) {
    const wert = /[0-9]/.test(ch) ? ch : (ch.charCodeAt(0) - 55).toString();
    for (const d of wert) rest = (rest * 10 + Number(d)) % 97;
  }
  const valid = rest === 1;
  const formatiert = iban.replace(/(.{4})/g, "$1 ").trim();
  return { valid, formatiert, land };
}

/* ----------------------------- Passwörter -------------------------------- */

export interface PasswortOpt {
  laenge: number;
  gross: boolean;
  klein: boolean;
  zahlen: boolean;
  zeichen: boolean;
}

/** Erzeugt ein kryptographisch zufälliges Passwort (crypto.getRandomValues). */
export function passwortErzeugen(opt: PasswortOpt): string {
  const teile = [
    opt.gross ? "ABCDEFGHJKLMNPQRSTUVWXYZ" : "",
    opt.klein ? "abcdefghijkmnopqrstuvwxyz" : "",
    opt.zahlen ? "23456789" : "",
    opt.zeichen ? "!@#$%&*+-=?" : "",
  ];
  const alphabet = teile.join("");
  const laenge = Math.max(4, Math.min(64, Math.floor(opt.laenge) || 16));
  if (!alphabet) return "";
  const rnd = new Uint32Array(laenge);
  crypto.getRandomValues(rnd);
  let out = "";
  for (let i = 0; i < laenge; i++) out += alphabet[rnd[i] % alphabet.length];
  return out;
}

/* ----------------------------- Rechnung ---------------------------------- */

export interface Position {
  text: string;
  menge: number;
  einzelpreis: number;
}

/** Rechnet Positionen zu Netto/MwSt/Brutto (Schweizer Sätze). */
export function rechnungSumme(positionen: Position[], mwstSatz: number): {
  netto: number;
  mwst: number;
  brutto: number;
} {
  const netto = positionen.reduce((s, p) => s + (p.menge || 0) * (p.einzelpreis || 0), 0);
  const mwst = Math.round(netto * (mwstSatz / 100) * 100) / 100;
  const brutto = Math.round((netto + mwst) * 100) / 100;
  return { netto: Math.round(netto * 100) / 100, mwst, brutto };
}

/** Betrag als CHF-String (Schweizer Format: 1'234.50). */
export function chf(betrag: number): string {
  const [g, r = "00"] = betrag.toFixed(2).split(".");
  return `${g.replace(/\B(?=(\d{3})+(?!\d))/g, "'")}.${r}`;
}

/** Baut eine versandfertige HTML-Rechnung (druck-/downloadbar). */
export function rechnungHtml(v: {
  absender: string;
  empfaenger: string;
  nummer: string;
  datum: string;
  positionen: Position[];
  mwstSatz: number;
  frist: string;
}): string {
  const s = rechnungSumme(v.positionen, v.mwstSatz);
  const zeilen = v.positionen
    .map(
      (p) =>
        `<tr><td>${esc(p.text)}</td><td class="r">${p.menge}</td><td class="r">${chf(p.einzelpreis)}</td><td class="r">${chf((p.menge || 0) * (p.einzelpreis || 0))}</td></tr>`,
    )
    .join("");
  return `<!doctype html><html lang="de"><head><meta charset="utf-8">
<title>Rechnung ${esc(v.nummer)}</title>
<style>body{font-family:system-ui,Arial,sans-serif;color:#1a1a1a;max-width:760px;margin:40px auto;padding:0 24px}
h1{font-size:22px;margin:0 0 4px}.muted{color:#666;font-size:13px}
.head{display:flex;justify-content:space-between;gap:24px;margin:24px 0}
table{width:100%;border-collapse:collapse;margin-top:16px}th,td{padding:8px 6px;border-bottom:1px solid #e5e5e5;text-align:left;font-size:14px}
.r{text-align:right}tfoot td{border:0;font-size:14px}tfoot .tot{font-weight:700;font-size:16px;border-top:2px solid #1a1a1a}
.box{white-space:pre-line;font-size:14px}</style></head><body>
<h1>Rechnung</h1><div class="muted">Nr. ${esc(v.nummer)} · ${esc(v.datum)}</div>
<div class="head"><div class="box"><strong>Von</strong>\n${esc(v.absender)}</div>
<div class="box"><strong>An</strong>\n${esc(v.empfaenger)}</div></div>
<table><thead><tr><th>Leistung</th><th class="r">Menge</th><th class="r">Einzel</th><th class="r">Betrag</th></tr></thead>
<tbody>${zeilen}</tbody>
<tfoot><tr><td colspan="3" class="r">Netto</td><td class="r">${chf(s.netto)}</td></tr>
<tr><td colspan="3" class="r">MwSt ${v.mwstSatz}%</td><td class="r">${chf(s.mwst)}</td></tr>
<tr class="tot"><td colspan="3" class="r">Total CHF</td><td class="r">${chf(s.brutto)}</td></tr></tfoot></table>
<p class="muted">Zahlbar innert ${esc(v.frist)} Tagen. Besten Dank.</p></body></html>`;
}

/* --------------------- Marge & Stundensatz ------------------------------- */

/** Marge/Aufschlag/Gewinn aus Einkauf & Verkauf. */
export function marge(einkauf: number, verkauf: number): { gewinn: number; margeProz: number; aufschlagProz: number } {
  const gewinn = Math.round((verkauf - einkauf) * 100) / 100;
  const margeProz = verkauf ? Math.round((gewinn / verkauf) * 1000) / 10 : 0;
  const aufschlagProz = einkauf ? Math.round((gewinn / einkauf) * 1000) / 10 : 0;
  return { gewinn, margeProz, aufschlagProz };
}

/** Kostendeckender Stundensatz aus Jahreskosten + fakturierbaren Stunden + Zielmarge. */
export function stundensatz(jahreskosten: number, fakturierbareStunden: number, margeProz: number): number {
  if (fakturierbareStunden <= 0) return 0;
  const kostenSatz = jahreskosten / fakturierbareStunden;
  const satz = kostenSatz / (1 - Math.min(0.95, Math.max(0, margeProz / 100)));
  return Math.round(satz * 100) / 100;
}

/* --------------------------- E-Mail-Signatur ----------------------------- */

export function signaturHtml(v: {
  name: string;
  rolle: string;
  firma: string;
  tel: string;
  mail: string;
  web: string;
}): string {
  const zeile = (label: string, wert: string, href?: string) =>
    wert ? `<div style="font-size:13px;color:#444">${label}${href ? `<a href="${esc(href)}" style="color:#c25e0e;text-decoration:none">${esc(wert)}</a>` : esc(wert)}</div>` : "";
  return `<table cellpadding="0" cellspacing="0" style="font-family:Arial,sans-serif"><tr><td style="border-left:3px solid #ff8c2a;padding-left:12px">
<div style="font-size:15px;font-weight:700;color:#1a1a1a">${esc(v.name)}</div>
${v.rolle ? `<div style="font-size:13px;color:#666">${esc(v.rolle)}${v.firma ? ` · ${esc(v.firma)}` : ""}</div>` : v.firma ? `<div style="font-size:13px;color:#666">${esc(v.firma)}</div>` : ""}
<div style="height:6px"></div>
${zeile("☎ ", v.tel, v.tel ? `tel:${v.tel.replace(/\s+/g, "")}` : undefined)}
${zeile("✉ ", v.mail, v.mail ? `mailto:${v.mail}` : undefined)}
${zeile("🌐 ", v.web, v.web ? (v.web.startsWith("http") ? v.web : `https://${v.web}`) : undefined)}
</td></tr></table>`;
}

/* ------------------------------ SEO-Slug --------------------------------- */

/** URL-Slug + sauberer Titel aus freiem Text. */
export function slug(text: string): { slug: string; titel: string } {
  const clean = text
    .toLowerCase()
    .replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss")
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
  const titel = text.trim().replace(/\s+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return { slug: clean, titel };
}

/* ------------------------------ Helfer ----------------------------------- */

function esc(s: string): string {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c] as string));
}
