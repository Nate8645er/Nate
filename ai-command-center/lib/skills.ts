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
    | "Informatik & Code";
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
  /* ENTERPRISE – Strategie und Systemlandschaft (+4 = 44) */
  "/businessplan": "ENTERPRISE",
  "/api-doku": "ENTERPRISE",
  "/ki-strategie": "ENTERPRISE",
  "/integrations-plan": "ENTERPRISE",
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
