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
  kategorie:
    | "Erstellen"
    | "Marketing"
    | "Verkauf & Kunden"
    | "Analyse & Kontrolle"
    | "Finanzen"
    | "Personal & Recht"
    | "Planung & Büro"
    | "Informatik & Code"
    | "Branchen-Pakete"
    | "Automatisierung & Integration"
    | "Kundenservice"
    | "Daten & KI";
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
    befehl: "/whatsapp",
    name: "WhatsApp-Nachrichten",
    beschreibung: "Versandfertige WhatsApp-Antworten für Kunden – kurz, persönlich, professionell.",
    kategorie: "Marketing",
    vorlage:
      "Erstelle versandfertige WhatsApp-Nachrichten für [Firma]: Anlass " +
      "[Kundenanfrage beantworten / Terminbestätigung / Angebot nachfassen / " +
      "Status-Update]. Kunde: [Name]. Kontext: [worum geht es]. " +
      "3 Varianten: kurz (2 Sätze), mittel, mit Emoji – jeweils per Du und per Sie. " +
      "Ton: freundlich, professionell, sofort kopierbar.",
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
  /* ---------- Verkauf & Kunden ---------- */
  {
    befehl: "/verkaufsskript",
    name: "Verkaufsgespräch",
    beschreibung: "Gesprächsleitfaden mit Einwand-Antworten für Ihr Angebot.",
    kategorie: "Verkauf & Kunden",
    vorlage:
      "Erstelle einen Verkaufs-Gesprächsleitfaden für [Produkt/Dienstleistung]: " +
      "Gesprächseinstieg, 5 Nutzen-Argumente, die 6 häufigsten Einwände mit " +
      "überzeugenden Antworten, Preisnennung und Abschlussfragen. " +
      "Zielkunde: [wer]. Ton: [beratend/direkt].",
  },
  {
    befehl: "/nachfassen",
    name: "Nachfassen / Follow-up",
    beschreibung: "Versandfertige Nachfass-Nachrichten, die Abschlüsse holen.",
    kategorie: "Verkauf & Kunden",
    vorlage:
      "Erstelle 3 versandfertige Nachfass-Nachrichten (E-Mail + WhatsApp + " +
      "Telefon-Leitfaden) für: [Offerte/Angebot] an [Kunde], gesendet am " +
      "[Datum], bisher keine Antwort. Ton: freundlich, wertstiftend, " +
      "ohne Druck – mit klarem nächsten Schritt.",
  },
  {
    befehl: "/kundenumfrage",
    name: "Kundenumfrage",
    beschreibung: "Fertige Zufriedenheits-Umfrage mit Auswertungsraster.",
    kategorie: "Verkauf & Kunden",
    vorlage:
      "Erstelle eine Kundenumfrage für [Firma/Produkt]: 8-10 präzise Fragen " +
      "(Zufriedenheit, Weiterempfehlung, Verbesserungen), Einladungstext für " +
      "E-Mail/WhatsApp und ein Auswertungsraster mit Handlungsempfehlungen.",
  },
  {
    befehl: "/reklamation",
    name: "Reklamations-Antwort",
    beschreibung: "Souveräne Antwort, die den Kunden hält statt verliert.",
    kategorie: "Verkauf & Kunden",
    vorlage:
      "Schreibe eine professionelle Antwort auf folgende Reklamation: " +
      "[Reklamation einfügen]. Mit ehrlicher Anerkennung, konkreter Lösung " +
      "[was wir anbieten], Wiedergutmachung falls angebracht und " +
      "versöhnlichem Abschluss. Versandfertig mit Betreff.",
  },
  /* ---------- Finanzen ---------- */
  {
    befehl: "/budget",
    name: "Budget-Plan",
    beschreibung: "Jahresbudget mit Monatsaufteilung und Reserven.",
    kategorie: "Finanzen",
    vorlage:
      "Erstelle ein Jahresbudget für [Firma/Abteilung/Projekt]: erwartete " +
      "Einnahmen [Betrag/Quellen], Fixkosten [auflisten], variable Kosten " +
      "[auflisten]. Mit Monatsaufteilung, Reserve-Empfehlung, " +
      "Kennzahlen und Warnsignalen, ab wann gehandelt werden muss.",
  },
  {
    befehl: "/liquiditaet",
    name: "Liquiditätsplan",
    beschreibung: "13-Wochen-Vorschau: Kommt genug Geld rein?",
    kategorie: "Finanzen",
    vorlage:
      "Erstelle einen 13-Wochen-Liquiditätsplan: Kontostand heute [Betrag], " +
      "erwartete Zahlungseingänge [Rechnungen mit Fälligkeit], fixe Ausgaben " +
      "[Miete/Löhne/etc. mit Terminen]. Zeige Engpässe, Puffer und 3 konkrete " +
      "Massnahmen zur Verbesserung.",
  },
  {
    befehl: "/kalkulation",
    name: "Preis-Kalkulation",
    beschreibung: "Stundensatz oder Produktpreis sauber durchgerechnet.",
    kategorie: "Finanzen",
    vorlage:
      "Kalkuliere [Stundensatz/Produktpreis] für [Leistung/Produkt]: " +
      "Kosten [Material/Einkauf/Lohn], Gemeinkosten [Miete/Versicherung/etc.], " +
      "gewünschte Marge [%]. Zeige die Rechnung transparent, vergleiche mit " +
      "marktüblichen Preisen und empfiehl einen Verkaufspreis.",
  },
  /* ---------- Personal & Recht ---------- */
  {
    befehl: "/bewerber-check",
    name: "Bewerber-Analyse",
    beschreibung: "Lebenslauf strukturiert prüfen + Interviewfragen.",
    kategorie: "Personal & Recht",
    vorlage:
      "Analysiere folgende Bewerbung für die Stelle [Position]: Stärken, " +
      "Lücken, offene Fragen, Passung zu unseren Anforderungen [Anforderungen]. " +
      "Erstelle 10 gezielte Interviewfragen. Bewerbung: " +
      "[Lebenslauf einfügen oder Datei anhängen]",
  },
  {
    befehl: "/arbeitszeugnis",
    name: "Arbeitszeugnis",
    beschreibung: "Wohlwollend-korrektes Zeugnis nach Schweizer Praxis.",
    kategorie: "Personal & Recht",
    vorlage:
      "Erstelle ein vollständiges Arbeitszeugnis nach Schweizer Praxis: " +
      "Mitarbeiter [Name], Position [Funktion], Zeitraum [von-bis], " +
      "Aufgaben [Hauptaufgaben], Leistung [sehr gut/gut/genügend], " +
      "Austrittsgrund [Grund]. Wohlwollend, wahr und codefrei formuliert.",
  },
  {
    befehl: "/mitarbeitergespraech",
    name: "Mitarbeitergespräch",
    beschreibung: "Leitfaden für Jahres-, Feedback- oder Konfliktgespräch.",
    kategorie: "Personal & Recht",
    vorlage:
      "Erstelle einen Gesprächsleitfaden für ein [Jahresgespräch/Feedback-" +
      "gespräch/Konfliktgespräch] mit [Mitarbeiter, Funktion]. Anlass/Themen: " +
      "[was ansprechen]. Mit Gesprächsaufbau, konkreten Formulierungen, " +
      "Zielvereinbarungs-Vorlage und Notizblatt.",
  },
  {
    befehl: "/onboarding",
    name: "Einarbeitungsplan",
    beschreibung: "30-60-90-Tage-Plan für neue Mitarbeitende.",
    kategorie: "Personal & Recht",
    vorlage:
      "Erstelle einen Einarbeitungsplan (erste Woche + 30/60/90 Tage) für " +
      "[Position] in unserer Firma [Firma, Branche]. Aufgabenbereich: " +
      "[Hauptaufgaben]. Mit Checkliste vor Arbeitsbeginn, Lernzielen, " +
      "Verantwortlichkeiten und Meilenstein-Gesprächen.",
  },
  {
    befehl: "/vertrag",
    name: "Vertragsentwurf",
    beschreibung: "Sauberer Vertragsentwurf zum Prüfen durch Ihren Anwalt.",
    kategorie: "Personal & Recht",
    vorlage:
      "Erstelle einen Vertragsentwurf: [Dienstleistungsvertrag/Werkvertrag/" +
      "Mietvertrag/NDA] zwischen [Partei A] und [Partei B]. Gegenstand: " +
      "[was geregelt wird]. Eckpunkte: [Preis, Dauer, Kündigung, besondere " +
      "Punkte]. Klar gegliedert, Schweizer Recht, mit Hinweis welche Klauseln " +
      "anwaltlich geprüft werden sollten.",
  },
  {
    befehl: "/datenschutz",
    name: "Datenschutz-Check",
    beschreibung: "DSG/DSGVO-Basisprüfung mit konkreter Massnahmenliste.",
    kategorie: "Personal & Recht",
    vorlage:
      "Prüfe unsere Situation auf Datenschutz (Schweizer DSG + DSGVO wo " +
      "relevant): Wir sind [Firma, Branche] und bearbeiten folgende Daten: " +
      "[welche Kundendaten/Tools/Newsletter/Website]. Erstelle eine " +
      "priorisierte Massnahmenliste und eine einfache Datenschutzerklärung " +
      "als Entwurf.",
  },
  /* ---------- Planung & Büro (Ergänzung) ---------- */
  {
    befehl: "/sitzungsprotokoll",
    name: "Sitzungsprotokoll",
    beschreibung: "Aus Stichworten ein sauberes Protokoll mit Aufgabenliste.",
    kategorie: "Planung & Büro",
    vorlage:
      "Erstelle aus folgenden Sitzungsnotizen ein professionelles Protokoll: " +
      "Teilnehmende, besprochene Punkte, Entscheidungen, Aufgabenliste " +
      "(wer/was/bis wann), offene Punkte für die nächste Sitzung. " +
      "Notizen: [Stichworte einfügen oder Datei anhängen]",
  },
  {
    befehl: "/geschaeftsbrief",
    name: "Geschäftsbrief",
    beschreibung: "Formeller Brief – von Kündigung bis Behördenschreiben.",
    kategorie: "Planung & Büro",
    vorlage:
      "Schreibe einen formellen Geschäftsbrief: Anlass [Kündigung Vertrag/" +
      "Anfrage/Einsprache/Behördenschreiben], Empfänger [wer], unser Anliegen: " +
      "[was erreicht werden soll]. Korrekt aufgebaut mit Betreff, sachlichem " +
      "Ton und klarer Forderung/Frist, versandfertig.",
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

  {
    befehl: "/jahresplanung",
    name: "Jahresplanung",
    beschreibung: "Das ganze Firmenjahr strukturiert: Ziele, Quartale, Meilensteine.",
    kategorie: "Planung & Büro",
    vorlage:
      "Erstelle eine Jahresplanung für [Firma/Bereich] für das Jahr [Jahr]: " +
      "Hauptziele [Ziele auflisten], wichtige Termine [Messen/Saison/etc.]. " +
      "Mit Quartals-Meilensteinen, Verantwortlichkeiten, Budget-Eckpunkten " +
      "und einem Prüfrhythmus (was schauen wir monatlich an).",
  },
  {
    befehl: "/schulung",
    name: "Schulungsunterlagen",
    beschreibung: "Fertige Schulung für Ihr Team: Ablauf, Inhalte, Übungen, Handout.",
    kategorie: "Personal & Recht",
    vorlage:
      "Erstelle komplette Schulungsunterlagen zum Thema [Thema] für " +
      "[Zielgruppe, z. B. neue Mitarbeitende/Verkaufsteam]: Lernziele, " +
      "Ablaufplan für [Dauer], verständliche Inhalte mit Beispielen aus " +
      "[Branche], 3 Übungen mit Lösungen und ein einseitiges Handout.",
  },
  {
    befehl: "/lieferanten-vergleich",
    name: "Lieferanten-Vergleich",
    beschreibung: "Angebote strukturiert vergleichen und sauber verhandeln.",
    kategorie: "Finanzen",
    vorlage:
      "Vergleiche folgende Lieferanten-Angebote strukturiert: " +
      "[Angebote mit Preisen/Konditionen einfügen oder Dateien anhängen]. " +
      "Mit Vergleichstabelle (Preis, Qualität, Lieferzeit, Risiken), " +
      "Empfehlung, Verhandlungspunkten je Anbieter und einem " +
      "versandfertigen Nachverhandlungs-Text.",
  },
  {
    befehl: "/krisenplan",
    name: "Krisen- / Notfallplan",
    beschreibung: "Vorbereitet, wenn es brennt: Szenarien, Abläufe, Kommunikation.",
    kategorie: "Planung & Büro",
    vorlage:
      "Erstelle einen Krisen- und Notfallplan für [Firma, Branche]: die 5 " +
      "wahrscheinlichsten Szenarien [z. B. IT-Ausfall, Schlüsselperson fällt " +
      "aus, Lieferengpass, Reklamationswelle], je Szenario Sofortmassnahmen, " +
      "Verantwortliche, Kommunikationsvorlagen für Kunden und Team sowie " +
      "eine Prüf-Checkliste fürs Jahr.",
  },
  /* ---------- Exklusiv ab BUSINESS ---------- */
  {
    befehl: "/prozess-automatisierung",
    name: "Automatisierungs-Fahrplan",
    beschreibung: "Welche Abläufe Ihrer Firma sich automatisieren lassen – mit Plan.",
    kategorie: "Planung & Büro",
    vorlage:
      "Analysiere unsere Firma und erstelle einen Automatisierungs-Fahrplan: " +
      "Branche [Branche], Team [Anzahl Personen], heutige Abläufe: " +
      "[wichtigste Abläufe beschreiben]. Liefere: Automatisierungs-Potenzial " +
      "je Ablauf, Aufwand/Nutzen-Matrix, konkrete Umsetzungs-Reihenfolge für " +
      "12 Monate und geschätzte Zeitersparnis pro Woche.",
  },
  {
    befehl: "/abteilungs-bericht",
    name: "Abteilungs-Bericht",
    beschreibung: "Konsolidierter Bericht über mehrere Teams/Standorte.",
    kategorie: "Planung & Büro",
    vorlage:
      "Erstelle einen konsolidierten Führungs-Bericht über unsere Abteilungen: " +
      "[Zahlen/Stichpunkte je Abteilung oder Datei anhängen]. Mit Gesamtbild, " +
      "Vergleich der Abteilungen, Auffälligkeiten, Risiken und konkreten " +
      "Führungs-Entscheidungen, die jetzt anstehen.",
  },
  /* ---------- Exklusiv ab ENTERPRISE ---------- */
  {
    befehl: "/ki-strategie",
    name: "KI-Strategie",
    beschreibung: "Firmenweite KI-Roadmap: wo KI Ihnen Vorsprung verschafft.",
    kategorie: "Analyse & Kontrolle",
    vorlage:
      "Erstelle eine firmenweite KI-Strategie für [Firma, Branche, Grösse]: " +
      "heutige Situation [was ist digital/manuell], Wettbewerb, die 5 " +
      "wirkungsvollsten KI-Einsatzfelder mit Business-Case, Risiken und " +
      "Datenschutz, Roadmap über 24 Monate mit Meilensteinen und Budget-Rahmen.",
  },
  {
    befehl: "/integrations-plan",
    name: "System-Integrations-Plan",
    beschreibung: "Anbindung Ihrer Systeme (ERP/CRM/Maschinen) sauber geplant.",
    kategorie: "Informatik & Code",
    vorlage:
      "Erstelle einen Integrations-Plan für unsere Systemlandschaft: " +
      "vorhandene Systeme [ERP/CRM/Buchhaltung/Maschinen/etc. auflisten], " +
      "Ziel: [was soll automatisch fliessen]. Mit Architektur-Skizze in Text, " +
      "Schnittstellen je System, Reihenfolge der Anbindung, Aufwandsschätzung " +
      "und Risiken/Abhängigkeiten.",
  },

  /* ================================================================ */
  /* BRANCHEN-PAKETE – ein KI-System für JEDE Branche.                 */
  /* Jeder Befehl liefert ein branchentypisches, fertiges Ergebnis.   */
  /* ================================================================ */
  {
    befehl: "/handwerk",
    name: "Handwerk-Paket",
    beschreibung: "Offerte, Aufmass-Notiz und Arbeitsrapport für Handwerksbetriebe.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle als Handwerksbetrieb [Gewerk] für [Kunde] ein [Dokument: Offerte/Rapport/Rechnung] " +
      "zu folgendem Auftrag: [Arbeit beschreiben]. Material: [Liste], Arbeitszeit: [Stunden], " +
      "Stundensatz: [CHF]. Struktur mit Positionen, Mengen, Einzel- und Gesamtpreis, MwSt, " +
      "Zahlungs- und Gewährleistungshinweis.",
  },
  {
    befehl: "/gastronomie",
    name: "Gastro-Paket",
    beschreibung: "Menükarte, Tagesaktion und Antwort auf Gäste-Bewertungen.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle für [Restaurant/Café, Küchenstil] eine [Menükarte/Wochenaktion/Event-Menü]: " +
      "[Anzahl] Gerichte mit appetitlichen Beschreibungen, Preisen, Allergen-Hinweisen und " +
      "passenden Getränke-Empfehlungen. Zielgruppe: [z. B. Business-Lunch, Familien].",
  },
  {
    befehl: "/immobilien",
    name: "Immobilien-Exposé",
    beschreibung: "Verkaufs-/Vermietungs-Exposé mit Highlights und Beschreibung.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle ein verkaufsstarkes Exposé für [Objekttyp] in [Ort]: [Fläche] m², [Zimmer] Zimmer, " +
      "Baujahr [Jahr], Preis [CHF]. Ausstattung: [Liste]. Mit Titel, emotionalem Einstieg, " +
      "Ausstattungs-Highlights, Lagebeschreibung, Eckdaten-Tabelle und Kontakt-Call-to-Action.",
  },
  {
    befehl: "/gesundheit",
    name: "Praxis / Gesundheit",
    beschreibung: "Patienteninfo, Anamnesebogen und Aufklärungsschreiben.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle für eine [Arzt-/Zahnarzt-/Therapie]-Praxis ein [Patienten-Infoblatt/Anamnesebogen/" +
      "Aufklärung] zum Thema [Behandlung/Anliegen]. Verständliche Sprache, klare Abschnitte, " +
      "wichtige Hinweise hervorgehoben, Datenschutz-Zeile. Kein medizinischer Ersatz für Beratung.",
  },
  {
    befehl: "/handel",
    name: "Detailhandel",
    beschreibung: "Produkttexte, Aktions-Konzept und Sortiments-Vorschlag.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle für [Geschäft/Shop, Sortiment] [Produkttexte/Aktions-Konzept]: für die Produkte " +
      "[Liste] je Titel, Nutzen-Beschreibung, 3 Bullet-Vorteile und Verkaufsargument. Optional " +
      "Aktion mit Mechanik, Zeitraum und Bewerbungs-Idee.",
  },
  {
    befehl: "/beratung",
    name: "Beratung / Coaching",
    beschreibung: "Angebot und Programm-Konzept für Berater und Coaches.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle für [Beratung/Coaching-Thema] ein [Angebot/Programm-Konzept] für [Zielkunde]: " +
      "Ausgangslage, Ziel, Vorgehen in Phasen, Ergebnisse/Deliverables, Dauer, Investition und " +
      "nächster Schritt. Überzeugend, konkret, ohne Floskeln.",
  },
  {
    befehl: "/bildung",
    name: "Bildung / Kurse",
    beschreibung: "Kursplan, Lernmodul und Kursbeschreibung.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle für [Kurs/Thema] und [Zielgruppe] einen [Kursplan/Lernmodul]: Lernziele, " +
      "Gliederung in Einheiten mit Dauer, Methoden, Übungen und Erfolgskontrolle. Niveau: [Anfänger/…].",
  },
  {
    befehl: "/logistik",
    name: "Logistik / Transport",
    beschreibung: "Tourenplan, Lieferschein-Text und Transport-Angebot.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle für [Transport/Logistik-Anliegen] einen [Tourenplan/Transport-Offerte]: Stationen " +
      "[Liste], Mengen/Gewicht [Angabe], Zeitfenster, sinnvolle Reihenfolge, geschätzte Dauer und " +
      "Kosten-Aufstellung. Hinweise zu Gefahrgut/Kühlung falls relevant.",
  },
  {
    befehl: "/bau",
    name: "Bau / Planung",
    beschreibung: "Leistungsverzeichnis und Bauzeitenplan.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle für [Bauvorhaben] ein [Leistungsverzeichnis/Bauzeitenplan]: Gewerke/Positionen mit " +
      "Mengen und Einheiten, sinnvolle Reihenfolge, Abhängigkeiten und grobe Zeitschätzung je Phase. " +
      "Praxisnah für [Neubau/Umbau/Renovation].",
  },
  {
    befehl: "/treuhand",
    name: "Treuhand / Finanzdienst",
    beschreibung: "Mandantenbericht, Fristen-Übersicht und Beratungsschreiben.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle für [Mandant, Rechtsform] ein [Mandantenbericht/Schreiben] zu [Thema: MwSt, " +
      "Jahresabschluss, Lohn]. Sachlich, mit klaren Handlungsempfehlungen, Fristen und benötigten " +
      "Unterlagen. Schweizer Kontext, keine verbindliche Rechts-/Steuerauskunft.",
  },
  {
    befehl: "/verein",
    name: "Verein / Nonprofit",
    beschreibung: "Protokoll, Mitgliederbrief und Förderantrag.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle für [Verein/Organisation] ein [Sitzungsprotokoll/Mitgliederbrief/Förderantrag] zu " +
      "[Anlass/Projekt]. Vereinsgerechte Sprache, klare Struktur, bei Förderantrag: Ziel, Wirkung, " +
      "Budget und Zeitplan.",
  },
  {
    befehl: "/event",
    name: "Event / Anlass",
    beschreibung: "Event-Konzept mit Ablaufplan und Checkliste.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle ein Konzept für [Event-Art] mit [Gästezahl] Personen, Budget [CHF], Ort [Angabe]: " +
      "Motto, Ablaufplan mit Uhrzeiten, Aufgaben-/Verantwortungsliste, Budget-Aufstellung und " +
      "To-do-Checkliste bis zum Tag X.",
  },
  {
    befehl: "/fitness",
    name: "Fitness / Wellness",
    beschreibung: "Trainings-/Behandlungsplan und Angebots-Paket.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle für [Studio/Praxis] und [Kunde: Ziel, Niveau] einen [Trainings-/Behandlungsplan] über " +
      "[Zeitraum]: Wochenstruktur, Einheiten mit Übungen/Dauer, Progression und Hinweise. Kein " +
      "medizinischer Ersatz.",
  },
  {
    befehl: "/werkstatt",
    name: "Auto / Werkstatt",
    beschreibung: "Kostenvoranschlag und Servicebericht für Werkstätten.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle für [Fahrzeug, Kennzeichen] einen [Kostenvoranschlag/Servicebericht]: durchgeführte/" +
      "nötige Arbeiten [Liste], Ersatzteile mit Preisen, Arbeitszeit und Stundensatz, Gesamt inkl. MwSt " +
      "und Empfehlung für nächsten Service.",
  },
  {
    befehl: "/produktion",
    name: "Produktion / Industrie",
    beschreibung: "Arbeitsanweisung, Prüfplan und Wartungsplan.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle für [Produkt/Anlage/Prozess] eine [Arbeitsanweisung/Prüfplan/Wartungsplan]: Zweck, " +
      "benötigte Mittel, Schritte in Reihenfolge, Sicherheits- und Qualitäts-Prüfpunkte, Intervalle " +
      "und Verantwortliche.",
  },
  {
    befehl: "/reise",
    name: "Reise / Tourismus",
    beschreibung: "Reiseangebot und Tagesprogramm.",
    kategorie: "Branchen-Pakete",
    vorlage:
      "Erstelle für [Reiseziel] und [Reisende: Anzahl, Tage, Budget] ein [Reiseangebot/Programm]: " +
      "Highlights, Tag-für-Tag-Ablauf, Unterkunfts- und Transport-Vorschläge, Preisrahmen und " +
      "Buchungs-Call-to-Action.",
  },

  /* ================================================================ */
  /* AUTOMATISIERUNG & INTEGRATION – Abläufe verbinden & automatisieren */
  /* ================================================================ */
  {
    befehl: "/automatisierung",
    name: "Automatisierungs-Fahrplan",
    beschreibung: "Findet automatisierbare Abläufe und liefert einen konkreten Plan.",
    kategorie: "Automatisierung & Integration",
    vorlage:
      "Analysiere den Ablauf [Prozess beschreiben, z. B. Angebot → Auftrag → Rechnung] in [Firma/" +
      "Branche] und erstelle einen Automatisierungs-Fahrplan: aktuelle Schritte, Zeitfresser, was sich " +
      "wie automatisieren lässt (Auslöser → Aktion), benötigte Werkzeuge, Aufwand/Nutzen und " +
      "Reihenfolge der Umsetzung.",
  },
  {
    befehl: "/integration",
    name: "Integrations-Konzept",
    beschreibung: "Konzept, um System A mit System B zu verbinden.",
    kategorie: "Automatisierung & Integration",
    vorlage:
      "Erstelle ein Integrations-Konzept, um [System A] mit [System B] zu verbinden: welche Daten in " +
      "welche Richtung fliessen, Auslöser, Zuordnung der Felder, Fehlerfälle/Fallbacks, Sicherheits- " +
      "und Datenschutz-Hinweise und ein schrittweiser Umsetzungsplan.",
  },
  {
    befehl: "/workflow",
    name: "Workflow-Design",
    beschreibung: "Entwirft einen sauberen End-to-End-Ablauf mit Zuständigkeiten.",
    kategorie: "Automatisierung & Integration",
    vorlage:
      "Entwirf einen End-to-End-Workflow für [Ziel/Prozess]: Auslöser, Schritte mit Verantwortlichen, " +
      "Entscheidungspunkte, automatische vs. manuelle Schritte, Benachrichtigungen und Messpunkte (KPIs).",
  },
  {
    befehl: "/datenimport",
    name: "Datenimport / Migration",
    beschreibung: "Plan für sauberen Import/Umzug von Daten.",
    kategorie: "Automatisierung & Integration",
    vorlage:
      "Erstelle einen Plan, um [Daten: z. B. Kundenliste, Produkte] aus [Quelle] nach [Ziel] zu " +
      "übernehmen: Feld-Zuordnung, Bereinigungs-Regeln, Dubletten-Handling, Testlauf, Roll-back und " +
      "Prüf-Checkliste nach dem Import.",
  },
  {
    befehl: "/api-anbindung",
    name: "API-Anbindung",
    beschreibung: "Spezifiziert eine Anbindung an eine eigene/fremde API.",
    kategorie: "Automatisierung & Integration",
    vorlage:
      "Spezifiziere die Anbindung an die API von [System]: Anwendungsfälle, benötigte Endpunkte, " +
      "Authentifizierung, Datenmodell, Rate-Limits, Fehlerbehandlung und ein minimaler Beispiel-Ablauf. " +
      "Sicherheitshinweise inklusive.",
  },
  {
    befehl: "/report-automatik",
    name: "Automatischer Report",
    beschreibung: "Konzept für wiederkehrende Berichte/KPIs auf Knopfdruck.",
    kategorie: "Automatisierung & Integration",
    vorlage:
      "Konzipiere einen automatischen [täglichen/wöchentlichen/monatlichen] Report für [Zweck/" +
      "Empfänger]: welche Kennzahlen aus welcher Quelle, Aufbereitung, Format, Verteilweg und ein " +
      "Vorschlag für Schwellen-Warnungen.",
  },

  /* ================================================================ */
  /* KUNDENSERVICE – schneller, konsistenter Support.                 */
  /* ================================================================ */
  {
    befehl: "/faq",
    name: "FAQ-Set",
    beschreibung: "Erstellt ein vollständiges FAQ zu Produkt/Dienstleistung.",
    kategorie: "Kundenservice",
    vorlage:
      "Erstelle ein FAQ-Set für [Produkt/Dienstleistung]: die [Anzahl] häufigsten Kundenfragen mit " +
      "klaren, freundlichen Antworten. Gruppiere nach Themen (Kauf, Nutzung, Zahlung, Support).",
  },
  {
    befehl: "/support-bausteine",
    name: "Support-Textbausteine",
    beschreibung: "Wiederverwendbare Antworten für häufige Support-Fälle.",
    kategorie: "Kundenservice",
    vorlage:
      "Erstelle Textbausteine für den Support von [Firma] zu den Fällen: [Liste, z. B. Lieferverzug, " +
      "Rückgabe, technisches Problem]. Je Baustein freundliche, lösungsorientierte Antwort im Ton [Ton], " +
      "mit Platzhaltern für Namen/Details.",
  },
  {
    befehl: "/bewertung-antwort",
    name: "Bewertungs-Antwort",
    beschreibung: "Professionelle Antwort auf Online-Bewertungen (positiv/negativ).",
    kategorie: "Kundenservice",
    vorlage:
      "Formuliere eine Antwort auf diese Online-Bewertung: «[Bewertung einfügen]». Ton: professionell, " +
      "wertschätzend, deeskalierend; bei Kritik: Verständnis + Lösung/Angebot, ohne Schuldeingeständnis. " +
      "Im Namen von [Firma].",
  },
  {
    befehl: "/rueckgewinnung",
    name: "Kunden-Rückgewinnung",
    beschreibung: "Antwort auf Kündigung mit Rückgewinnungs-Angebot.",
    kategorie: "Kundenservice",
    vorlage:
      "Ein Kunde hat gekündigt: «[Kündigung/Grund]». Formuliere eine wertschätzende Antwort mit einem " +
      "passenden Rückgewinnungs-Angebot [Angebot], ohne aufdringlich zu sein, und einer einfachen " +
      "Möglichkeit, zu bleiben.",
  },

  /* ================================================================ */
  /* DATEN & KI – Zahlen zu Entscheidungen machen.                    */
  /* ================================================================ */
  {
    befehl: "/datenanalyse",
    name: "Datenanalyse",
    beschreibung: "Wertet angehängte Tabellen/Zahlen aus und findet Erkenntnisse.",
    kategorie: "Daten & KI",
    vorlage:
      "Analysiere die angehängten/eingefügten Daten [Tabelle/Zahlen] mit Fokus auf [Frage/Ziel]: " +
      "wichtigste Kennzahlen, Auffälligkeiten, Trends, Top/Flop, und 3 konkrete Handlungs-Empfehlungen. " +
      "Ergebnis als klare Zusammenfassung mit Zahlen.",
  },
  {
    befehl: "/kpi-set",
    name: "KPI-Set & Dashboard",
    beschreibung: "Definiert die richtigen Kennzahlen und ein Dashboard-Konzept.",
    kategorie: "Daten & KI",
    vorlage:
      "Definiere für [Firma/Bereich] und Ziel [Ziel] ein KPI-Set: 6–10 aussagekräftige Kennzahlen mit " +
      "Definition, Datenquelle, Zielwert und Häufigkeit, plus ein Dashboard-Layout-Vorschlag (welche " +
      "Kennzahl wo).",
  },
  {
    befehl: "/ab-test",
    name: "A/B-Test-Plan",
    beschreibung: "Sauberer Testplan für Website, Mail oder Angebot.",
    kategorie: "Daten & KI",
    vorlage:
      "Erstelle einen A/B-Test-Plan für [Element: Betreff/Landingpage/Preis]: Hypothese, Varianten A/B, " +
      "zu messende Metrik, benötigte Stichprobe/Dauer, Erfolgs-Kriterium und Auswertungs-Vorgehen.",
  },
  {
    befehl: "/wettbewerbsanalyse",
    name: "Wettbewerbs- & SWOT-Analyse",
    beschreibung: "Vergleicht mit Mitbewerbern und liefert SWOT + Strategie.",
    kategorie: "Daten & KI",
    vorlage:
      "Erstelle eine Wettbewerbs-Analyse für [Firma/Angebot] gegenüber [Mitbewerber/Liste]: Vergleich " +
      "nach [Kriterien], SWOT (Stärken/Schwächen/Chancen/Risiken) und 3 strategische Empfehlungen zur " +
      "Differenzierung.",
  },
  {
    befehl: "/markteintritt",
    name: "Markteintritt / Expansion",
    beschreibung: "Plan für neuen Markt, neues Land oder neue Zielgruppe.",
    kategorie: "Daten & KI",
    vorlage:
      "Erstelle einen Markteintritts-Plan für [Angebot] in [Markt/Land/Zielgruppe]: Marktbild, " +
      "Chancen/Risiken, rechtliche/kulturelle Besonderheiten, Positionierung, Preisrahmen, Kanäle und " +
      "einen Fahrplan für die ersten 90 Tage.",
  },
];

/** Skills nach Kategorie gruppiert (für Katalog-Seite und Palette). */
export const SKILL_KATEGORIEN = [
  "Erstellen",
  "Marketing",
  "Verkauf & Kunden",
  "Analyse & Kontrolle",
  "Finanzen",
  "Personal & Recht",
  "Planung & Büro",
  "Informatik & Code",
  "Branchen-Pakete",
  "Automatisierung & Integration",
  "Kundenservice",
  "Daten & KI",
] as const;

/** Gesamtzahl der Skills – überall dynamisch verwenden statt hart codieren. */
export const SKILL_ANZAHL = SKILLS.length;

/* ------------------------------------------------------------------ */
/* Abo-Stufen: jede Stufe schaltet zusätzliche Skills frei.            */
/* Ein System, sechs Ausbaustufen – höhere Stufen enthalten immer      */
/* alles aus den tieferen.                                             */
/* ------------------------------------------------------------------ */

export type SkillStufe = "FREE" | "PERSONAL" | "STARTER" | "PROFESSIONAL" | "BUSINESS" | "ENTERPRISE";

export const STUFEN_REIHENFOLGE: SkillStufe[] = [
  "FREE", "PERSONAL", "STARTER", "PROFESSIONAL", "BUSINESS", "ENTERPRISE",
];

/** Ab welcher Stufe ein Skill verfügbar ist (alles Aufgezählte inklusive). */
export const SKILL_AB_STUFE: Record<string, SkillStufe> = {
  /* FREE – der Kern zum Kennenlernen (8) */
  "/website": "FREE",
  "/offerte": "FREE",
  "/dokument": "FREE",
  "/werbetext": "FREE",
  "/kontrolle": "FREE",
  "/uebersetzen": "FREE",
  "/termine": "FREE",
  "/code": "FREE",
  /* PERSONAL – der Alltag von Einzelpersonen (+8 = 16) */
  "/praesentation": "PERSONAL",
  "/rechnung": "PERSONAL",
  "/mahnung": "PERSONAL",
  "/geschaeftsbrief": "PERSONAL",
  "/social": "PERSONAL",
  "/newsletter": "PERSONAL",
  "/sitzungsprotokoll": "PERSONAL",
  "/whatsapp": "PERSONAL",
  /* STARTER – Marketing + Verkauf fürs Tagesgeschäft (+8 = 24) */
  "/stellenanzeige": "STARTER",
  "/kampagne": "STARTER",
  "/verkaufsskript": "STARTER",
  "/nachfassen": "STARTER",
  "/kundenumfrage": "STARTER",
  "/reklamation": "STARTER",
  "/support": "STARTER",
  "/wochenbericht": "STARTER",
  /* PROFESSIONAL – Analyse, Finanzen, Technik (+8 = 32) */
  "/markt": "PROFESSIONAL",
  "/preise": "PROFESSIONAL",
  "/prognose": "PROFESSIONAL",
  "/budget": "PROFESSIONAL",
  "/liquiditaet": "PROFESSIONAL",
  "/kalkulation": "PROFESSIONAL",
  "/prozesse": "PROFESSIONAL",
  "/bugfix": "PROFESSIONAL",
  /* BUSINESS – Personal, Recht, Führung (+8 = 40) */
  "/bewerber-check": "BUSINESS",
  "/arbeitszeugnis": "BUSINESS",
  "/mitarbeitergespraech": "BUSINESS",
  "/onboarding": "BUSINESS",
  "/vertrag": "BUSINESS",
  "/datenschutz": "BUSINESS",
  "/prozess-automatisierung": "BUSINESS",
  "/abteilungs-bericht": "BUSINESS",
  /* Firmen-Paket 2026 (+4 = 48 total) */
  "/jahresplanung": "PERSONAL",
  "/schulung": "STARTER",
  "/lieferanten-vergleich": "PROFESSIONAL",
  "/krisenplan": "BUSINESS",
  /* ENTERPRISE – Strategie und Systemlandschaft */
  "/businessplan": "ENTERPRISE",
  "/api-doku": "ENTERPRISE",
  "/ki-strategie": "ENTERPRISE",
  "/integrations-plan": "ENTERPRISE",

  /* ---- Erweiterung 2026: universell für jede Branche ---- */
  /* Kundenservice – schon früh nützlich */
  "/faq": "PERSONAL",
  "/support-bausteine": "PERSONAL",
  "/bewertung-antwort": "STARTER",
  "/rueckgewinnung": "STARTER",
  /* Branchen-Pakete – Kern für das Tagesgeschäft (STARTER) */
  "/handwerk": "STARTER",
  "/gastronomie": "STARTER",
  "/handel": "STARTER",
  "/immobilien": "STARTER",
  "/beratung": "STARTER",
  "/fitness": "STARTER",
  "/werkstatt": "STARTER",
  "/event": "STARTER",
  "/reise": "STARTER",
  /* Branchen-Pakete – anspruchsvoller (PROFESSIONAL) */
  "/gesundheit": "PROFESSIONAL",
  "/bildung": "PROFESSIONAL",
  "/logistik": "PROFESSIONAL",
  "/bau": "PROFESSIONAL",
  "/treuhand": "PROFESSIONAL",
  "/verein": "PROFESSIONAL",
  "/produktion": "PROFESSIONAL",
  /* Daten & KI */
  "/datenanalyse": "PROFESSIONAL",
  "/kpi-set": "BUSINESS",
  "/ab-test": "BUSINESS",
  "/wettbewerbsanalyse": "BUSINESS",
  "/markteintritt": "ENTERPRISE",
  /* Automatisierung & Integration */
  "/automatisierung": "PROFESSIONAL",
  "/workflow": "PROFESSIONAL",
  "/integration": "BUSINESS",
  "/datenimport": "BUSINESS",
  "/api-anbindung": "BUSINESS",
  "/report-automatik": "BUSINESS",
};

/** Ist ein Skill in der gegebenen Stufe enthalten? */
export function skillVerfuegbar(befehl: string, stufe: SkillStufe): boolean {
  const ab = SKILL_AB_STUFE[befehl] ?? "FREE";
  return STUFEN_REIHENFOLGE.indexOf(stufe) >= STUFEN_REIHENFOLGE.indexOf(ab);
}

/** Anzahl verfügbarer Skills pro Stufe (für Preistabellen und Shop). */
export function skillAnzahlFuer(stufe: SkillStufe): number {
  return SKILLS.filter((s) => skillVerfuegbar(s.befehl, stufe)).length;
}

/** Findet Skills, deren Befehl oder Name zur Eingabe passt (für "/"-Palette). */
export function skillSuche(eingabe: string): Skill[] {
  const q = eingabe.trim().toLowerCase();
  if (!q.startsWith("/")) return [];
  const rest = q.slice(1);
  return SKILLS.filter(
    (s) => s.befehl.slice(1).startsWith(rest) || s.name.toLowerCase().includes(rest),
  ).slice(0, 8);
}
