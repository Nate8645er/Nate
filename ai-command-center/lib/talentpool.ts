/**
 * Generativer Talent-Pool: über 1 Milliarde adressierbare
 * Spezialisten-Profile.
 *
 * Ehrliches Prinzip (kein Marketing-Trick): Die Profile existieren als
 * kombinatorischer Adressraum (Rolle x Fachgebiet x Branche x
 * Spezialisierung x Markt x Stufe). Jede Kombination ist über ihren Index
 * deterministisch adressierbar und wird bei Bedarf instanziiert – genau
 * so arbeitet der Commander im Org-Modus, wenn er pro Auftrag die
 * passenden Spezialisten besetzt. Gleichzeitig RECHNENDE Agenten bleiben
 * pro Abo-Stufe gedeckelt (MAX_DYN_AGENTS) – das haelt Missionen schnell,
 * stabil und bezahlbar.
 */

const ROLLEN = [
  "Analyst", "Stratege", "Texter", "Entwickler", "Designer", "Planer",
  "Berater", "Prüfer", "Rechercheur", "Redaktor", "Kalkulator", "Architekt",
  "Koordinator", "Übersetzer", "Controller", "Organisator", "Optimierer",
  "Moderator", "Dokumentar", "Trainer", "Einkäufer", "Verkäufer",
  "Produktmanager", "Projektleiter", "Datenanalyst", "Marktforscher",
  "Kampagnenleiter", "Kundenberater", "Prozessingenieur", "Qualitätsleiter",
  "Businessanalyst", "Finanzplaner", "Personalentwickler", "Einsatzleiter",
  "Konzepter", "Systemplaner", "Tester", "Auditor", "Werbeleiter",
  "Vertriebsplaner", "Contentmanager", "Communitymanager", "Innovationsscout",
  "Risikoanalyst", "Lektor", "Statistiker", "Budgetplaner", "Terminplaner",
  "Angebotsspezialist", "Supportspezialist", "Wissensmanager", "Trendanalyst",
  "Preisstratege", "Markenstratege", "Verhandlungsberater", "Compliance-Prüfer",
  "Ablaufplaner", "Krisenberater", "Wachstumsstratege", "Automatisierer",
] as const;

const FACHGEBIETE = [
  "Marketing", "Vertrieb", "Finanzen", "Personal", "Einkauf", "Logistik",
  "Produktion", "Kundendienst", "Recht", "Steuern", "Buchhaltung",
  "Controlling", "Kommunikation", "Public Relations", "Social Media",
  "Suchmaschinen", "E-Mail-Marketing", "Webentwicklung", "App-Entwicklung",
  "Datenanalyse", "Künstliche Intelligenz", "Automatisierung", "Sicherheit",
  "Datenschutz", "Qualitätsmanagement", "Projektmanagement", "Strategie",
  "Innovation", "Nachhaltigkeit", "Export", "Import", "Preisgestaltung",
  "Verhandlung", "Präsentation", "Dokumentation", "Schulung", "Onboarding",
  "Krisenkommunikation", "Marktforschung", "Produktentwicklung",
  "Kundenbindung", "Beschwerdemanagement", "Prozessoptimierung",
  "Lieferketten", "Immobilien", "Versicherung", "Gesundheitswesen", "Bildung",
] as const;

const BRANCHEN = [
  "Handel", "E-Commerce", "Gastronomie", "Hotellerie", "Handwerk", "Bau",
  "Treuhand", "Banken", "Versicherungen", "Gesundheit", "Pflege", "Bildung",
  "Software", "IT-Dienstleistung", "Agenturen", "Medien", "Industrie",
  "Maschinenbau", "Pharma", "Chemie", "Energie", "Transport", "Logistik",
  "Immobilien", "Landwirtschaft", "Lebensmittel", "Mode", "Sport", "Tourismus",
  "Automobil", "Elektronik", "Telekommunikation", "Recht & Beratung",
  "Non-Profit", "Öffentliche Hand", "Startups",
] as const;

const SPEZIALISIERUNGEN = [
  "Kleinunternehmen", "Mittelstand", "Konzerne", "B2B", "B2C", "D2C",
  "Neukundengewinnung", "Bestandskunden", "Premiumsegment", "Preiseinstieg",
  "Digitalisierung", "Turnaround", "Wachstum", "Kostensenkung",
  "Internationalisierung", "Lokalgeschäft", "Onlinegeschäft", "Filialbetrieb",
  "Saisongeschäft", "Abo-Modelle", "Projektgeschäft", "Servicegeschäft",
  "Produktlancierung", "Rebranding", "Fusionen", "Nachfolge", "Compliance",
  "Ausschreibungen", "Förderanträge", "Investorensuche", "Teamaufbau",
  "Remote-Arbeit", "Schichtbetrieb", "Franchising", "Lizenzgeschäft",
  "Datengetrieben", "Kreativgetrieben", "Qualitätsführerschaft",
  "Geschwindigkeit", "Kundenerlebnis", "Barrierefreiheit", "Mehrsprachigkeit",
  "Krisenfestigkeit", "Regulierte Märkte",
] as const;

const MAERKTE = [
  "Schweiz", "DACH", "Deutschland", "Österreich", "Frankreich", "Italien",
  "Westschweiz", "Tessin", "Europa", "Nordamerika", "Lateinamerika",
  "Naher Osten", "Asien-Pazifik", "Skandinavien", "Benelux", "UK & Irland",
  "Osteuropa", "Iberien", "Global", "Städtisch", "Ländlich", "Grenzregionen",
  "Tourismusregionen", "Wirtschaftszentren", "Emerging Markets",
  "Online-Marktplätze", "Social Commerce", "Fachmärkte", "Nischenmärkte",
  "Wachstumsmärkte",
] as const;

const STUFEN = [
  "Junior", "Professional", "Senior", "Expert", "Lead", "Principal",
  "Direktion", "Partner",
] as const;

const DIMENSIONEN = [ROLLEN, FACHGEBIETE, BRANCHEN, SPEZIALISIERUNGEN, MAERKTE, STUFEN] as const;

/** Gesamtgrösse des adressierbaren Talent-Pools (Produkt aller Dimensionen). */
export const TALENTPOOL_GROESSE = DIMENSIONEN.reduce((p, d) => p * d.length, 1);

export interface TalentProfil {
  index: number;
  titel: string;
  rolle: string;
  fachgebiet: string;
  branche: string;
  spezialisierung: string;
  markt: string;
  stufe: string;
}

/**
 * Instanziiert das Profil mit dem gegebenen Index (0 .. GROESSE-1)
 * deterministisch über eine Mixed-Radix-Zerlegung – dieselbe Nummer
 * ergibt immer denselben Spezialisten.
 */
export function talentProfil(index: number): TalentProfil {
  let rest = ((Math.floor(index) % TALENTPOOL_GROESSE) + TALENTPOOL_GROESSE) % TALENTPOOL_GROESSE;
  const werte: string[] = [];
  for (const dim of DIMENSIONEN) {
    werte.push(dim[rest % dim.length]);
    rest = Math.floor(rest / dim.length);
  }
  const [rolle, fachgebiet, branche, spezialisierung, markt, stufe] = werte;
  return {
    index,
    rolle,
    fachgebiet,
    branche,
    spezialisierung,
    markt,
    stufe,
    titel: `${stufe} ${rolle} für ${fachgebiet}`,
  };
}

/**
 * Streut n gut verteilte Beispiel-Profile über den Pool (deterministisch
 * pro Seed). Der Seed wechselt beim Aufrufer z. B. alle 30 Minuten –
 * so rotiert die sichtbare Auswahl mit jeder Regeneration.
 */
export function talentBeispiele(n: number, seed: number): TalentProfil[] {
  const schritt = 862_664_617; // gross und teilerfremd gewaehlt -> gleichmaessige Streuung
  const profile: TalentProfil[] = [];
  for (let i = 0; i < n; i++) {
    profile.push(talentProfil((seed * 97 + i * schritt) % TALENTPOOL_GROESSE));
  }
  return profile;
}

/** Formatiert die Poolgrösse mit Schweizer Tausendertrennung. */
export function talentpoolFormatiert(): string {
  return TALENTPOOL_GROESSE.toLocaleString("de-CH");
}
