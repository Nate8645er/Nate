/**
 * Preis-/Paket-Daten – zentrale, editierbare Quelle für die Verkaufsseite (/preise).
 *
 * WICHTIG: Die Beträge sind Beispielpreise. Passen Sie sie an Ihr Angebot an;
 * die Seite und der Vergleich lesen ausschliesslich aus dieser Datei.
 * Währung: CHF (Schweiz). `planId` verknüpft das Paket mit der internen
 * Abo-Stufe (Lizenz/Onboarding), damit Kauf → Zugang konsistent bleibt.
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
    id: "basic",
    name: "Basic",
    planId: "STARTER",
    untertitel: "Ihre kompakte KI-Abteilung für den Start.",
    zielgruppe: "Einzelunternehmer & kleine Teams",
    preisMonat: 49,
    preisJahr: 490,
    leistungen: [
      "12 spezialisierte KI-Agenten in Fachteams",
      "25 Missionen pro Tag",
      "Fähigkeiten für Erstellen, Marketing, Verkauf & Analyse",
      "Fertige Dokumente: Offerten, Websites, Präsentationen, Verträge",
      "E-Mail-Zentrale: Antworten & Angebote in Sekunden",
      "Autopilot für wiederkehrende Aufgaben",
      "Qualitäts-Score für jedes Ergebnis",
      "Echte Dateien & Code mit Download",
      "Ergebnis-Vorschau direkt im Browser",
      "Vertonte Einrichtungs-Videos & Support per E-Mail",
    ],
    cta: "Basic wählen",
  },
  {
    id: "pro",
    name: "Pro",
    planId: "BUSINESS",
    untertitel: "Ihre digitale Abteilung mit allen Integrationen.",
    zielgruppe: "Wachsende Firmen & Teams",
    preisMonat: 149,
    preisJahr: 1490,
    badge: "Beliebt",
    hervorgehoben: true,
    leistungen: [
      "Alles aus Basic – plus:",
      "250 KI-Agenten als digitale Abteilung",
      "Unbegrenzte Missionen mit Prioritäts-Verarbeitung",
      "Alle Fähigkeiten inkl. Finanzen, Personal & Recht, Code",
      "Alle Firmen-Integrationen (M365, Google, Slack, Shopify, Stripe, eigene APIs)",
      "Firmen-Wissensdatenbank (RAG) für eigene Dokumente",
      "Eigene Workflows, Automationen & Freigaben",
      "Dokumentenanalyse (PDF, Word, Excel)",
      "Zugänge für Ihr ganzes Team mit Rollen",
      "Prioritäts-Support & dedizierter Ansprechpartner",
    ],
    cta: "Pro wählen",
  },
  {
    id: "enterprise",
    name: "Enterprise",
    planId: "ENTERPRISE",
    untertitel: "Individuelle KI-Infrastruktur nach Mass.",
    zielgruppe: "Grosse Unternehmen",
    preisMonat: 490,
    preisJahr: 4900,
    leistungen: [
      "Alles aus Pro – plus:",
      "Bis 1000 virtuelle Mitarbeitende",
      "Alle Fähigkeiten + individuelle KI-Strategie",
      "Individuelle Integrationen (ERP/CRM, SSO, Maschinen)",
      "Private Cloud oder On-Premise-Betrieb",
      "Eigene, trainierte KI-Modelle möglich",
      "SLA & Sicherheit nach Mass, Audit-Log",
      "Unbegrenzte Team-Zugänge",
      "Persönliche Begleitung, Schulung & Onboarding",
    ],
    cta: "Kontakt aufnehmen",
  },
];

/** Vergleichstabelle – Zeilen mit Werten je Paket (in PAKETE-Reihenfolge). */
export interface VergleichZeile {
  label: string;
  werte: [string, string, string];
}
export interface VergleichGruppe {
  gruppe: string;
  zeilen: VergleichZeile[];
}

export const VERGLEICH: readonly VergleichGruppe[] = [
  {
    gruppe: "Team & Leistung",
    zeilen: [
      { label: "KI-Agenten", werte: ["12", "250", "bis 1000"] },
      { label: "Missionen pro Tag", werte: ["25", "Unbegrenzt", "Unbegrenzt"] },
      { label: "Qualitäts-Score je Ergebnis", werte: ["✓", "✓", "✓"] },
      { label: "Prioritäts-Verarbeitung", werte: ["–", "✓", "✓"] },
    ],
  },
  {
    gruppe: "Integrationen & Automation",
    zeilen: [
      { label: "Firmen-Integrationen", werte: ["Basis", "Alle", "Alle + individuell"] },
      { label: "Autopilot / Workflows", werte: ["✓", "✓", "✓"] },
      { label: "Eigene APIs & Maschinen", werte: ["–", "✓", "✓"] },
      { label: "Wissensdatenbank (RAG)", werte: ["–", "✓", "✓"] },
    ],
  },
  {
    gruppe: "Team & Support",
    zeilen: [
      { label: "Team-Zugänge", werte: ["1", "Ganzes Team", "Unbegrenzt"] },
      { label: "Support", werte: ["E-Mail", "Priorität", "Persönlich + SLA"] },
      { label: "Private Cloud / On-Premise", werte: ["–", "–", "✓"] },
      { label: "Schulung & Onboarding", werte: ["Videos", "Videos + Setup", "Persönlich"] },
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
