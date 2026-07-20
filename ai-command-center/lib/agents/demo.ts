/**
 * Demo-Modus: deterministische, simulierte Agentenantworten.
 *
 * Wird vom Orchestrator verwendet, wenn fuer einen Provider kein API-Key
 * gesetzt ist oder der Call endgueltig scheitert. Die Mission laeuft damit
 * IMMER vollstaendig durch – ohne Netzwerk, ohne Zufall (gleiche Eingabe
 * ergibt exakt dieselbe Ausgabe).
 */

import type { QualityReport, TaskPlan, WorkerRole } from "./types";

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

/** Demo-Teilaufgabe je Worker (fuer den Commander-Plan im Demo-Modus). */
const DEMO_TASKS: Record<WorkerRole, (g: string) => string> = {
  builder: (g) =>
    `Erstelle ein konkretes, sofort verwendbares Umsetzungspaket fuer "${g}": Struktur, Kerninhalte und naechste Schritte.`,
  analyst: (g) =>
    `Analysiere fuer "${g}" Zielgruppe, Marktkontext, Chancen und Risiken und leite drei priorisierte Empfehlungen ab.`,
  marketing: (g) =>
    `Entwickle fuer "${g}" eine Kampagnenidee mit Zielgruppen-Profilen und einem 4-Wochen-Content-Plan.`,
  research: (g) =>
    `Recherchiere fuer "${g}" Hintergruende und Alternativen, vergleiche die Optionen strukturiert und bewerte die Quellenlage.`,
  coding: (g) =>
    `Entwirf fuer "${g}" eine technische Loesung mit Code-Skizze und einem konkreten Automatisierungs-Vorschlag.`,
  business: (g) =>
    `Bewerte fuer "${g}" Strategie, grobe Zahlen (Kosten/Ertrag) und die drei wichtigsten Risiken inkl. Gegenmassnahmen.`,
};

/** Commander-Plan im Demo-Modus: je eine Teilaufgabe pro aktivem Worker. */
export function demoPlan(goal: string, workers: readonly WorkerRole[]): TaskPlan {
  const g = shortGoal(goal);
  const plan: TaskPlan = {};
  for (const worker of workers) plan[worker] = DEMO_TASKS[worker](g);
  return plan;
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

/** Marketing-Ergebnis im Demo-Modus. */
export function demoMarketingOutput(goal: string, task: string): string {
  const g = shortGoal(goal);
  return [
    `## Marketing-Paket: ${g}`,
    "",
    `**Auftrag:** ${task}`,
    "",
    "### Kampagnenidee",
    `- Leitmotiv: "${g}" als greifbaren Kundennutzen erzaehlen – eine Kernbotschaft, ueberall konsistent.`,
    "- Mechanik: Aufmerksamkeit (Reichweiten-Kanal) -> Vertrauen (Beweis/Story) -> Handlung (klares Angebot mit CTA).",
    "",
    "### Zielgruppen",
    "- Kernzielgruppe: Bestandsnahe Kaufbereite mit konkretem Bedarf – Ansprache direkt und nutzenorientiert.",
    "- Ausbauzielgruppe: Interessierte ohne Dringlichkeit – Ansprache ueber Inhalte mit Mehrwert statt Rabatt.",
    "",
    "### Content-Plan (4 Wochen)",
    "1. Woche 1: Kernbotschaft + Vorstellung (1 Hero-Beitrag, 2 Kurzformate).",
    "2. Woche 2: Beweis – Kundenstimme oder Blick hinter die Kulissen (2 Beitraege).",
    "3. Woche 3: Angebot mit klarem CTA (1 Kampagnen-Beitrag, 1 Reminder).",
    "4. Woche 4: Auswertung + bestes Format wiederholen (2 Beitraege).",
    "",
    "### Messbarer naechster Schritt",
    "- Ein Kanal, ein Angebot, zwei Wochen testen; Erfolgskriterium vorab festlegen (z. B. Anfragen pro Woche).",
  ].join("\n");
}

/** Coding-Ergebnis im Demo-Modus. */
export function demoCodingOutput(goal: string, task: string): string {
  const g = shortGoal(goal);
  return [
    `## Technische Loesung: ${g}`,
    "",
    `**Auftrag:** ${task}`,
    "",
    "### Loesungsskizze",
    "- Kleinster sinnvoller Aufbau: ein Eingang (Formular/API), ein Verarbeitungsschritt, ein Ausgang (Benachrichtigung/Ablage).",
    "- Erst manuell validieren, dann automatisieren – keine Infrastruktur vor dem ersten Nutzen.",
    "",
    "### Code-Skizze",
    "```ts",
    "// Minimaler Automatisierungs-Endpunkt (Skizze, bewusst ohne Framework-Details)",
    "export async function handleRequest(input: { name: string; nachricht: string }) {",
    "  if (!input.name.trim() || !input.nachricht.trim()) {",
    '    return { ok: false, fehler: "Name und Nachricht sind erforderlich." };',
    "  }",
    "  await speichern(input);        // z. B. Tabelle oder CRM",
    "  await benachrichtigen(input);  // z. B. E-Mail oder Chat",
    "  return { ok: true };",
    "}",
    "```",
    "",
    "### Automatisierungs-Vorschlag",
    "1. Wiederkehrenden manuellen Schritt identifizieren (hoechste Frequenz zuerst).",
    "2. Mit einem No-Code-Workflow oder kleinem Skript abbilden; Fehlerfall mit Benachrichtigung absichern.",
    "3. Annahme: Es existiert noch keine Systemlandschaft – die Skizze bleibt bewusst anschlussoffen.",
  ].join("\n");
}

/** Research-Ergebnis im Demo-Modus. */
export function demoResearchOutput(goal: string, task: string): string {
  const g = shortGoal(goal);
  return [
    `## Tiefenrecherche: ${g}`,
    "",
    `**Auftrag:** ${task}`,
    "",
    "### Hintergrund",
    `- Die Fragestellung "${g}" laesst sich in drei Optionen zerlegen: Status quo behalten, punktuell verbessern, neu aufsetzen.`,
    "",
    "### Vergleich der Optionen",
    "1. Status quo: kein Aufwand, aber ungenutztes Potenzial – sinnvoll nur bei fehlenden Ressourcen.",
    "2. Punktuell verbessern: bestes Aufwand-Nutzen-Verhaeltnis; schnell messbar.",
    "3. Neu aufsetzen: hoechstes Potenzial, aber laengste Amortisation und groesstes Risiko.",
    "",
    "### Quellenlage",
    "- Demo-Modus: Es wurden keine Live-Quellen abgerufen; alle Aussagen sind als Annahmen gekennzeichnet.",
    "- Fuer eine belastbare Entscheidung: zwei bis drei Branchenquellen und eigene Zahlen ergaenzen.",
    "",
    "### Empfehlung",
    "- Mit Option 2 starten und ein Erfolgskriterium definieren; Option 3 nur bei belegtem Engpass pruefen.",
  ].join("\n");
}

/** Business-Ergebnis im Demo-Modus. */
export function demoBusinessOutput(goal: string, task: string): string {
  const g = shortGoal(goal);
  return [
    `## Business-Bewertung: ${g}`,
    "",
    `**Auftrag:** ${task}`,
    "",
    "### Strategie",
    `- "${g}" auf ein klares Nutzenversprechen fuer eine Kernzielgruppe zuspitzen; Breite folgt nach dem ersten Beleg.`,
    "",
    "### Zahlen (Annahmen)",
    "- Aufwand: ueberschaubares Startbudget plus laufende Zeit pro Woche – vorab als Obergrenze fixieren.",
    "- Ertrag: erster messbarer Effekt nach 4 bis 8 Wochen realistisch; Break-even konservativ planen.",
    "",
    "### Risiken und Gegenmassnahmen",
    "1. Nachfrage bleibt aus (hoch/mittel): mit kleinem Test validieren, bevor investiert wird.",
    "2. Aufwand unterschaetzt (mittel/mittel): Umfang fest deckeln, Zusatzwuensche in Phase 2 schieben.",
    "3. Kein messbarer Effekt (mittel/hoch): Erfolgskriterium vorab definieren und woechentlich pruefen.",
    "",
    "### Entscheidungsvorlage",
    "- Weiterfuehren, wenn das Erfolgskriterium nach dem Testzeitraum erreicht ist; sonst stoppen oder anpassen.",
  ].join("\n");
}

/**
 * Demo-Ausgabe je Worker-Rolle – der Orchestrator waehlt darueber den
 * passenden Fallback fuer jeden aktiven Worker.
 */
export const DEMO_WORKER_OUTPUTS: Record<
  WorkerRole,
  (goal: string, task: string) => string
> = {
  builder: demoBuilderOutput,
  analyst: demoAnalystOutput,
  marketing: demoMarketingOutput,
  research: demoResearchOutput,
  coding: demoCodingOutput,
  business: demoBusinessOutput,
};

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
    `Die Mission "${g}" wurde vom Team bearbeitet: Jeder aktive Worker hat seine Teilaufgabe geliefert – vom umsetzbaren Paket bis zu Kontext, Chancen und Risiken. Alles ist unten zu einem verwendbaren Gesamtergebnis zusammengefuehrt.`,
    "",
    body,
    "",
    "## Empfohlenes Vorgehen",
    "1. Ergebnis reviewen und Zielbild bestaetigen.",
    "2. Die priorisierten Empfehlungen des Analysten umsetzen.",
    "3. Verbesserungsvorschlaege des Quality-Agenten einarbeiten und finalisieren.",
  ].join("\n");
}
