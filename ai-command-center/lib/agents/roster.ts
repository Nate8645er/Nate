/**
 * Agenten-Roster – der benannte Spezialisten-Katalog des AI Command Center.
 *
 * Das ist die "Belegschaft" der Plattform: alle spezialisierten Agenten,
 * die der Commander für eine Mission einsetzen kann. Der Katalog ist echte
 * Grundlage, kein Deko-Text:
 *  - Die Agenten-Übersicht (/agenten) rendert daraus die volle Mannschaft.
 *  - Der Org-Planer (team.ts) bekommt diese Namen als bevorzugte Rollen,
 *    damit BUSINESS/ENTERPRISE-Missionen tatsächlich benannte Spezialisten
 *    besetzen statt generischer Rollen.
 *  - Neue Spezialisten kann der Commander jederzeit dynamisch ergänzen
 *    (Org-Modus) – der Katalog ist die Basis, keine Obergrenze.
 */

export type Abteilung =
  | "Führung & Steuerung"
  | "Forschung & Wissen"
  | "Entwicklung & Technik"
  | "Marketing & Vertrieb"
  | "Kundenservice & Kommunikation"
  | "Dokumente & Recht"
  | "Finanzen & Personal"
  | "Medien & Kreation"
  | "Betrieb & Sicherheit";

export interface RosterAgent {
  /** Stabile Kennung, z. B. "ceo". */
  id: string;
  /** Anzeigename, z. B. "CEO-Agent". */
  name: string;
  abteilung: Abteilung;
  /** Ein Satz: wofür dieser Agent zuständig ist. */
  aufgabe: string;
  /** 2–3 konkrete Fähigkeiten für die Übersicht. */
  kann: readonly string[];
  /**
   * true = Rolle ist im Katalog, aber die Laufzeit-Fähigkeit (z. B. echte
   * Bild-/Video-/Sprach-Verarbeitung) ist noch im Ausbau. Ehrlich als
   * "geplant" gekennzeichnet, statt mehr zu versprechen als der Code liefert.
   */
  geplant?: boolean;
}

/** Reihenfolge der Abteilungen in der Übersicht. */
export const ABTEILUNGEN: readonly Abteilung[] = [
  "Führung & Steuerung",
  "Forschung & Wissen",
  "Entwicklung & Technik",
  "Marketing & Vertrieb",
  "Kundenservice & Kommunikation",
  "Dokumente & Recht",
  "Finanzen & Personal",
  "Medien & Kreation",
  "Betrieb & Sicherheit",
];

/** Akzentnuance je Abteilung (für die Übersichts-Kacheln). */
export const ABTEILUNG_AKZENT: Record<Abteilung, string> = {
  "Führung & Steuerung": "#ff8c2a",
  "Forschung & Wissen": "#8b5cf6",
  "Entwicklung & Technik": "#22c55e",
  "Marketing & Vertrieb": "#ec4899",
  "Kundenservice & Kommunikation": "#06b6d4",
  "Dokumente & Recht": "#eab308",
  "Finanzen & Personal": "#14b8a6",
  "Medien & Kreation": "#f97316",
  "Betrieb & Sicherheit": "#ef4444",
};

export const AGENT_ROSTER: readonly RosterAgent[] = [
  // ---------- Führung & Steuerung ----------
  {
    id: "ceo",
    name: "CEO-Agent (Commander)",
    abteilung: "Führung & Steuerung",
    aufgabe: "Versteht Ihr Ziel, plant die Mission und verteilt die Arbeit auf das Team.",
    kann: ["Auftrag zerlegen", "Team zusammenstellen", "Ergebnis abnehmen"],
  },
  {
    id: "projektmanager",
    name: "Projektmanager-Agent",
    abteilung: "Führung & Steuerung",
    aufgabe: "Koordiniert Aufgaben, Reihenfolge und Abhängigkeiten über mehrere Agenten.",
    kann: ["Aufgaben priorisieren", "Fortschritt verfolgen", "Termine planen"],
  },
  {
    id: "planung",
    name: "Planungs-Agent",
    abteilung: "Führung & Steuerung",
    aufgabe: "Entwirft den konkreten Lösungsweg, bevor gearbeitet wird.",
    kann: ["Schritte planen", "Ressourcen abschätzen", "Risiken erkennen"],
  },

  // ---------- Forschung & Wissen ----------
  {
    id: "forschung",
    name: "Forschungs-Agent",
    abteilung: "Forschung & Wissen",
    aufgabe: "Recherchiert Fakten, Quellen und Hintergründe für fundierte Ergebnisse.",
    kann: ["Web-Recherche", "Quellen prüfen", "Zusammenfassen"],
  },
  {
    id: "browser",
    name: "Browser-Agent",
    abteilung: "Forschung & Wissen",
    aufgabe: "Liest Webseiten live und beschafft aktuelle Informationen mit Quellen.",
    kann: ["Seiten lesen", "Daten extrahieren", "Quellen belegen"],
  },
  {
    id: "wissen",
    name: "Wissens-Agent",
    abteilung: "Forschung & Wissen",
    aufgabe: "Verwaltet Ihr Firmenwissen und bringt es in jede Mission ein.",
    kann: ["Wissen speichern", "Kontext liefern", "Wiederfinden"],
  },
  {
    id: "datenanalyse",
    name: "Datenanalyse-Agent",
    abteilung: "Forschung & Wissen",
    aufgabe: "Wertet Zahlen und Tabellen aus und findet Muster und Auffälligkeiten.",
    kann: ["Tabellen auswerten", "Trends erkennen", "Empfehlungen"],
  },
  {
    id: "bi",
    name: "Business-Intelligence-Agent",
    abteilung: "Forschung & Wissen",
    aufgabe: "Verdichtet Daten zu Kennzahlen und Entscheidungsgrundlagen.",
    kann: ["KPIs bilden", "Dashboards entwerfen", "Reports"],
  },

  // ---------- Entwicklung & Technik ----------
  {
    id: "programmierer",
    name: "Programmierer-Agent",
    abteilung: "Entwicklung & Technik",
    aufgabe: "Schreibt lauffähigen Code – von Script bis Web-Anwendung.",
    kann: ["Code schreiben", "Features bauen", "Dateien liefern"],
  },
  {
    id: "debug",
    name: "Debug-Agent",
    abteilung: "Entwicklung & Technik",
    aufgabe: "Findet und behebt Fehler im Code.",
    kann: ["Fehler suchen", "Ursache finden", "Fix vorschlagen"],
  },
  {
    id: "qa",
    name: "QA-Agent",
    abteilung: "Entwicklung & Technik",
    aufgabe: "Prüft jedes Ergebnis auf Qualität und vergibt einen Quality-Score.",
    kann: ["Ergebnis prüfen", "Score vergeben", "Verbesserungen"],
  },
  {
    id: "devops",
    name: "DevOps-Agent",
    abteilung: "Entwicklung & Technik",
    aufgabe: "Plant Build, Deployment und Betrieb von Software.",
    kann: ["CI/CD planen", "Deployment", "Betrieb"],
  },
  {
    id: "cloud",
    name: "Cloud-Agent",
    abteilung: "Entwicklung & Technik",
    aufgabe: "Berät zu Cloud-Ressourcen, Kosten und Skalierung.",
    kann: ["Cloud-Setup", "Kosten prüfen", "Skalierung"],
  },
  {
    id: "api",
    name: "API-Agent",
    abteilung: "Entwicklung & Technik",
    aufgabe: "Spezifiziert und verbindet Schnittstellen zu anderen Systemen.",
    kann: ["APIs entwerfen", "Anbinden", "Daten mappen"],
  },
  {
    id: "automatisierung",
    name: "Automatisierungs-Agent",
    abteilung: "Entwicklung & Technik",
    aufgabe: "Baut wiederkehrende Abläufe zu automatischen Workflows um.",
    kann: ["Abläufe analysieren", "Auslöser definieren", "Automatisieren"],
  },

  // ---------- Marketing & Vertrieb ----------
  {
    id: "marketing",
    name: "Marketing-Agent",
    abteilung: "Marketing & Vertrieb",
    aufgabe: "Entwickelt Kampagnen, Botschaften und Werbetexte.",
    kann: ["Kampagnen", "Texte", "Kanalplan"],
  },
  {
    id: "sales",
    name: "Sales-Agent",
    abteilung: "Marketing & Vertrieb",
    aufgabe: "Erstellt Angebote, Verkaufsskripte und Nachfass-Nachrichten.",
    kann: ["Angebote", "Verkaufsskript", "Nachfassen"],
  },
  {
    id: "social",
    name: "Social-Media-Agent",
    abteilung: "Marketing & Vertrieb",
    aufgabe: "Plant und schreibt Beiträge für alle sozialen Kanäle.",
    kann: ["Post-Pläne", "Captions", "Hashtags"],
  },
  {
    id: "seo",
    name: "SEO-Agent",
    abteilung: "Marketing & Vertrieb",
    aufgabe: "Optimiert Inhalte für bessere Auffindbarkeit bei Suchmaschinen.",
    kann: ["Keywords", "Meta-Texte", "Struktur"],
  },
  {
    id: "werbe",
    name: "Werbe-Agent",
    abteilung: "Marketing & Vertrieb",
    aufgabe: "Erstellt Anzeigentexte und Konzepte für Google/Meta/TikTok.",
    kann: ["Ad-Texte", "Zielgruppen", "Varianten"],
  },

  // ---------- Kundenservice & Kommunikation ----------
  {
    id: "kundenservice",
    name: "Kundenservice-Agent",
    abteilung: "Kundenservice & Kommunikation",
    aufgabe: "Beantwortet Kundenanfragen freundlich, korrekt und im Ton der Firma.",
    kann: ["Anfragen beantworten", "Deeskalieren", "Bausteine"],
  },
  {
    id: "support",
    name: "Support-Agent",
    abteilung: "Kundenservice & Kommunikation",
    aufgabe: "Löst technische Fragen und erstellt FAQ und Anleitungen.",
    kann: ["Probleme lösen", "FAQ", "Anleitungen"],
  },
  {
    id: "email",
    name: "E-Mail-Agent",
    abteilung: "Kundenservice & Kommunikation",
    aufgabe: "Schreibt versandfertige E-Mails und Antworten mit Ihrer Signatur.",
    kann: ["Mails verfassen", "Antworten", "Signatur"],
  },
  {
    id: "crm",
    name: "CRM-Agent",
    abteilung: "Kundenservice & Kommunikation",
    aufgabe: "Pflegt Kontakte, verfolgt Leads und hält die Pipeline aktuell.",
    kann: ["Kontakte pflegen", "Leads verfolgen", "Follow-ups"],
  },
  {
    id: "meeting",
    name: "Meeting-Agent",
    abteilung: "Kundenservice & Kommunikation",
    aufgabe: "Bereitet Sitzungen vor und erstellt Protokolle mit To-dos.",
    kann: ["Agenda", "Protokoll", "To-dos"],
  },
  {
    id: "sprach",
    name: "Sprach-Agent",
    abteilung: "Kundenservice & Kommunikation",
    aufgabe: "Verarbeitet gesprochene Sprache und formuliert klare Texte daraus.",
    kann: ["Diktat verstehen", "Formulieren", "Übersetzen"],
    geplant: true,
  },

  // ---------- Dokumente & Recht ----------
  {
    id: "dokumente",
    name: "Dokumenten-Agent",
    abteilung: "Dokumente & Recht",
    aufgabe: "Liest PDF, Word und Excel, fasst zusammen und erstellt Dokumente.",
    kann: ["PDF lesen", "Zusammenfassen", "Dokumente erstellen"],
  },
  {
    id: "vertrag",
    name: "Vertragsanalyse-Agent",
    abteilung: "Dokumente & Recht",
    aufgabe: "Prüft Verträge auf Risiken, Fristen und unklare Klauseln.",
    kann: ["Verträge prüfen", "Risiken markieren", "Entwürfe"],
  },
  {
    id: "compliance",
    name: "Compliance-Agent",
    abteilung: "Dokumente & Recht",
    aufgabe: "Achtet auf Datenschutz und regulatorische Vorgaben (z. B. DSGVO).",
    kann: ["Datenschutz-Check", "Richtlinien", "Hinweise"],
  },

  // ---------- Finanzen & Personal ----------
  {
    id: "buchhaltung",
    name: "Buchhaltungs-Agent",
    abteilung: "Finanzen & Personal",
    aufgabe: "Erstellt Rechnungen, Auswertungen und Finanzübersichten.",
    kann: ["Rechnungen", "Auswertungen", "Budget"],
  },
  {
    id: "hr",
    name: "HR-Agent",
    abteilung: "Finanzen & Personal",
    aufgabe: "Unterstützt bei Stellenanzeigen, Bewerber-Check und Zeugnissen.",
    kann: ["Stellenanzeigen", "Bewerber-Check", "Zeugnisse"],
  },
  {
    id: "einkauf",
    name: "Einkaufs-Agent",
    abteilung: "Finanzen & Personal",
    aufgabe: "Vergleicht Lieferanten und bereitet Beschaffungs-Entscheide auf.",
    kann: ["Lieferanten vergleichen", "Anfragen", "Bestellungen"],
  },

  // ---------- Medien & Kreation ----------
  {
    id: "bild",
    name: "Bild-Agent",
    abteilung: "Medien & Kreation",
    aufgabe: "Analysiert Bilder und beschreibt Motive für weitere Aufgaben.",
    kann: ["Bilder verstehen", "Beschreiben", "Konzepte"],
    geplant: true,
  },
  {
    id: "video",
    name: "Video-Agent",
    abteilung: "Medien & Kreation",
    aufgabe: "Erstellt Drehbücher, Storyboards und Konzepte für Videos.",
    kann: ["Drehbuch", "Storyboard", "Konzept"],
    geplant: true,
  },

  // ---------- Betrieb & Sicherheit ----------
  {
    id: "sicherheit",
    name: "Sicherheits-Agent",
    abteilung: "Betrieb & Sicherheit",
    aufgabe: "Prüft auf Schwachstellen und schützt Daten und Zugänge (rein defensiv).",
    kann: ["Schwachstellen prüfen", "Härtung", "Warnungen"],
  },
  {
    id: "monitoring",
    name: "Monitoring-Agent",
    abteilung: "Betrieb & Sicherheit",
    aufgabe: "Überwacht Status und Auslastung und meldet Auffälligkeiten.",
    kann: ["Status prüfen", "Auslastung", "Alarme"],
  },
  {
    id: "reporting",
    name: "Reporting-Agent",
    abteilung: "Betrieb & Sicherheit",
    aufgabe: "Erstellt regelmässige Berichte aus den Ergebnissen des Teams.",
    kann: ["Berichte", "Auswertung", "Verteilung"],
  },
];

/** Anzahl benannter Spezialisten im Katalog. */
export const AGENT_ANZAHL = AGENT_ROSTER.length;

/** Agenten einer Abteilung, in Katalog-Reihenfolge. */
export function agentenNach(abteilung: Abteilung): RosterAgent[] {
  return AGENT_ROSTER.filter((a) => a.abteilung === abteilung);
}
