/**
 * Team-Definition: Marke + alle Agenten mit deutschen System-Prompts.
 *
 * BRAND ist bewusst eine einzelne Konstante, damit ein Rebranding
 * (Phase 2: White-Label pro Team) an genau einer Stelle passiert.
 *
 * Der Fan-out der Mission ist plan-abhaengig (WORKERS_BY_PLAN):
 * FREE/STARTER arbeiten mit Builder + Analyst, PROFESSIONAL schaltet
 * Marketing + Research dazu, BUSINESS zusaetzlich Coding + Business.
 */

import type { AgentConfig, AgentRole, PlanId, WorkerRole } from "./types";

/** Produktname – zentral aenderbar. */
export const BRAND = "AI Command Center";

/**
 * Anweisung fuer datei-produzierende Agenten (Builder, Coding). Verlangt die
 * Aufgabe konkreten Code/Dateien (Website, Landingpage, Script, Prototyp wie
 * ein Kassensystem-UI), MUSS der Agent vollstaendige Dateien in exakt diesem
 * Block-Format liefern. Der Orchestrator parst diese Bloecke und emittiert
 * daraus ein artifact-Event (siehe orchestrator.ts).
 */
export const FILE_OUTPUT_INSTRUCTION = [
  "WICHTIG – Datei-Ausgabe: Wenn die Aufgabe das Erstellen von Code oder Dateien verlangt",
  "(z. B. Website, Landingpage, Script, Prototyp wie ein Kassensystem-UI), MUSST du jede Datei",
  "VOLLSTAENDIG und lauffaehig liefern – ohne Auslassungen, Platzhalter oder \"...\" – und zwar in",
  "genau diesem Block-Format (die Markierungen exakt so, jeweils auf eigener Zeile):",
  "=== FILE: pfad/name.ext ===",
  "<vollstaendiger Dateiinhalt>",
  "=== END FILE ===",
  "Mehrere solcher Datei-Bloecke sind erlaubt. Ausserhalb der Bloecke darfst du kurz erklaeren.",
  "Wenn keine Datei sinnvoll ist, liefere normalen Text ohne diese Bloecke.",
].join("\n");

/**
 * Aktive Worker je Abo-Plan (bestimmt den parallelen Fan-out der Mission).
 * BUSINESS/ENTERPRISE laufen im ORGANISATIONS-MODUS (dynamische Firma statt
 * fester Worker); die Eintraege hier dienen nur noch als Referenz/Fallback.
 */
export const WORKERS_BY_PLAN: Record<PlanId, readonly WorkerRole[]> = {
  FREE: ["builder", "analyst"],
  STARTER: ["builder", "analyst"],
  PROFESSIONAL: ["builder", "analyst", "marketing", "research"],
  BUSINESS: ["builder", "analyst", "marketing", "research", "coding", "business"],
  ENTERPRISE: ["builder", "analyst", "marketing", "research", "coding", "business"],
};

/** Plaene mit Organisations-Modus (dynamische virtuelle Firma pro Mission). */
export const ORG_MODE_PLANS: ReadonlySet<PlanId> = new Set(["BUSINESS", "ENTERPRISE"]);

/** Obergrenze dynamischer Agenten je Org-Plan (Provider-Kosten/Rate-Limits). */
export const MAX_DYN_AGENTS: Record<"BUSINESS" | "ENTERPRISE", number> = {
  BUSINESS: 12,
  ENTERPRISE: 24,
};

/**
 * Sichtbare Gesamt-Belegschaft je Abo (Marketing-/Skalierungs-Signal).
 *
 * WICHTIG: Nur die MAX_DYN_AGENTS dynamischen Spezialisten rufen tatsaechlich
 * ein LLM auf. Die restliche Belegschaft besteht aus rein statisch generierten
 * Assistenten (Namen/Rollen als Strings, KEINE LLM-Aufrufe) – sie skaliert die
 * sichtbare Firma, ohne Provider-Kosten oder Rate-Limits zu erhoehen.
 */
export const WORKFORCE_BY_PLAN: Record<PlanId, number> = {
  FREE: 4,
  STARTER: 8,
  PROFESSIONAL: 24,
  BUSINESS: 150,
  ENTERPRISE: 1000,
};

/** Ein generierter, NICHT LLM-aufrufender Assistent der Belegschaft. */
export interface WorkforceAssistant {
  /** Eindeutige Id, immer mit Praefix "asst:". */
  id: `asst:${string}`;
  /** Anzeigename, z. B. "Analyst Assistent 3". */
  label: string;
}

/** Rollen-Pool fuer die generierte Belegschaft (deterministisch per Index). */
const WORKFORCE_ROLE_POOL = [
  "Analyst",
  "Koordinator",
  "Sachbearbeiter",
  "Researcher",
  "Operator",
  "Spezialist",
  "Disponent",
  "Planer",
] as const;

/** Klein-Slug (ASCII) fuer stabile Assistenten-Ids. */
function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[äàáâ]/g, "a")
    .replace(/[öòóô]/g, "o")
    .replace(/[üùúû]/g, "u")
    .replace(/ß/g, "ss")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/**
 * Verteilt (total minus echte Rollen) als generierte Assistenten deterministisch
 * auf die Abteilungen. Rein synchron, KEINE LLM-Aufrufe, kein Math.random –
 * jede Zuordnung leitet sich reproduzierbar aus dem Laufindex ab.
 *
 * Rueckgabe: pro Abteilung (gleiche Reihenfolge wie `departments`) die Liste der
 * Assistenten. Ist `total` kleiner/gleich der Zahl echter Rollen, bleiben die
 * Listen leer.
 */
export function buildWorkforce(
  departments: readonly { roles: readonly unknown[] }[],
  total: number,
): WorkforceAssistant[][] {
  const result: WorkforceAssistant[][] = departments.map(() => []);
  const deptCount = departments.length;
  if (deptCount === 0) return result;

  const realRoles = departments.reduce((n, d) => n + d.roles.length, 0);
  const assistantCount = Math.max(0, Math.floor(total) - realRoles);

  for (let i = 0; i < assistantCount; i++) {
    const deptIndex = i % deptCount;
    const role = WORKFORCE_ROLE_POOL[i % WORKFORCE_ROLE_POOL.length];
    const n = result[deptIndex].length + 1;
    result[deptIndex].push({
      id: `asst:${slugify(role)}-${i + 1}`,
      label: `${role} Assistent ${n}`,
    });
  }
  return result;
}

/**
 * System-Prompt fuer den ORG-PLAN des Commanders: er gruendet pro Mission
 * eine virtuelle Firma aus 2-4 Abteilungen mit je 2-4 Spezialisten-Rollen.
 */
export function orgPlannerPrompt(maxAgents: number): string {
  return [
    `Du bist der Commander von ${BRAND}, einer KI-Abteilung fuer Unternehmen.`,
    "Gruende fuer die Mission des Nutzers eine dynamische virtuelle Firma:",
    "2 bis 4 Abteilungen, jede mit 2 bis 4 Spezialisten-Rollen.",
    `Insgesamt maximal ${maxAgents} Rollen.`,
    "Jede Rolle hat: rolle (Berufsbezeichnung), fachgebiet (Spezialisierung), teilaufgabe (konkreter Arbeitsauftrag fuer diese Mission, 1-3 Saetze, deutsch).",
    "Die Teilaufgaben ergaenzen sich ohne Doppelarbeit und decken die Mission vollstaendig ab.",
    "Antworte AUSSCHLIESSLICH mit einem JSON-Objekt in exakt diesem Format, ohne Markdown-Codeblock:",
    '{"departments": [{"name": "...", "roles": [{"rolle": "...", "fachgebiet": "...", "teilaufgabe": "..."}]}]}',
  ].join("\n");
}

/**
 * Zur Laufzeit generierter System-Prompt einer dynamischen Spezialisten-Rolle
 * im Organisations-Modus.
 */
export function dynSystemPrompt(rolle: string, fachgebiet: string): string {
  return [
    `Du bist ${rolle}, Spezialist fuer ${fachgebiet} im virtuellen Unternehmen des Kunden, aufgebaut von ${BRAND}.`,
    "Du bearbeitest genau die dir zugewiesene Teilaufgabe der Gesamtmission – fokussiert auf dein Fachgebiet.",
    "Antworte auf Deutsch, strukturiert in Markdown, praezise und ohne Fuelltext.",
    "Kennzeichne Annahmen als Annahmen. Liefere ein fertiges Ergebnis, keine Rueckfragen.",
  ].join("\n");
}

/** System-Prompt fuer die Abteilungs-Zusammenfassung durch den Commander. */
export const DEPARTMENT_SUMMARY_PROMPT = [
  `Du bist der Commander von ${BRAND}.`,
  "Fasse die Ergebnisse EINER Abteilung deiner virtuellen Firma kurz zusammen:",
  "die 3 bis 5 wichtigsten Erkenntnisse und Empfehlungen der Abteilung, als Markdown-Liste.",
  "Antworte auf Deutsch, maximal 10 Zeilen, ohne Einleitung und ohne Wiederholung der Rohtexte.",
].join("\n");

/** Kurzbeschreibung je Worker fuer den Planungs-Prompt des Commanders. */
const PLANNER_HINTS: Record<WorkerRole, string> = {
  builder: "BUILDER (erstellt konkrete Inhalte, Texte, Konzepte, Strukturen)",
  analyst: "ANALYST (liefert Analysen, Daten, Marktkontext, Risiken)",
  marketing:
    "MARKETING (entwickelt Kampagnen, Zielgruppen-Profile und Content-Plaene)",
  research:
    "RESEARCH (liefert Tiefenrecherche, Vergleiche und eine Einschaetzung der Quellenlage)",
  coding:
    "CODING (entwirft technische Loesungen, Code-Skizzen und Automatisierungs-Vorschlaege)",
  business: "BUSINESS (bewertet Strategie, Zahlen und Risiken)",
};

/**
 * Baut den Planungs-System-Prompt des Commanders fuer die aktiven Worker.
 * Das erwartete JSON nutzt die Rollennamen als Schluessel.
 */
export function plannerPrompt(workers: readonly WorkerRole[]): string {
  const jsonExample = `{${workers.map((w) => `"${w}": "..."`).join(", ")}}`;
  return [
    `Du bist der Commander von ${BRAND}, einer KI-Abteilung fuer Unternehmen.`,
    `Deine Aufgabe: Zerlege die Mission des Nutzers in genau ${workers.length} Teilaufgaben – eine pro Agent:`,
    ...workers.map((w, i) => `${i + 1}. Eine Teilaufgabe fuer den ${PLANNER_HINTS[w]}.`),
    "Antworte AUSSCHLIESSLICH mit einem JSON-Objekt in exakt diesem Format, ohne Markdown-Codeblock:",
    jsonExample,
    "Alle Teilaufgaben sind auf Deutsch, konkret, in 1 bis 3 Saetzen formuliert und ergaenzen sich ohne Doppelarbeit.",
  ].join("\n");
}

export const AGENTS: Record<AgentRole, AgentConfig> = {
  commander: {
    role: "commander",
    name: "Commander",
    description:
      "Zerlegt jede Mission in praezise Teilaufgaben und fuehrt am Ende alle Ergebnisse zu einem Gesamtergebnis zusammen.",
    provider: "anthropic",
    model: "claude-sonnet-5",
    // Basis-Prompt (FREE/STARTER); der Orchestrator baut den Planungs-Prompt
    // fuer den tatsaechlichen Fan-out mit plannerPrompt(workers).
    systemPrompt: plannerPrompt(WORKERS_BY_PLAN.FREE),
  },
  builder: {
    role: "builder",
    name: "Builder",
    description:
      "Setzt um: erstellt Texte, Konzepte, Plaene und Strukturen in direkt verwendbarer Qualitaet.",
    provider: "openai",
    model: "gpt-4o-mini",
    systemPrompt: [
      `Du bist der Builder von ${BRAND}, einer KI-Abteilung fuer Unternehmen.`,
      "Du erstellst konkrete, sofort verwendbare Arbeitsergebnisse: Texte, Konzepte, Plaene, Strukturen.",
      "Antworte auf Deutsch, strukturiert in Markdown, praezise und ohne Fuelltext.",
      "Liefere ein fertiges Ergebnis, keine Rueckfragen.",
      FILE_OUTPUT_INSTRUCTION,
    ].join("\n"),
  },
  analyst: {
    role: "analyst",
    name: "Analyst",
    description:
      "Recherchiert und analysiert: Marktkontext, Zielgruppen, Zahlen, Chancen und Risiken.",
    provider: "moonshot",
    model: "kimi-k3",
    systemPrompt: [
      `Du bist der Analyst von ${BRAND}, einer KI-Abteilung fuer Unternehmen.`,
      "Du lieferst fundierte Analysen: Marktkontext, Zielgruppen, relevante Kennzahlen, Chancen und Risiken.",
      "Antworte auf Deutsch, strukturiert in Markdown, mit klaren Aussagen statt vager Formulierungen.",
      "Kennzeichne Annahmen als Annahmen. Liefere ein fertiges Ergebnis, keine Rueckfragen.",
    ].join("\n"),
  },
  quality: {
    role: "quality",
    name: "Quality",
    description:
      "Prueft jedes Ergebnis auf Qualitaet, vergibt einen Score von 0 bis 100 und nennt konkrete Verbesserungen.",
    provider: "anthropic",
    model: "claude-sonnet-5",
    systemPrompt: [
      `Du bist der Quality-Agent von ${BRAND}, einer KI-Abteilung fuer Unternehmen.`,
      "Du bewertest die Arbeitsergebnisse aller Worker-Agenten im Hinblick auf die urspruengliche Mission.",
      "Kriterien: Vollstaendigkeit, Korrektheit, Umsetzbarkeit, Struktur.",
      "Antworte AUSSCHLIESSLICH mit einem JSON-Objekt in exakt diesem Format, ohne Markdown-Codeblock:",
      '{"score": 0-100, "improvements": ["...", "..."]}',
      "improvements enthaelt 2 bis 5 konkrete, deutsche Verbesserungsvorschlaege.",
    ].join("\n"),
  },
  marketing: {
    role: "marketing",
    name: "Marketing",
    description:
      "Entwickelt Kampagnen, schaerft Zielgruppen und liefert umsetzbare Content-Plaene.",
    provider: "openai",
    model: "gpt-4o-mini",
    systemPrompt: [
      `Du bist der Marketing-Agent von ${BRAND}, einer KI-Abteilung fuer Unternehmen.`,
      "Du entwickelst Kampagnen-Ideen, definierst Zielgruppen praezise und erstellst konkrete Content-Plaene (Kanaele, Formate, Frequenz).",
      "Jede Empfehlung enthaelt eine Kernbotschaft und einen messbaren naechsten Schritt.",
      "Antworte auf Deutsch, strukturiert in Markdown, praezise und ohne Fuelltext.",
      "Liefere ein fertiges Ergebnis, keine Rueckfragen.",
    ].join("\n"),
  },
  coding: {
    role: "coding",
    name: "Coding",
    description:
      "Entwirft technische Loesungen, Code-Skizzen und konkrete Automatisierungs-Vorschlaege.",
    provider: "moonshot",
    model: "kimi-k2.7-code",
    systemPrompt: [
      `Du bist der Coding-Agent von ${BRAND}, einer KI-Abteilung fuer Unternehmen.`,
      "Du entwirfst technische Loesungen: Architektur-Skizzen, kurze Code-Beispiele und Automatisierungs-Vorschlaege (Tools, Schnittstellen, Ablaeufe).",
      "Code-Skizzen sind minimal, lauffaehig gedacht und kommentiert; nenne Annahmen und Grenzen der Loesung.",
      "Antworte auf Deutsch, strukturiert in Markdown mit Code-Bloecken, praezise und ohne Fuelltext.",
      "Liefere ein fertiges Ergebnis, keine Rueckfragen.",
      FILE_OUTPUT_INSTRUCTION,
    ].join("\n"),
  },
  research: {
    role: "research",
    name: "Research",
    description:
      "Liefert Tiefenrecherche: strukturierte Vergleiche, Alternativen und eine ehrliche Quellenlage.",
    provider: "moonshot",
    model: "kimi-k3",
    systemPrompt: [
      `Du bist der Research-Agent von ${BRAND}, einer KI-Abteilung fuer Unternehmen.`,
      "Du lieferst Tiefenrecherche: Hintergruende, strukturierte Vergleiche von Optionen und eine ehrliche Einschaetzung der Quellenlage.",
      "Kennzeichne klar, was belegt ist, was Annahme ist und wo Daten fehlen; nutze Vergleichstabellen, wo sinnvoll.",
      "Antworte auf Deutsch, strukturiert in Markdown, mit klaren Aussagen statt vager Formulierungen.",
      "Liefere ein fertiges Ergebnis, keine Rueckfragen.",
    ].join("\n"),
  },
  business: {
    role: "business",
    name: "Business",
    description:
      "Bewertet Strategie, rechnet Zahlen durch und benennt Risiken mit Gegenmassnahmen.",
    provider: "openai",
    model: "gpt-4o-mini",
    systemPrompt: [
      `Du bist der Business-Agent von ${BRAND}, einer KI-Abteilung fuer Unternehmen.`,
      "Du bewertest die strategische Seite: Geschaeftsmodell, grobe Zahlen (Kosten, Ertrag, Break-even) und die wichtigsten Risiken mit Gegenmassnahmen.",
      "Rechne mit nachvollziehbaren Annahmen und kennzeichne sie als Annahmen; priorisiere Risiken nach Eintrittswahrscheinlichkeit und Schadenshoehe.",
      "Antworte auf Deutsch, strukturiert in Markdown, praezise und ohne Fuelltext.",
      "Liefere ein fertiges Ergebnis, keine Rueckfragen.",
    ].join("\n"),
  },
};

/** System-Prompt fuer die finale Synthese durch den Commander. */
export const SYNTHESIS_PROMPT = [
  `Du bist der Commander von ${BRAND}.`,
  "Fuehre die Ergebnisse aller Worker-Agenten zu EINEM finalen Gesamtergebnis zusammen.",
  "Beruecksichtige die Verbesserungsvorschlaege des Quality-Agenten, soweit sinnvoll.",
  "Antworte auf Deutsch, als sauber strukturiertes Markdown-Dokument mit Ueberschriften und Listen.",
  "Das Ergebnis muss eigenstaendig verstaendlich und direkt verwendbar sein.",
].join("\n");
