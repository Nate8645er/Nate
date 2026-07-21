/**
 * Connector-Registry für das Integration-Center.
 *
 * Rein statischer Katalog (keine Live-Verbindungen): beschreibt, welche
 * Firmensysteme als Anbindung angefragt werden können, in welcher
 * Plan-Stufe sie verfügbar sind und in welchem Ausbau-Status sie stehen.
 * Live-Anbindungen werden pro Unternehmen als Enterprise-Projekt
 * eingerichtet (siehe ARCHITEKTUR-ENTERPRISE.md, Adapter-Muster).
 *
 * Markenrecht: Es werden bewusst KEINE Fremdlogos verwendet, sondern
 * neutrale Monogramm-Badges (2 Buchstaben) im HUD-Stil mit einer
 * Akzentnuance pro Kategorie.
 */

export type ConnectorKategorie =
  | "Produktivität"
  | "CRM + Vertrieb"
  | "ERP + Finanzen"
  | "Kommunikation"
  | "Cloud + Dateien"
  | "E-Commerce"
  | "Eigene Systeme";

export type ConnectorStatus = "verfügbar-auf-anfrage" | "in-entwicklung";

export type ConnectorPlanStufe = "BUSINESS" | "ENTERPRISE";

export interface Connector {
  /** Stabile Kennung, z. B. "microsoft365". */
  id: string;
  /** Anzeigename des Systems. */
  name: string;
  /** Monogramm-Badge (2 Buchstaben) statt Markenlogo. */
  monogramm: string;
  kategorie: ConnectorKategorie;
  /** Ein Satz: was die KI-Abteilung mit dieser Anbindung kann. */
  beschreibung: string;
  status: ConnectorStatus;
  /** Plan-Stufe, ab der die Anbindung angefragt werden kann. */
  planStufe: ConnectorPlanStufe;
}

/** Anzeige-Reihenfolge der Kategorien plus Akzentnuance je Kategorie. */
export const KATEGORIE_AKZENT: Record<ConnectorKategorie, string> = {
  Produktivität: "#ffb35c",
  "CRM + Vertrieb": "#ff8c2a",
  "ERP + Finanzen": "#ffd257",
  Kommunikation: "#ffc98a",
  "Cloud + Dateien": "#e8a04f",
  "E-Commerce": "#ff9d47",
  "Eigene Systeme": "#f5e0b8",
};

export const KATEGORIEN: readonly ConnectorKategorie[] = [
  "Produktivität",
  "CRM + Vertrieb",
  "ERP + Finanzen",
  "Kommunikation",
  "Cloud + Dateien",
  "E-Commerce",
  "Eigene Systeme",
];

export const STATUS_LABEL: Record<ConnectorStatus, string> = {
  "verfügbar-auf-anfrage": "Verfügbar auf Anfrage",
  "in-entwicklung": "In Entwicklung",
};

export const CONNECTORS: readonly Connector[] = [
  // --- Produktivität ---
  {
    id: "microsoft365",
    name: "Microsoft 365",
    monogramm: "MS",
    kategorie: "Produktivität",
    beschreibung:
      "Die KI liest und entwirft Mails in Outlook, plant Termine und erstellt Word- und Excel-Dokumente direkt in Ihrem Tenant.",
    status: "verfügbar-auf-anfrage",
    planStufe: "BUSINESS",
  },
  {
    id: "google-workspace",
    name: "Google Workspace",
    monogramm: "GW",
    kategorie: "Produktivität",
    beschreibung:
      "Die KI arbeitet mit Gmail, Kalender, Docs und Sheets: Entwürfe schreiben, Termine koordinieren, Tabellen befüllen.",
    status: "verfügbar-auf-anfrage",
    planStufe: "BUSINESS",
  },
  // --- CRM + Vertrieb ---
  {
    id: "salesforce",
    name: "Salesforce",
    monogramm: "SF",
    kategorie: "CRM + Vertrieb",
    beschreibung:
      "Die KI pflegt Leads und Opportunities, fasst Accounts zusammen und bereitet Vertriebsreports aus Ihren CRM-Daten auf.",
    status: "verfügbar-auf-anfrage",
    planStufe: "ENTERPRISE",
  },
  {
    id: "hubspot",
    name: "HubSpot",
    monogramm: "HS",
    kategorie: "CRM + Vertrieb",
    beschreibung:
      "Die KI qualifiziert Kontakte, schreibt Follow-up-Mails und hält Deals und Pipelines in HubSpot aktuell.",
    status: "verfügbar-auf-anfrage",
    planStufe: "BUSINESS",
  },
  // --- ERP + Finanzen ---
  {
    id: "sap",
    name: "SAP",
    monogramm: "SP",
    kategorie: "ERP + Finanzen",
    beschreibung:
      "Die KI liest Stammdaten, Bestellungen und Belege aus Ihrem SAP-System und bereitet sie für Entscheidungen auf.",
    status: "in-entwicklung",
    planStufe: "ENTERPRISE",
  },
  {
    id: "stripe",
    name: "Stripe",
    monogramm: "ST",
    kategorie: "ERP + Finanzen",
    beschreibung:
      "Die KI überwacht Zahlungen und Abos, erkennt Auffälligkeiten und erstellt Umsatz-Auswertungen aus Ihren Stripe-Daten.",
    status: "verfügbar-auf-anfrage",
    planStufe: "BUSINESS",
  },
  // --- Kommunikation ---
  {
    id: "slack",
    name: "Slack",
    monogramm: "SL",
    kategorie: "Kommunikation",
    beschreibung:
      "Die KI fasst Channels zusammen, beantwortet Team-Fragen und liefert Missions-Ergebnisse direkt in Ihren Workspace.",
    status: "verfügbar-auf-anfrage",
    planStufe: "BUSINESS",
  },
  {
    id: "microsoft-teams",
    name: "Microsoft Teams",
    monogramm: "MT",
    kategorie: "Kommunikation",
    beschreibung:
      "Die KI meldet Ergebnisse in Teams-Kanäle, fasst Chats zusammen und erinnert an offene Aufgaben.",
    status: "verfügbar-auf-anfrage",
    planStufe: "BUSINESS",
  },
  // --- Cloud + Dateien ---
  {
    id: "dropbox",
    name: "Dropbox",
    monogramm: "DX",
    kategorie: "Cloud + Dateien",
    beschreibung:
      "Die KI durchsucht Ihre Ablage, fasst Dokumente zusammen und legt erzeugte Dateien strukturiert ab.",
    status: "verfügbar-auf-anfrage",
    planStufe: "BUSINESS",
  },
  {
    id: "onedrive",
    name: "OneDrive",
    monogramm: "OD",
    kategorie: "Cloud + Dateien",
    beschreibung:
      "Die KI liest und schreibt Dateien in OneDrive/SharePoint und hält Team-Ordner automatisch aktuell.",
    status: "verfügbar-auf-anfrage",
    planStufe: "BUSINESS",
  },
  {
    id: "aws",
    name: "AWS",
    monogramm: "AW",
    kategorie: "Cloud + Dateien",
    beschreibung:
      "Die KI liest S3-Daten und Cloud-Metriken, überwacht Kosten und schlägt Optimierungen für Ihre AWS-Umgebung vor.",
    status: "in-entwicklung",
    planStufe: "ENTERPRISE",
  },
  {
    id: "azure",
    name: "Azure",
    monogramm: "AZ",
    kategorie: "Cloud + Dateien",
    beschreibung:
      "Die KI wertet Azure-Ressourcen, Logs und Kosten aus und unterstützt Ihr IT-Team bei Betrieb und Planung.",
    status: "in-entwicklung",
    planStufe: "ENTERPRISE",
  },
  // --- E-Commerce ---
  {
    id: "shopify",
    name: "Shopify",
    monogramm: "SH",
    kategorie: "E-Commerce",
    beschreibung:
      "Die KI pflegt Produkte und Lagerbestände, analysiert Bestellungen und schreibt Produkttexte direkt in Ihren Shop.",
    status: "verfügbar-auf-anfrage",
    planStufe: "BUSINESS",
  },
  {
    id: "woocommerce",
    name: "WooCommerce",
    monogramm: "WC",
    kategorie: "E-Commerce",
    beschreibung:
      "Die KI aktualisiert Produkte und Preise in Ihrem WooCommerce-Shop und wertet Bestell- und Kundendaten aus.",
    status: "in-entwicklung",
    planStufe: "BUSINESS",
  },
  // --- Eigene Systeme ---
  {
    id: "custom-rest",
    name: "Eigene REST-API/Webhooks",
    monogramm: "RW",
    kategorie: "Eigene Systeme",
    beschreibung:
      "Die KI wird per REST-API und Webhooks an Ihre eigene Firmensoftware angebunden und kann dort lesen und schreiben.",
    status: "verfügbar-auf-anfrage",
    planStufe: "ENTERPRISE",
  },
];

/** Connectors einer Kategorie in Katalog-Reihenfolge. */
export function connectorsByKategorie(kategorie: ConnectorKategorie): Connector[] {
  return CONNECTORS.filter((c) => c.kategorie === kategorie);
}
