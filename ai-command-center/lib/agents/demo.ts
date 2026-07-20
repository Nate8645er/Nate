/**
 * Demo-Modus: deterministische, simulierte Agentenantworten.
 *
 * Wird vom Orchestrator verwendet, wenn fuer einen Provider kein API-Key
 * gesetzt ist oder der Call endgueltig scheitert. Die Mission laeuft damit
 * IMMER vollstaendig durch – ohne Netzwerk, ohne Zufall (gleiche Eingabe
 * ergibt exakt dieselbe Ausgabe).
 */

import type { QualityReport, TaskPlan } from "./types";

/** Deterministischer Hash (FNV-1a) fuer stabile "Bewertungen" aus Text. */
function hash(text: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

/** Kuerzt das Ziel fuer Ueberschriften auf eine handliche Laenge. */
function shortGoal(goal: string): string {
  const g = goal.trim().replace(/\s+/g, " ");
  return g.length > 80 ? `${g.slice(0, 77)}…` : g;
}

/** Commander-Plan im Demo-Modus. */
export function demoPlan(goal: string): TaskPlan {
  const g = shortGoal(goal);
  return {
    builderTask: `Erstelle ein konkretes, sofort verwendbares Umsetzungspaket fuer "${g}": Struktur, Kerninhalte und naechste Schritte.`,
    analystTask: `Analysiere fuer "${g}" Zielgruppe, Marktkontext, Chancen und Risiken und leite drei priorisierte Empfehlungen ab.`,
  };
}

/** Builder-Ergebnis im Demo-Modus. */
export function demoBuilderOutput(goal: string, task: string): string {
  const g = shortGoal(goal);
  return [
    `## Umsetzungspaket: ${g}`,
    "",
    `**Auftrag:** ${task}`,
    "",
    "### 1. Konzept",
    `- Klarer Kern: Die Mission "${g}" wird in ein umsetzbares Ergebnis mit definiertem Umfang uebersetzt.`,
    "- Aufbau in drei Ebenen: Fundament (Ziel & Zielgruppe), Ausarbeitung (Inhalte & Struktur), Feinschliff (Ton & Details).",
    "",
    "### 2. Struktur",
    "1. Ausgangslage und Zielbild in zwei Saetzen festhalten.",
    "2. Kerninhalte als nummerierte Bausteine ausarbeiten – jeder Baustein direkt verwendbar.",
    "3. Offene Punkte als konkrete Entscheidungsfragen an den Auftraggeber formulieren.",
    "",
    "### 3. Naechste Schritte",
    "- Entwurf intern gegen das Missionsziel pruefen.",
    "- Eine Feedbackrunde einplanen, danach finalisieren.",
    "- Ergebnis in den Zielkanal (Dokument, Website, Praesentation) ueberfuehren.",
  ].join("\n");
}

/** Analyst-Ergebnis im Demo-Modus. */
export function demoAnalystOutput(goal: string, task: string): string {
  const g = shortGoal(goal);
  return [
    `## Analyse: ${g}`,
    "",
    `**Auftrag:** ${task}`,
    "",
    "### Zielgruppe",
    "- Primaer: Entscheider mit klarem Bedarf und wenig Zeit – erwartet ein direkt verwendbares Ergebnis.",
    "- Sekundaer: Umsetzende Teams, die mit dem Ergebnis weiterarbeiten.",
    "",
    "### Marktkontext",
    "- Annahme: Der Wettbewerb liefert generische Loesungen; Differenzierung entsteht durch Praezision und Tempo.",
    "- Annahme: Der groesste Hebel liegt in einer klaren Positionierung, nicht in mehr Umfang.",
    "",
    "### Chancen",
    "- Schneller sichtbarer Mehrwert durch ein fokussiertes erstes Ergebnis.",
    "- Wiederverwendbare Struktur fuer Folgemissionen.",
    "",
    "### Risiken",
    "- Unklare Zieldefinition fuehrt zu Streuverlust – Gegenmassnahme: Zielbild in Satz 1 fixieren.",
    "- Ueberladung des Ergebnisses – Gegenmassnahme: maximal drei Kernaussagen.",
    "",
    "### Priorisierte Empfehlungen",
    "1. Zielbild und Kernbotschaft zuerst festziehen.",
    "2. Ein minimal vollstaendiges Ergebnis liefern, dann iterieren.",
    "3. Erfolgskriterium definieren (woran wird das Ergebnis gemessen?).",
  ].join("\n");
}

/** Quality-Report im Demo-Modus: stabiler Score 82–91 aus dem Input abgeleitet. */
export function demoQualityReport(combinedOutputs: string): QualityReport {
  return {
    score: 82 + (hash(combinedOutputs) % 10),
    improvements: [
      "Kernaussagen mit konkreten Zahlen oder Beispielen unterlegen.",
      "Annahmen durch kurze Validierung (Kundenfeedback, Daten) absichern.",
      "Naechste Schritte mit Verantwortlichkeiten und Terminen versehen.",
    ],
  };
}

/** Finale Synthese im Demo-Modus. */
export function demoSynthesis(goal: string, combinedOutputs: string): string {
  const g = shortGoal(goal);
  const body = combinedOutputs.trim()
    ? combinedOutputs.trim()
    : "_Keine Worker-Ergebnisse verfuegbar – Kurzfassung aus dem Missionsziel abgeleitet._";
  return [
    `# Ergebnis: ${g}`,
    "",
    "## Zusammenfassung",
    `Die Mission "${g}" wurde vom Team bearbeitet: Der Builder hat ein umsetzbares Paket erstellt, der Analyst Kontext, Chancen und Risiken geliefert. Beides ist unten zu einem verwendbaren Gesamtergebnis zusammengefuehrt.`,
    "",
    body,
    "",
    "## Empfohlenes Vorgehen",
    "1. Ergebnis reviewen und Zielbild bestaetigen.",
    "2. Die priorisierten Empfehlungen des Analysten umsetzen.",
    "3. Verbesserungsvorschlaege des Quality-Agenten einarbeiten und finalisieren.",
  ].join("\n");
}
