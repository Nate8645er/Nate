/**
 * Baut die Willkommens-/Lizenz-E-Mail nach einem erfolgreichen Kauf.
 * Reine Funktion (kein Versand, keine Seiteneffekte) → gut testbar.
 */

import type { MailEingabe } from "./mail";

export interface WillkommenDaten {
  an: string;
  planName: string;
  lizenzSchluessel: string;
  /** Basis-URL des Shops/Apps, z. B. https://ihr-shop.ch */
  appUrl: string;
}

export function willkommensMail(d: WillkommenDaten): MailEingabe {
  const einloesenUrl = `${d.appUrl.replace(/\/$/, "")}/onboarding`;
  const text = [
    `Willkommen beim AI Command Center – Ihr Paket ${d.planName} ist aktiv.`,
    "",
    "Ihr Lizenzschlüssel:",
    d.lizenzSchluessel,
    "",
    "So starten Sie:",
    `1. Öffnen Sie ${einloesenUrl}`,
    "2. Lizenzschlüssel eingeben und einlösen",
    "3. Ihre KI-Abteilung ist freigeschaltet – legen Sie los.",
    "",
    "Bewahren Sie diesen Schlüssel gut auf. Sie finden ihn jederzeit auch in",
    "Ihrem Konto wieder. Bei Fragen antworten Sie einfach auf diese E-Mail.",
    "",
    "Freundliche Grüsse",
    "Ihr AI Command Center",
  ].join("\n");

  const html = [
    `<h2>Willkommen beim AI Command Center</h2>`,
    `<p>Ihr Paket <strong>${escapeHtml(d.planName)}</strong> ist aktiv.</p>`,
    `<p><strong>Ihr Lizenzschlüssel:</strong></p>`,
    `<p style="font-family:monospace;font-size:16px;background:#f5f2ea;padding:12px 16px;border-radius:8px;letter-spacing:.5px">${escapeHtml(d.lizenzSchluessel)}</p>`,
    `<p>So starten Sie:</p>`,
    `<ol><li>Öffnen Sie <a href="${escapeAttr(einloesenUrl)}">${escapeHtml(einloesenUrl)}</a></li>`,
    `<li>Lizenzschlüssel eingeben und einlösen</li>`,
    `<li>Ihre KI-Abteilung ist freigeschaltet – legen Sie los.</li></ol>`,
    `<p>Bewahren Sie den Schlüssel gut auf; Sie finden ihn auch in Ihrem Konto.</p>`,
    `<p>Freundliche Grüsse<br>Ihr AI Command Center</p>`,
  ].join("");

  return {
    an: d.an,
    betreff: `Ihr Zugang zum AI Command Center – Paket ${d.planName}`,
    text,
    html,
  };
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function escapeAttr(s: string): string {
  return escapeHtml(s).replace(/"/g, "&quot;");
}
