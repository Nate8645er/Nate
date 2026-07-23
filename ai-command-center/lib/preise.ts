/**
 * Preis-/Paket-Daten – zentrale, editierbare Quelle für die Verkaufsseite (/preise).
 *
 * WICHTIG: Die Beträge sind Beispielpreise. Passen Sie sie an Ihr Angebot an;
 * die Seite und der Vergleich lesen ausschliesslich aus dieser Datei.
 * Währung: CHF (Schweiz). `planId` verknüpft das Paket mit der internen
 * Abo-Stufe (Lizenz/Onboarding), damit Kauf → Zugang konsistent bleibt.
 *
 * Fünf Stufen von günstig bis Konzern: Solo, Start, Pro (beliebt),
 * Business, Enterprise.
 */

import type { PlanId } from "./agents/types";

export interface Paket {
  id: string;
  name: string;
  /** Interne Abo-Stufe, die der Kunde nach dem Kauf erhält. */
  planId: PlanId;
  /** Kurzer Nutzen-Untertitel. */
  untertitel: string;
  /** Für wen das Paket gedacht ist. */
  zielgruppe: string;
  /** Beispiel-Monatspreis in CHF (anpassen). */
  preisMonat: number;
  /** Beispiel-Jahrespreis in CHF (anpassen; meist mit Rabatt). */
  preisJahr: number;
  /** Optionales Abzeichen, z. B. „Beliebt". */
  badge?: string;
  /** Optisch hervorgehoben. */
  hervorgehoben?: boolean;
  /** Die wichtigsten Leistungen (kurz). */
  leistungen: string[];
  /** Text auf dem Kauf-Button. */
  cta: string;
}

export const PAKETE: readonly Paket[] = [
  {
    id: "gratis",
    name: "Gratis",
    planId: "FREE",
    untertitel: "Ihr KI-Team kostenlos kennenlernen.",
    zielgruppe: "Zum Ausprobieren",
    preisMonat: 0,
    preisJahr: 0,
    badge: "Kostenlos",
    leistungen: [
      "4 KI-Agenten zum Kennenlernen",
      "3 Missionen pro Tag",
      "Basis-Fähigkeiten & Vorschau im Browser",
      "Kein Zahlungsmittel nötig",
    ],
    cta: "Kostenlos starten",
  },
  {
    id: "solo",
    name: "Solo",
    planId: "PERSONAL",
    untertitel: "Ihr KI-Einstieg für Einzelpersonen.",
    zielgruppe: "Einzelpersonen & Einstieg",
    preisMonat: 19,
    preisJahr: 190,
    leistungen: [
      "4 KI-Agenten (Kern-Team)",
      "10 Missionen pro Tag",
      "Basis-Fähigkeiten: Texte, Offerten, E-Mails",
      "Ergebnis-Vorschau & Download",
      "Support per E-Mail",
    ],
    cta: "Solo wählen",
  },
  {
    id: "start",
    name: "Start",
    planId: "STARTER",
    untertitel: "Ihre kompakte KI-Abteilung für den Start.",
    zielgruppe: "Selbstständige & kleine Teams",
    preisMonat: 49,
    preisJahr: 490,
    leistungen: [
      "12 spezialisierte KI-Agenten",
      "25 Missionen pro Tag",
      "Fähigkeiten inkl. Verkauf & Marketing",
      "E-Mail-Zentrale & Autopilot",
      "Qualitäts-Score je Ergebnis",
    ],
    cta: "Start wählen",
  },
  {
    id: "pro",
    name: "Pro",
    planId: "PROFESSIONAL",
    untertitel: "Fachteams inkl. Finanzen, Analyse & erste Integrationen.",
    zielgruppe: "Wachsende Firmen",
    preisMonat: 179,
    preisJahr: 1790,
    badge: "Beliebt",
    hervorgehoben: true,
    leistungen: [
      "Alles aus Start – plus:",
      "50 Agenten in Fachteams",
      "Dokumentenanalyse (PDF, Word, Excel)",
      "Erste Firmen-Integrationen & Prioritäts-Verarbeitung",
      "Wissensdatenbank (RAG) für eigene Dokumente",
    ],
    cta: "Pro wählen",
  },
  {
    id: "business",
    name: "Business",
    planId: "BUSINESS",
    untertitel: "Ihre digitale Abteilung mit allen Integrationen.",
    zielgruppe: "Grössere Teams & Firmen",
    preisMonat: 390,
    preisJahr: 3900,
    leistungen: [
      "Alles aus Pro – plus:",
      "250 KI-Agenten als digitale Abteilung",
      "Unbegrenzte Missionen",
      "Alle Firmen-Integrationen & eigene Workflows",
      "Team-Zugänge mit Rollen, dedizierter Ansprechpartner",
    ],
    cta: "Business wählen",
  },
  {
    id: "enterprise",
    name: "Enterprise",
    planId: "ENTERPRISE",
    untertitel: "Individuelle KI-Infrastruktur nach Mass.",
    zielgruppe: "Grosse Unternehmen",
    preisMonat: 790,
    preisJahr: 7900,
    leistungen: [
      "Alles aus Business – plus:",
      "Bis 1000 virtuelle Mitarbeitende",
      "Individuelle Integrationen (ERP/CRM, SSO, Maschinen)",
      "Private Cloud oder On-Premise, eigene Modelle",
      "SLA & Sicherheit nach Mass, persönliche Begleitung",
    ],
    cta: "Kontakt aufnehmen",
  },
];

/** Vergleichstabelle – Zeilen mit einem Wert je Paket (in PAKETE-Reihenfolge). */
export interface VergleichZeile {
  label: string;
  werte: string[];
}
export interface VergleichGruppe {
  gruppe: string;
  zeilen: VergleichZeile[];
}

export const VERGLEICH: readonly VergleichGruppe[] = [
  {
    gruppe: "Team & Leistung",
    zeilen: [
      { label: "KI-Agenten", werte: ["4", "4", "12", "50", "250", "bis 1000"] },
      { label: "Missionen pro Tag", werte: ["3", "10", "25", "100", "Unbegrenzt", "Unbegrenzt"] },
      { label: "Qualitäts-Score je Ergebnis", werte: ["✓", "✓", "✓", "✓", "✓", "✓"] },
      { label: "Prioritäts-Verarbeitung", werte: ["–", "–", "–", "✓", "✓", "✓"] },
    ],
  },
  {
    gruppe: "Integrationen & Automation",
    zeilen: [
      { label: "Firmen-Integrationen", werte: ["–", "–", "Basis", "Erweitert", "Alle", "Alle + individuell"] },
      { label: "Autopilot / Workflows", werte: ["–", "–", "✓", "✓", "✓", "✓"] },
      { label: "Eigene APIs & Maschinen", werte: ["–", "–", "–", "✓", "✓", "✓"] },
      { label: "Wissensdatenbank (RAG)", werte: ["–", "–", "–", "✓", "✓", "✓"] },
    ],
  },
  {
    gruppe: "Team & Support",
    zeilen: [
      { label: "Team-Zugänge", werte: ["1", "1", "1", "5", "Ganzes Team", "Unbegrenzt"] },
      { label: "Support", werte: ["Community", "E-Mail", "E-Mail", "Priorität", "Priorität", "Persönlich + SLA"] },
      { label: "Private Cloud / On-Premise", werte: ["–", "–", "–", "–", "–", "✓"] },
      { label: "Schulung & Onboarding", werte: ["Videos", "Videos", "Videos", "Videos + Setup", "Setup", "Persönlich"] },
    ],
  },
];

/** Häufige Fragen für die Verkaufsseite. */
export const FAQ: readonly { frage: string; antwort: string }[] = [
  {
    frage: "Bekomme ich nach dem Kauf sofort Zugang?",
    antwort:
      "Ja. Nach der Zahlung erhalten Sie Ihren Lizenzschlüssel per E-Mail und öffnen damit sofort Ihr Dashboard – auf PC oder Handy, ohne separates Konto.",
  },
  {
    frage: "Kann ich mein Abo jederzeit wechseln oder kündigen?",
    antwort:
      "Ja. Sie können jederzeit auf ein höheres oder tieferes Paket wechseln. Die Abrechnung passt sich automatisch an.",
  },
  {
    frage: "Sind meine Firmendaten sicher?",
    antwort:
      "Ihre Arbeitsdaten bleiben in Ihrer Umgebung. Wichtige, schreibende Schritte laufen nur mit Ihrer ausdrücklichen Freigabe. Enterprise bietet zusätzlich private Cloud oder On-Premise.",
  },
  {
    frage: "Ist das ein Chatbot?",
    antwort:
      "Nein. Sie geben einen Auftrag, und Ihre KI-Belegschaft führt ihn bis zum fertigen, geprüften Ergebnis aus – E-Mails, Angebote, Berichte, Code.",
  },
  {
    frage: "Welche Zahlungsarten gibt es?",
    antwort:
      "Kreditkarte und weitere gängige Methoden über einen sicheren Checkout. Rechnungen und Zahlungen werden automatisch synchronisiert.",
  },
];

/** CHF-Betrag als Anzeige-String (Schweizer Format, ohne Rappen). */
export function chf(betrag: number): string {
  return "CHF " + betrag.toLocaleString("de-CH");
}
