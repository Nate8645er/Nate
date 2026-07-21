/**
 * Skill-Katalog des AI Command Center.
 *
 * Ein Skill ist ein geprüfter Befehl mit strukturierter Auftrags-Vorlage.
 * Die Vorlage wird in der Kommandozentrale eingesetzt (Slash-Befehl) und
 * als Missions-Ziel ausgeführt – strukturierte Aufträge führen zu
 * konstant besseren, vollständigeren Ergebnissen als freie Ein-Zeiler.
 *
 * [Eckige Klammern] sind Platzhalter, die der Nutzer vor dem Ausführen
 * ersetzt. Kein Server-Umbau nötig: die Vorlage IST der Missions-Auftrag.
 */

export interface Skill {
  /** Slash-Befehl, z. B. "/offerte" (eindeutig, klein). */
  befehl: string;
  name: string;
  beschreibung: string;
  kategorie: "Erstellen" | "Marketing" | "Analyse & Kontrolle" | "Planung & Büro" | "Informatik & Code";
  /** Struktur-Vorlage, wird als Missions-Ziel ausgeführt. */
  vorlage: string;
}

export const SKILLS: Skill[] = [
  /* ---------- Erstellen ---------- */
  {
    befehl: "/website",
    name: "Website / Landingpage",
    beschreibung: "Fertige Landingpage als lauffähige HTML-Datei mit Vorschau.",
    kategorie: "Erstellen",
    vorlage:
      "Erstelle eine vollständige, moderne Landingpage für [Angebot/Firma]. " +
      "Zielgruppe: [Zielgruppe]. Inhalte: überzeugende Überschrift, Nutzen-Argumente, " +
      "Preise oder Angebot, Kontakt-Bereich mit Handlungsaufforderung. " +
      "Stil: [modern/edel/verspielt].",
  },
  {
    befehl: "/offerte",
    name: "Offerte / Angebot",
    beschreibung: "Versandfertige Offerte als professionelles Dokument.",
    kategorie: "Erstellen",
    vorlage:
      "Erstelle eine vollständige, versandfertige Offerte als Dokument: " +
      "Leistung [was wird angeboten], Preis [Betrag] CHF, Lieferzeit [Dauer], " +
      "Zahlungsbedingungen [z. B. 50% bei Start], Gültigkeit 30 Tage, " +
      "professioneller Aufbau mit Einleitung und Abschluss.",
  },
  {
    befehl: "/praesentation",
    name: "Präsentation",
    beschreibung: "Fertige Präsentation mit Folien-Struktur zum Durchklicken.",
    kategorie: "Erstellen",
    vorlage:
      "Erstelle eine überzeugende Präsentation zum Thema [Thema] für [Publikum]. " +
      "Etwa [8] Folien: Einstieg, Problem, Lösung, Nutzen, Zahlen, nächste Schritte. " +
      "Kernbotschaft: [Botschaft].",
  },
  {
    befehl: "/dokument",
    name: "Konzept / Bericht",
    beschreibung: "Professionell strukturiertes Dokument zu jedem Thema.",
    kategorie: "Erstellen",
    vorlage:
      "Erstelle ein professionelles Dokument: [Konzept/Bericht/Anleitung] zum Thema " +
      "[Thema]. Zweck: [wofür wird es gebraucht]. Mit klarer Gliederung, " +
      "konkreten Empfehlungen und Zusammenfassung am Anfang.",
  },
  {
    befehl: "/stellenanzeige",
    name: "Stellenanzeige",
    beschreibung: "Ansprechende Stellenanzeige, die passende Bewerber anzieht.",
    kategorie: "Erstellen",
    vorlage:
      "Erstelle eine ansprechende Stellenanzeige für die Position [Position] " +
      "([Pensum]%) in unserer Firma [Firma, Branche, Ort]. Aufgaben: [Hauptaufgaben]. " +
      "Wir bieten: [Vorteile]. Ton: [modern/seriös].",
  },
  /* ---------- Marketing ---------- */
  {
    befehl: "/kampagne",
    name: "Marketing-Kampagne",
    beschreibung: "Komplette Kampagne: Botschaft, Kanäle, Texte, Zeitplan.",
    kategorie: "Marketing",
    vorlage:
      "Erstelle eine komplette Marketing-Kampagne für [Produkt/Angebot]. " +
      "Ziel: [z. B. mehr Anfragen]. Budget: etwa [Betrag] CHF. Zielgruppe: [wer]. " +
      "Mit Kernbotschaft, Kanal-Plan, fertigen Werbetexten und 4-Wochen-Zeitplan.",
  },
  {
    befehl: "/social",
    name: "Social-Media-Woche",
    beschreibung: "Wochenplan mit fertigen Post-Texten für alle Kanäle.",
    kategorie: "Marketing",
    vorlage:
      "Erstelle einen Social-Media-Wochenplan für [Firma/Branche] mit 5 fertigen " +
      "Posts (Text + Bild-Idee + beste Uhrzeit) für [Instagram/TikTok/LinkedIn]. " +
      "Ziel: [Bekanntheit/Verkäufe]. Tonalität: [locker/seriös].",
  },
  {
    befehl: "/werbetext",
    name: "Werbetext",
    beschreibung: "Verkaufsstarke Texte für Anzeige, Flyer oder Website.",
    kategorie: "Marketing",
    vorlage:
      "Schreibe verkaufsstarke Werbetexte für [Produkt/Dienstleistung]: " +
      "3 Varianten (kurz für Anzeige, mittel für Flyer, lang für Website). " +
      "Wichtigster Nutzen: [Nutzen]. Zielgruppe: [wer].",
  },
  {
    befehl: "/newsletter",
    name: "Newsletter",
    beschreibung: "Fertiger Newsletter mit Betreff, Text und Handlungsaufruf.",
    kategorie: "Marketing",
    vorlage:
      "Erstelle einen fertigen Newsletter für [Firma] zum Thema [Anlass/Angebot]. " +
      "Mit 3 Betreff-Varianten, ansprechendem Text und klarem Handlungsaufruf. " +
      "Empfänger: [Kunden/Interessenten].",
  },
  /* ---------- Analyse & Kontrolle ---------- */
  {
    befehl: "/kontrolle",
    name: "Kontrolle / Prüfung",
    beschreibung: "Angebot, Vertrag oder Text auf Schwachstellen prüfen.",
    kategorie: "Analyse & Kontrolle",
    vorlage:
      "Kontrolliere Folgendes gründlich auf Schwachstellen, Risiken und " +
      "Verbesserungsmöglichkeiten und erstelle einen Prüfbericht mit konkreten " +
      "Empfehlungen: [Text/Angebot/Vertrag hier einfügen]",
  },
  {
    befehl: "/markt",
    name: "Marktanalyse",
    beschreibung: "Markt, Konkurrenz und Chancen fundiert eingeordnet.",
    kategorie: "Analyse & Kontrolle",
    vorlage:
      "Erstelle eine Marktanalyse für [Produkt/Branche] in [Region]: Marktgrösse, " +
      "wichtigste Mitbewerber mit Stärken/Schwächen, Zielsegmente, Chancen und " +
      "Risiken, konkrete Empfehlung für unser Vorgehen.",
  },
  {
    befehl: "/preise",
    name: "Preis-Analyse",
    beschreibung: "Preisstruktur durchleuchten und Verbesserungen vorschlagen.",
    kategorie: "Analyse & Kontrolle",
    vorlage:
      "Analysiere unsere Preisstruktur und mache konkrete Verbesserungsvorschläge. " +
      "Unsere Angebote und Preise: [Angebote mit Preisen auflisten]. " +
      "Unsere Kosten grob: [falls bekannt]. Ziel: [mehr Gewinn/mehr Kunden].",
  },
  {
    befehl: "/uebersetzen",
    name: "Übersetzen",
    beschreibung: "Geschäftstexte professionell in andere Sprachen übertragen.",
    kategorie: "Analyse & Kontrolle",
    vorlage:
      "Übersetze den folgenden Geschäftstext professionell nach [Sprache], " +
      "mit passendem Ton für [Kunden/Partner] und einer kurzen Rückübersetzung " +
      "zur Kontrolle: [Text hier einfügen]",
  },
  /* ---------- Planung & Büro ---------- */
  {
    befehl: "/businessplan",
    name: "Businessplan",
    beschreibung: "Vollständiger Businessplan mit Zahlen-Gerüst.",
    kategorie: "Planung & Büro",
    vorlage:
      "Erstelle einen vollständigen Businessplan für [Geschäftsidee]: " +
      "Zusammenfassung, Angebot, Markt, Konkurrenz, Marketing, Organisation, " +
      "Finanzplan-Gerüst für 3 Jahre mit realistischen Annahmen, Risiken, " +
      "nächste Schritte. Startkapital: etwa [Betrag] CHF.",
  },
  {
    befehl: "/prozesse",
    name: "Prozess-Optimierung",
    beschreibung: "Abläufe analysieren und Zeit-/Kostenfresser eliminieren.",
    kategorie: "Planung & Büro",
    vorlage:
      "Analysiere folgenden Ablauf in unserer Firma und erstelle einen " +
      "Optimierungsplan (Zeitfresser, Automatisierungs-Möglichkeiten, neue " +
      "Schritt-für-Schritt-Prozesse): [Ablauf beschreiben, z. B. von Anfrage " +
      "bis Rechnung]",
  },
  {
    befehl: "/prognose",
    name: "Prognose / Vorhersage",
    beschreibung: "Aus Ihren Zahlen eine fundierte Vorhersage mit Szenarien.",
    kategorie: "Analyse & Kontrolle",
    vorlage:
      "Erstelle aus folgenden Zahlen eine Prognose für die nächsten [3/6/12] " +
      "Monate mit drei Szenarien (vorsichtig, realistisch, optimistisch), " +
      "klaren Annahmen und Empfehlungen: [Zahlen einfügen oder Datei anhängen]",
  },
  {
    befehl: "/termine",
    name: "Terminplanung",
    beschreibung: "Wochen-/Projektplan mit Prioritäten und Zeitfenstern.",
    kategorie: "Planung & Büro",
    vorlage:
      "Erstelle einen realistischen [Wochen/Projekt]-Plan: Aufgaben: " +
      "[Aufgaben auflisten]. Fixe Termine: [Termine]. Verfügbare Zeit: " +
      "[Stunden pro Tag]. Mit Prioritäten, Zeitfenstern und Pufferzeiten.",
  },
  {
    befehl: "/support",
    name: "Kundensupport-Paket",
    beschreibung: "FAQ + fertige Antwort-Vorlagen für Ihren Kundendienst.",
    kategorie: "Planung & Büro",
    vorlage:
      "Erstelle ein Kundensupport-Paket für [Firma/Produkt]: die 10 häufigsten " +
      "Kundenfragen mit fertigen Antwort-Vorlagen, eine Eskalations-Richtlinie " +
      "(wann an einen Menschen übergeben) und Textbausteine für Reklamationen.",
  },
  {
    befehl: "/wochenbericht",
    name: "Wochenbericht",
    beschreibung: "Bericht für die Geschäftsleitung, klar und entscheidbar.",
    kategorie: "Planung & Büro",
    vorlage:
      "Erstelle einen professionellen Wochenbericht für die Geschäftsleitung " +
      "aus diesen Stichpunkten (Struktur: Zusammenfassung, Kennzahlen, " +
      "Fortschritte, Probleme mit Lösungsvorschlag, nächste Woche): " +
      "[Stichpunkte der Woche einfügen]",
  },
  {
    befehl: "/rechnung",
    name: "Rechnung erstellen",
    beschreibung: "Professionelle Rechnung mit Positionen, MwSt und Zahlungsfrist.",
    kategorie: "Planung & Büro",
    vorlage:
      "Erstelle eine professionelle, versandfertige Rechnung als Dokument: " +
      "Rechnungssteller: [Ihre Firma, Adresse]. Kunde: [Name, Firma, Adresse]. " +
      "Positionen: [Leistung 1: Betrag CHF; Leistung 2: Betrag CHF]. " +
      "MwSt: [8.1% / keine]. Zahlungsfrist: [30] Tage. Rechnungsnummer: [Nr].",
  },
  {
    befehl: "/mahnung",
    name: "Zahlungserinnerung",
    beschreibung: "Freundliche Erinnerung bis 2. Mahnung – wirksam, ohne Kunden zu verlieren.",
    kategorie: "Planung & Büro",
    vorlage:
      "Erstelle eine [freundliche Zahlungserinnerung / 1. Mahnung / 2. Mahnung] " +
      "für: Kunde [Name], Rechnung [Nr] über [Betrag] CHF, fällig seit [Datum]. " +
      "Ton: bestimmt aber beziehungserhaltend. Mit Betreff, versandfertig.",
  },
  /* ---------- Informatik & Code ---------- */
  {
    befehl: "/code",
    name: "Code schreiben",
    beschreibung: "Lauffähiger Code als echte Datei: Script, Tool oder Webanwendung.",
    kategorie: "Informatik & Code",
    vorlage:
      "Schreibe lauffähigen, sauber kommentierten Code: [was soll das Programm " +
      "tun]. Sprache/Technologie: [z. B. Python, JavaScript, HTML/CSS]. " +
      "Eingaben: [was kommt rein]. Ausgaben: [was soll rauskommen]. " +
      "Liefere den vollständigen Code als Datei plus kurze Anleitung.",
  },
  {
    befehl: "/bugfix",
    name: "Code prüfen / Fehler finden",
    beschreibung: "Code-Review: Fehler, Sicherheitslücken und Verbesserungen.",
    kategorie: "Informatik & Code",
    vorlage:
      "Prüfe folgenden Code gründlich auf Fehler, Sicherheitslücken und " +
      "Verbesserungsmöglichkeiten. Erstelle einen Review-Bericht und die " +
      "korrigierte Version als Datei: [Code hier einfügen oder Datei anhängen]",
  },
  {
    befehl: "/api-doku",
    name: "Technische Dokumentation",
    beschreibung: "README, API-Doku oder Anleitung für Ihr Software-Projekt.",
    kategorie: "Informatik & Code",
    vorlage:
      "Erstelle eine professionelle technische Dokumentation für [Projekt/API]: " +
      "Zweck, Installation, Verwendung mit Beispielen, [API-Endpunkte/Konfiguration], " +
      "häufige Probleme. Zielgruppe: [Entwickler/Endnutzer]. " +
      "Grundlage: [Beschreibung einfügen oder Datei anhängen]",
  },
];

/** Skills nach Kategorie gruppiert (für Katalog-Seite und Palette). */
export const SKILL_KATEGORIEN = [
  "Erstellen",
  "Marketing",
  "Analyse & Kontrolle",
  "Planung & Büro",
  "Informatik & Code",
] as const;

/** Findet Skills, deren Befehl oder Name zur Eingabe passt (für "/"-Palette). */
export function skillSuche(eingabe: string): Skill[] {
  const q = eingabe.trim().toLowerCase();
  if (!q.startsWith("/")) return [];
  const rest = q.slice(1);
  return SKILLS.filter(
    (s) => s.befehl.slice(1).startsWith(rest) || s.name.toLowerCase().includes(rest),
  ).slice(0, 8);
}
