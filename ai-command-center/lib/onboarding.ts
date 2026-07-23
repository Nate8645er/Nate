/**
 * Video-Onboarding – Single Source of Truth pro Abo-Tarif.
 *
 * Ziel: Nach dem Kauf hat der Kunde sofort einen persönlichen Einrichtungs-
 * Bereich (/onboarding): ein Übersichtsvideo, ein tarifspezifisches Deep-Dive-
 * Video (modular/versioniert einhängbar) und eine interaktive Checkliste, die
 * Schritt für Schritt durch Einrichtung, Dienst-Anbindung, Agenten-Setup,
 * Dashboard-Nutzung und Automationen führt.
 *
 * WARTUNG: Alle Inhalte hier zentral pflegen. Sobald ein tarifspezifisches
 * Video produziert ist (mit Higgsfield), einfach `videoSrc` beim Tarif setzen
 * und `videoVersion` erhöhen – der Bereich zeigt es dann automatisch an.
 */

import type { PlanId } from "./agents/types";

/** Ein Schritt der Einrichtungs-Checkliste. */
export interface OnboardingStep {
  /** Stabile Kennung für die Fortschritts-Speicherung (localStorage). */
  id: string;
  titel: string;
  text: string;
  /** Sprung an die passende Stelle im System. */
  href?: string;
  /** Kurzer Tooltip mit Zusatzhinweis. */
  tooltip?: string;
}

export interface TierTutorial {
  plan: PlanId;
  name: string;
  kurz: string;
  /** Version des Tarif-Videos – erhöht sich bei Produkt-/Video-Änderungen. */
  videoVersion: string;
  /**
   * Tarifspezifisches Deep-Dive-Video. `null`, solange es noch produziert wird –
   * dann zeigt der Bereich ehrlich „in Produktion" statt eines Platzhalters.
   */
  videoSrc: string | null;
  enthalten: string[];
  schritte: OnboardingStep[];
}

/** Systemrundgang (echte Bildschirm-Aufnahme aller Bereiche) – gilt für alle Tarife. */
export const UEBERSICHT_VIDEO = {
  src: "/ki-system-tour.mp4",
  poster: "/shop-hero.webp",
  titel: "Systemrundgang: Ihr AI Command Center in Aktion",
  dauer: "echter Rundgang durch alle Bereiche",
};

/* ------------------------------------------------------------------ */
/* Wiederverwendbare Schritt-Bausteine (pro Tarif kombiniert).         */
/* ------------------------------------------------------------------ */

const S = {
  aktivieren: {
    id: "aktivieren",
    titel: "Zugang aktivieren",
    text: "Öffnen Sie /dashboard?key=IHR-SCHLÜSSEL auf PC oder Handy – die Lizenz aktiviert sich automatisch. Den Schlüssel haben Sie per E-Mail und in der Shop-Bestellung erhalten.",
    href: "/dashboard",
    tooltip: "Der Schlüssel wird lokal in Ihrem Browser gespeichert. Kein separates Konto nötig.",
  },
  firma: {
    id: "firma",
    titel: "Firma einrichten",
    text: "Hinterlegen Sie Branche, Tonalität und Ziele. Ihr KI-Team stellt sich darauf ein und liefert passendere Ergebnisse.",
    href: "/einstellungen",
    tooltip: "Diese Angaben fliessen in jede Mission ein und bleiben in Ihrem Browser.",
  },
  ersteMission: {
    id: "erste-mission",
    titel: "Erste Mission starten",
    text: "Geben Sie im Dashboard einen Auftrag – z. B. «Erstelle eine Angebots-E-Mail für Kunde X». Ihr Team plant, arbeitet und liefert das Ergebnis.",
    href: "/dashboard",
    tooltip: "Kein Chatbot: Sie geben einen Befehl, die Belegschaft führt ihn bis zum fertigen Ergebnis aus.",
  },
  ergebnis: {
    id: "ergebnis",
    titel: "Ergebnis prüfen & herunterladen",
    text: "Sehen Sie sich den Quality-Score an und laden Sie die fertigen Dateien herunter. Alles gehört Ihnen.",
    tooltip: "Jedes Ergebnis wird vor der Auslieferung automatisch geprüft und mit 0–100 bewertet.",
  },
  skills: {
    id: "skills",
    titel: "Skills entdecken",
    text: "Stöbern Sie durch die Befehle Ihrer Belegschaft und starten Sie einen davon mit einem Klick.",
    href: "/faehigkeiten",
  },
  email: {
    id: "email",
    titel: "E-Mail-Zentrale nutzen",
    text: "Eingehende Mail einfügen → fertige Antwort erhalten, oder Offerten schreiben lassen. Ein Klick öffnet Gmail vorbefüllt.",
    href: "/email",
  },
  dienste: {
    id: "dienste",
    titel: "Dienste auswählen & anbinden",
    text: "Wählen Sie, welche Systeme angebunden werden (Microsoft 365, Google Workspace, Slack, Shopify, Stripe, eigene APIs). Die Anbindung wird pro Firma sicher eingerichtet.",
    href: "/integrationen",
    tooltip: "Wichtige/schreibende Schritte laufen nur mit Ihrer ausdrücklichen Freigabe.",
  },
  autopilot: {
    id: "autopilot",
    titel: "Automationen erstellen",
    text: "Legen Sie wiederkehrende Aufträge im Autopilot an – Wochenpläne, Berichte, Angebotsideen erledigt Ihre Belegschaft dann regelmässig.",
    href: "/workflows",
    tooltip: "Routine läuft autonom; wichtige Schritte werden Ihnen vor der Ausführung zur Freigabe vorgelegt.",
  },
  team: {
    id: "team",
    titel: "Abteilungen & Agenten ansehen",
    text: "Verschaffen Sie sich einen Überblick über Ihre Belegschaft: Führung, Entwicklung, Marketing, Kundenservice, Finanzen, Medien und mehr.",
    href: "/agenten",
  },
  freigaben: {
    id: "freigaben",
    titel: "Freigaben & Zugänge fürs Team",
    text: "Richten Sie Zugänge für Ihre Mitarbeitenden ein und legen Sie fest, welche Schritte eine Freigabe brauchen.",
    href: "/benutzer",
  },
  ansprechpartner: {
    id: "ansprechpartner",
    titel: "Persönliche Einrichtung vereinbaren",
    text: "Für individuelle Integrationen, private Umgebung oder On-Premise: Vereinbaren Sie ein Gespräch mit Ihrem dedizierten Ansprechpartner.",
    href: "/integrationen",
    tooltip: "Enterprise-spezifische Anbindungen (ERP/CRM, SSO, On-Premise) werden gemeinsam mit Ihnen umgesetzt.",
  },
} as const;

/* ------------------------------------------------------------------ */
/* Pro-Tarif-Tutorials.                                                */
/* ------------------------------------------------------------------ */

export const TUTORIALS: readonly TierTutorial[] = [
  {
    plan: "FREE",
    name: "Gratis",
    kurz: "Lernen Sie Ihr KI-Team in wenigen Minuten kennen.",
    videoVersion: "1.0",
    videoSrc: "/anleitung-free.mp4",
    enthalten: [
      "4 KI-Agenten zum Kennenlernen",
      "3 Missionen pro Tag",
      "Basis-Skills und Ergebnis-Vorschau im Browser",
    ],
    schritte: [S.aktivieren, S.firma, S.ersteMission, S.ergebnis, S.skills],
  },
  {
    plan: "PERSONAL",
    name: "Solo",
    kurz: "Ihr persönliches Kern-Team für den Alltag – inkl. E-Mail und Autopilot.",
    videoVersion: "1.0",
    videoSrc: "/anleitung-personal.mp4",
    enthalten: [
      "Kern-Team (Commander, Builder, Analyst, Quality)",
      "10 Missionen pro Tag, fertige Dateien mit Download",
      "E-Mail-Zentrale, CRM & Autopilot",
    ],
    schritte: [S.aktivieren, S.firma, S.ersteMission, S.ergebnis, S.email, S.autopilot, S.skills],
  },
  {
    plan: "STARTER",
    name: "Start",
    kurz: "Ihre kompakte KI-Abteilung inkl. Verkauf & Marketing.",
    videoVersion: "1.0",
    videoSrc: "/anleitung-starter.mp4",
    enthalten: [
      "12 spezialisierte Agenten, 25 Missionen pro Tag",
      "Skills inkl. Verkauf & Marketing, Quality-Score je Ergebnis",
      "Echte Dateien und Code mit Download",
    ],
    schritte: [S.aktivieren, S.firma, S.ersteMission, S.ergebnis, S.skills, S.email, S.autopilot, S.team],
  },
  {
    plan: "PROFESSIONAL",
    name: "Pro",
    kurz: "50 Agenten in Fachteams inkl. Finanzen, Analyse und ersten Integrationen.",
    videoVersion: "1.0",
    videoSrc: "/anleitung-professional.mp4",
    enthalten: [
      "50 Agenten in Fachteams organisiert",
      "Dokumentenanalyse (PDF, Word, Excel)",
      "5 Firmen-Integrationen inklusive, Prioritäts-Verarbeitung",
    ],
    schritte: [S.aktivieren, S.firma, S.dienste, S.ersteMission, S.ergebnis, S.autopilot, S.team, S.skills],
  },
  {
    plan: "BUSINESS",
    name: "Business",
    kurz: "Ihre digitale Abteilung mit 250 Agenten, allen Integrationen und Team-Zugängen.",
    videoVersion: "1.0",
    videoSrc: "/anleitung-business.mp4",
    enthalten: [
      "250 Agenten als digitale Abteilung",
      "Alle Firmen-Integrationen, eigene Workflows und Freigaben",
      "Zugänge für Ihr ganzes Team, dedizierter Ansprechpartner",
    ],
    schritte: [S.aktivieren, S.firma, S.dienste, S.freigaben, S.ersteMission, S.autopilot, S.team, S.email],
  },
  {
    plan: "ENTERPRISE",
    name: "Enterprise",
    kurz: "Bis 1000 virtuelle Mitarbeitende, individuelle Infrastruktur und persönliche Begleitung.",
    videoVersion: "1.0",
    videoSrc: "/anleitung-enterprise.mp4",
    enthalten: [
      "Bis 1000 virtuelle Mitarbeitende, alle Skills + KI-Strategie",
      "Individuelle KI-Infrastruktur, private Cloud oder On-Premise",
      "SLA und Sicherheit nach Mass, persönliche Begleitung",
    ],
    schritte: [S.aktivieren, S.ansprechpartner, S.firma, S.dienste, S.freigaben, S.autopilot, S.team],
  },
];

/** Tutorial zu einem Plan holen (Fallback: Starter als solide Mitte). */
export function tutorialFuer(plan: PlanId): TierTutorial {
  return TUTORIALS.find((t) => t.plan === plan) ?? TUTORIALS[2];
}
