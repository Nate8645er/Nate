/**
 * Ein-Klick-Vorlagen (Branchen-Playbooks) – vorformulierte Aufträge, die der
 * Nutzer mit einem Klick in die Mission übernimmt. Reine, testbare Daten +
 * Auswahl-Helfer; keine Abhängigkeiten. Team-Empfehlung Nr. 2 (einstimmig).
 */

import type { BranchenId } from "./roi";

export interface Vorlage {
  id: string;
  /** Branche, für die die Vorlage besonders passt ("alle" = überall sinnvoll). */
  branche: BranchenId | "alle";
  icon: string;
  titel: string;
  /** Kurzbeschreibung für die Karte. */
  kurz: string;
  /** Der fertige Auftragstext, der ins Missions-Feld übernommen wird. */
  prompt: string;
}

/** Alle Vorlagen. Reihenfolge = Standard-Anzeigereihenfolge. */
export const VORLAGEN: readonly Vorlage[] = [
  // Allgemein
  { id: "angebot", branche: "alle", icon: "📝", titel: "Angebot erstellen", kurz: "Versandfertige Offerte mit Positionen & Preisen.", prompt: "Erstelle eine professionelle, versandfertige Offerte für [Kunde] über [Leistung]. Mit Positionen, Einzel- und Gesamtpreisen (CHF), Gültigkeitsdauer, Zahlungs- und Lieferbedingungen. Höflicher Ton, klar strukturiert." },
  { id: "mail-antwort", branche: "alle", icon: "📨", titel: "Kunden-Mail beantworten", kurz: "Freundliche, klare Antwort in Ihrem Ton.", prompt: "Beantworte diese Kundenanfrage freundlich, klar und lösungsorientiert in unserem Ton: [Anfrage hier einfügen]. Biete konkrete nächste Schritte an." },
  { id: "social-woche", branche: "alle", icon: "📣", titel: "Social-Media-Woche planen", kurz: "7 fertige Posts inkl. Hashtags & Zeitplan.", prompt: "Plane eine Social-Media-Woche für unser Unternehmen: 7 fertige Posts (Text + Hashtags + Bildidee), passend zu unseren Leistungen, mit sinnvollem Veröffentlichungs-Zeitplan. Abwechslungsreich: Nutzen, Beweis, Angebot, Wissen." },
  { id: "bericht", branche: "alle", icon: "📊", titel: "Monatsbericht schreiben", kurz: "Zahlen zusammenfassen + Empfehlungen.", prompt: "Erstelle einen klaren Monatsbericht aus den angehängten Zahlen/Notizen: Zusammenfassung, wichtigste Kennzahlen, Trends und 3 konkrete Handlungsempfehlungen. Für die Geschäftsleitung verständlich." },

  // Handel / E-Commerce
  { id: "produkttexte", branche: "handel", icon: "🛒", titel: "Produkttexte schreiben", kurz: "Verkaufsstarke Beschreibungen inkl. SEO.", prompt: "Schreibe verkaufsstarke Produktbeschreibungen für [Produkt(e)]: Nutzen statt Merkmale, klare Struktur, Bullet-Highlights und SEO-Keywords. Ergänze je einen kurzen und einen ausführlichen Text." },
  { id: "retoure", branche: "handel", icon: "↩️", titel: "Retouren-Antwort", kurz: "Kulante, markenkonforme Rückmeldung.", prompt: "Formuliere eine kulante, markenkonforme Antwort auf eine Retouren-/Reklamationsanfrage: [Anliegen]. Lösung anbieten, Vertrauen erhalten, nächste Schritte nennen." },

  // Handwerk / Bau
  { id: "terminbestaetigung", branche: "handwerk", icon: "🔨", titel: "Termin & Materialliste", kurz: "Bestätigung + Materialliste in Minuten.", prompt: "Erstelle eine freundliche Terminbestätigung für [Auftrag/Kunde] inkl. voraussichtlicher Dauer, benötigter Materialliste und einer kurzen Vorbereitungs-Checkliste für den Kunden." },

  // Gastronomie
  { id: "menue", branche: "gastro", icon: "🍽️", titel: "Menü & Aktion", kurz: "Menükarte + Social-Aktion für ruhige Tage.", prompt: "Erstelle einen Vorschlag für eine Wochen-Menükarte und eine passende Social-Media-Aktion, um ruhige Tage zu füllen. Appetitliche Beschreibungen, Preisrahmen [z. B. CHF], klarer Call-to-Action." },

  // Dienstleistung / Beratung
  { id: "protokoll", branche: "dienstleistung", icon: "🗒️", titel: "Meeting-Protokoll", kurz: "Notizen → sauberes Protokoll + To-dos.", prompt: "Mach aus diesen Meeting-Notizen ein sauberes Protokoll: Zusammenfassung, Entscheidungen, offene Punkte und To-dos mit Verantwortlichen und Fristen: [Notizen einfügen]." },

  // Gesundheit / Praxis
  { id: "aufklaerung", branche: "gesundheit", icon: "🩺", titel: "Patienten-Info", kurz: "Verständlicher Aufklärungstext.", prompt: "Schreibe einen patientenfreundlichen, verständlichen Informations-/Aufklärungstext zu [Thema]. Klar, beruhigend, ohne Fachjargon, mit häufigen Fragen am Ende. Kein medizinischer Rat ohne Freigabe der Praxis." },

  // Marketing / Agentur
  { id: "kampagne", branche: "marketing", icon: "🎯", titel: "Kampagne entwerfen", kurz: "Konzept, Kanäle, Anzeigentexte.", prompt: "Entwirf eine kompakte Marketing-Kampagne für [Ziel/Angebot]: Kernbotschaft, Zielgruppe, Kanäle, 3 Anzeigentexte (kurz/mittel/lang) und ein einfacher Wochen-Zeitplan." },
  { id: "landingpage", branche: "marketing", icon: "🌐", titel: "Landingpage-Text", kurz: "Überschriften, Nutzen, CTA – konversionsstark.", prompt: "Schreibe konversionsstarken Landingpage-Text für [Angebot]: starke Hauptüberschrift + 3 Varianten, Nutzenblöcke, Einwand-Behandlung, Social-Proof-Platzhalter und klarer Call-to-Action." },
];

/**
 * Vorlagen für eine Branche: passende zuerst (Branche exakt), danach die
 * allgemeinen ("alle"). Unbekannte Branche → nur die allgemeinen + alle übrigen.
 * `limit` begrenzt die Anzahl (Standard: alle).
 */
export function vorlagenFuer(branche: BranchenId | null | undefined, limit?: number): Vorlage[] {
  const passend = branche ? VORLAGEN.filter((v) => v.branche === branche) : [];
  const allgemein = VORLAGEN.filter((v) => v.branche === "alle");
  const rest = VORLAGEN.filter((v) => v.branche !== "alle" && v.branche !== branche);
  const sortiert = [...passend, ...allgemein, ...rest];
  return typeof limit === "number" ? sortiert.slice(0, Math.max(0, limit)) : sortiert;
}
