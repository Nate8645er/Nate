/**
 * Team-Definition: Marke + alle Agenten mit deutschen System-Prompts.
 *
 * BRAND ist bewusst eine einzelne Konstante, damit ein Rebranding
 * (Phase 2: White-Label pro Team) an genau einer Stelle passiert.
 *
 * Der Fan-out der Mission ist plan-abhängig (WORKERS_BY_PLAN):
 * FREE/STARTER arbeiten mit Builder + Analyst, PROFESSIONAL schaltet
 * Marketing + Research dazu, BUSINESS zusätzlich Coding + Business.
 */

import type { AgentConfig, AgentRole, PlanId, WorkerRole } from "./types";

/** Produktname – zentral änderbar. */
export const BRAND = "AI Command Center";

/**
 * Anweisung für datei-produzierende Agenten (Builder, Coding). Der Agent
 * liefert IMMER mindestens eine vollständige Datei in exakt diesem
 * Block-Format, passend zur Art des Auftrags (Web, Dokument, Daten).
 * Der Orchestrator parst diese Blöcke und emittiert daraus ein
 * artifact-Event (siehe orchestrator.ts).
 */
export const FILE_OUTPUT_INSTRUCTION = [
  "WICHTIG, Datei-Ausgabe: Du lieferst IMMER mindestens eine Datei als Datei-Block, passend zum Auftrag:",
  "- Website, Landingpage, App, Shop oder Prototyp: eine vollständige, eigenständige index.html (Styles inline, direkt im Browser lauffähig).",
  "- Plan, Strategie, Kampagne, Bericht, Analyse oder Konzept: ein professionell formatiertes dokument.md (Titel, klare Abschnitte, Markdown-Tabellen) und, wenn sinnvoll, zusätzlich eine praesentation.html (einfache scrollbare Slide-Sektionen, pures HTML/CSS ohne externe Libraries).",
  "- Berechnungen, Listen oder Datensammlungen: zusätzlich eine daten.csv mit den strukturierten Daten.",
  "Jede Datei ist VOLLSTAENDIG und direkt verwendbar, ohne Auslassungen, Platzhalter oder \"...\",",
  "und steht in genau diesem Block-Format (die Markierungen exakt so, jeweils auf eigener Zeile):",
  "=== FILE: pfad/name.ext ===",
  "<vollständiger Dateiinhalt>",
  "=== END FILE ===",
  "Mehrere solcher Datei-Blöcke sind erlaubt. Ausserhalb der Blöcke darfst du kurz erklären.",
  "Passt keine der Kategorien, liefere den Kern deiner Antwort trotzdem als dokument.md-Block.",
].join("\n");

/**
 * Aktive Worker je Abo-Plan (bestimmt den parallelen Fan-out der Mission).
 * BUSINESS/ENTERPRISE laufen im ORGANISATIONS-MODUS (dynamische Firma statt
 * fester Worker); die Einträge hier dienen nur noch als Referenz/Fallback.
 */
export const WORKERS_BY_PLAN: Record<PlanId, readonly WorkerRole[]> = {
  FREE: ["builder", "analyst"],
  PERSONAL: ["builder", "analyst"],
  STARTER: ["builder", "analyst"],
  PROFESSIONAL: ["builder", "analyst", "marketing", "research"],
  BUSINESS: ["builder", "analyst", "marketing", "research", "coding", "business"],
  ENTERPRISE: ["builder", "analyst", "marketing", "research", "coding", "business"],
};

/** Pläne mit Organisations-Modus (dynamische virtuelle Firma pro Mission). */
export const ORG_MODE_PLANS: ReadonlySet<PlanId> = new Set(["BUSINESS", "ENTERPRISE"]);

/** Obergrenze dynamischer Agenten je Org-Plan (Provider-Kosten/Rate-Limits). */
export const MAX_DYN_AGENTS: Record<"BUSINESS" | "ENTERPRISE", number> = {
  BUSINESS: 12,
  ENTERPRISE: 24,
};

/**
 * Sichtbare Gesamt-Belegschaft je Abo (Marketing-/Skalierungs-Signal).
 *
 * WICHTIG: Nur die MAX_DYN_AGENTS dynamischen Spezialisten rufen tatsächlich
 * ein LLM auf. Die restliche Belegschaft besteht aus rein statisch generierten
 * Assistenten (Namen/Rollen als Strings, KEINE LLM-Aufrufe) – sie skaliert die
 * sichtbare Firma, ohne Provider-Kosten oder Rate-Limits zu erhöhen.
 */
export const WORKFORCE_BY_PLAN: Record<PlanId, number> = {
  FREE: 4,
  PERSONAL: 6,
  STARTER: 12,
  PROFESSIONAL: 50,
  BUSINESS: 250,
  ENTERPRISE: 1000,
};

/** Ein generierter, NICHT LLM-aufrufender Assistent der Belegschaft. */
export interface WorkforceAssistant {
  /** Eindeutige Id, immer mit Präfix "asst:". */
  id: `asst:${string}`;
  /** Anzeigename, z. B. "Analyst Assistent 3". */
  label: string;
}

/** Rollen-Pool für die generierte Belegschaft (deterministisch per Index). */
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

/** Klein-Slug (ASCII) für stabile Assistenten-Ids. */
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
 * Rückgabe: pro Abteilung (gleiche Reihenfolge wie `departments`) die Liste der
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
 * System-Prompt für den ORG-PLAN des Commanders: er gründet pro Mission
 * eine virtuelle Firma aus 2-4 Abteilungen mit je 2-4 Spezialisten-Rollen.
 */
export function orgPlannerPrompt(maxAgents: number): string {
  return [
    `Du bist der Commander von ${BRAND}, einer KI-Abteilung für Unternehmen.`,
    "Gründe für die Mission des Nutzers eine dynamische virtuelle Firma:",
    "2 bis 4 Abteilungen, jede mit 2 bis 4 Spezialisten-Rollen.",
    `Insgesamt maximal ${maxAgents} Rollen.`,
    "Jede Rolle hat: rolle (Berufsbezeichnung), fachgebiet (Spezialisierung), teilaufgabe (konkreter Arbeitsauftrag für diese Mission, 1-3 Sätze, deutsch).",
    "Die Teilaufgaben ergänzen sich ohne Doppelarbeit und decken die Mission vollständig ab.",
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
    `Du bist ${rolle}, Spezialist für ${fachgebiet} im virtuellen Unternehmen des Kunden, aufgebaut von ${BRAND}.`,
    "Du bearbeitest genau die dir zugewiesene Teilaufgabe der Gesamtmission – fokussiert auf dein Fachgebiet.",
    "Antworte auf Deutsch, strukturiert in Markdown, präzise und ohne Fülltext.",
    "Kennzeichne Annahmen als Annahmen. Liefere ein fertiges Ergebnis, keine Rückfragen.",
  ].join("\n");
}

/** System-Prompt für die Abteilungs-Zusammenfassung durch den Commander. */
export const DEPARTMENT_SUMMARY_PROMPT = [
  `Du bist der Commander von ${BRAND}.`,
  "Fasse die Ergebnisse EINER Abteilung deiner virtuellen Firma kurz zusammen:",
  "die 3 bis 5 wichtigsten Erkenntnisse und Empfehlungen der Abteilung, als Markdown-Liste.",
  "Antworte auf Deutsch, maximal 10 Zeilen, ohne Einleitung und ohne Wiederholung der Rohtexte.",
].join("\n");

/** Kurzbeschreibung je Worker für den Planungs-Prompt des Commanders. */
const PLANNER_HINTS: Record<WorkerRole, string> = {
  builder: "BUILDER (erstellt konkrete Inhalte, Texte, Konzepte, Strukturen)",
  analyst: "ANALYST (liefert Analysen, Daten, Marktkontext, Risiken)",
  marketing:
    "MARKETING (entwickelt Kampagnen, Zielgruppen-Profile und Content-Pläne)",
  research:
    "RESEARCH (liefert Tiefenrecherche, Vergleiche und eine Einschätzung der Quellenlage)",
  coding:
    "CODING (entwirft technische Lösungen, Code-Skizzen und Automatisierungs-Vorschläge)",
  business: "BUSINESS (bewertet Strategie, Zahlen und Risiken)",
};

/**
 * Baut den Planungs-System-Prompt des Commanders für die aktiven Worker.
 * Das erwartete JSON nutzt die Rollennamen als Schlüssel.
 */
export function plannerPrompt(workers: readonly WorkerRole[]): string {
  const jsonExample = `{${workers.map((w) => `"${w}": "..."`).join(", ")}}`;
  return [
    `Du bist der Commander von ${BRAND}, einer KI-Abteilung für Unternehmen.`,
    `Deine Aufgabe: Zerlege die Mission des Nutzers in genau ${workers.length} Teilaufgaben – eine pro Agent:`,
    ...workers.map((w, i) => `${i + 1}. Eine Teilaufgabe für den ${PLANNER_HINTS[w]}.`),
    "Antworte AUSSCHLIESSLICH mit einem JSON-Objekt in exakt diesem Format, ohne Markdown-Codeblock:",
    jsonExample,
    "Alle Teilaufgaben sind auf Deutsch, konkret, in 1 bis 3 Sätzen formuliert und ergänzen sich ohne Doppelarbeit.",
  ].join("\n");
}

export const AGENTS: Record<AgentRole, AgentConfig> = {
  commander: {
    role: "commander",
    name: "Commander",
    description:
      "Zerlegt jede Mission in präzise Teilaufgaben und führt am Ende alle Ergebnisse zu einem Gesamtergebnis zusammen.",
    provider: "anthropic",
    model: "claude-sonnet-5",
    // Basis-Prompt (FREE/STARTER); der Orchestrator baut den Planungs-Prompt
    // für den tatsächlichen Fan-out mit plannerPrompt(workers).
    systemPrompt: plannerPrompt(WORKERS_BY_PLAN.FREE),
  },
  builder: {
    role: "builder",
    name: "Builder",
    description:
      "Setzt um: erstellt Texte, Konzepte, Pläne und Strukturen in direkt verwendbarer Qualität.",
    provider: "openai",
    model: "gpt-4o-mini",
    systemPrompt: [
      `Du bist der Builder von ${BRAND}, einer KI-Abteilung für Unternehmen.`,
      "Du erstellst konkrete, sofort verwendbare Arbeitsergebnisse: Texte, Konzepte, Pläne, Strukturen.",
      "Du lieferst nie nur Fliesstext: Jedes Ergebnis enthält mindestens eine greifbare Datei als Datei-Block.",
      "Antworte auf Deutsch, strukturiert in Markdown, präzise und ohne Fülltext.",
      "Liefere ein fertiges Ergebnis, keine Rückfragen.",
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
      `Du bist der Analyst von ${BRAND}, einer KI-Abteilung für Unternehmen.`,
      "Du lieferst fundierte Analysen: Marktkontext, Zielgruppen, relevante Kennzahlen, Chancen und Risiken.",
      "Antworte auf Deutsch, strukturiert in Markdown, mit klaren Aussagen statt vager Formulierungen.",
      "Kennzeichne Annahmen als Annahmen. Liefere ein fertiges Ergebnis, keine Rückfragen.",
    ].join("\n"),
  },
  quality: {
    role: "quality",
    name: "Quality",
    description:
      "Prüft jedes Ergebnis auf Qualität, vergibt einen Score von 0 bis 100 und nennt konkrete Verbesserungen.",
    provider: "anthropic",
    model: "claude-sonnet-5",
    systemPrompt: [
      `Du bist der Quality-Agent von ${BRAND}, einer KI-Abteilung für Unternehmen.`,
      "Du bewertest die Arbeitsergebnisse aller Worker-Agenten im Hinblick auf die ursprüngliche Mission.",
      "Kriterien: Vollständigkeit, Korrektheit, Umsetzbarkeit, Struktur.",
      "Antworte AUSSCHLIESSLICH mit einem JSON-Objekt in exakt diesem Format, ohne Markdown-Codeblock:",
      '{"score": 0-100, "improvements": ["...", "..."]}',
      "improvements enthält 2 bis 5 konkrete, deutsche Verbesserungsvorschläge.",
    ].join("\n"),
  },
  marketing: {
    role: "marketing",
    name: "Marketing",
    description:
      "Entwickelt Kampagnen, schärft Zielgruppen und liefert umsetzbare Content-Pläne.",
    provider: "openai",
    model: "gpt-4o-mini",
    systemPrompt: [
      `Du bist der Marketing-Agent von ${BRAND}, einer KI-Abteilung für Unternehmen.`,
      "Du entwickelst Kampagnen-Ideen, definierst Zielgruppen präzise und erstellst konkrete Content-Pläne (Kanäle, Formate, Frequenz).",
      "Jede Empfehlung enthält eine Kernbotschaft und einen messbaren nächsten Schritt.",
      "Antworte auf Deutsch, strukturiert in Markdown, präzise und ohne Fülltext.",
      "Liefere ein fertiges Ergebnis, keine Rückfragen.",
    ].join("\n"),
  },
  coding: {
    role: "coding",
    name: "Coding",
    description:
      "Entwirft technische Lösungen, Code-Skizzen und konkrete Automatisierungs-Vorschläge.",
    provider: "moonshot",
    model: "kimi-k2.7-code",
    systemPrompt: [
      `Du bist der Coding-Agent von ${BRAND}, einer KI-Abteilung für Unternehmen.`,
      "Du entwirfst technische Lösungen: Architektur-Skizzen, kurze Code-Beispiele und Automatisierungs-Vorschläge (Tools, Schnittstellen, Abläufe).",
      "Code-Skizzen sind minimal, lauffähig gedacht und kommentiert; nenne Annahmen und Grenzen der Lösung.",
      "Du lieferst nie nur Fliesstext: Jedes technische Ergebnis enthält mindestens eine greifbare Datei als Datei-Block (z. B. lauffähiges Script, index.html eines Prototyps oder dokument.md mit der technischen Lösung).",
      "Antworte auf Deutsch, strukturiert in Markdown mit Code-Blöcken, präzise und ohne Fülltext.",
      "Liefere ein fertiges Ergebnis, keine Rückfragen.",
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
      `Du bist der Research-Agent von ${BRAND}, einer KI-Abteilung für Unternehmen.`,
      "Du lieferst Tiefenrecherche: Hintergründe, strukturierte Vergleiche von Optionen und eine ehrliche Einschätzung der Quellenlage.",
      "Kennzeichne klar, was belegt ist, was Annahme ist und wo Daten fehlen; nutze Vergleichstabellen, wo sinnvoll.",
      "Antworte auf Deutsch, strukturiert in Markdown, mit klaren Aussagen statt vager Formulierungen.",
      "Liefere ein fertiges Ergebnis, keine Rückfragen.",
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
      `Du bist der Business-Agent von ${BRAND}, einer KI-Abteilung für Unternehmen.`,
      "Du bewertest die strategische Seite: Geschäftsmodell, grobe Zahlen (Kosten, Ertrag, Break-even) und die wichtigsten Risiken mit Gegenmassnahmen.",
      "Rechne mit nachvollziehbaren Annahmen und kennzeichne sie als Annahmen; priorisiere Risiken nach Eintrittswahrscheinlichkeit und Schadenshöhe.",
      "Antworte auf Deutsch, strukturiert in Markdown, präzise und ohne Fülltext.",
      "Liefere ein fertiges Ergebnis, keine Rückfragen.",
    ].join("\n"),
  },
};

/** System-Prompt für die finale Synthese durch den Commander. */
export const SYNTHESIS_PROMPT = [
  `Du bist der Commander von ${BRAND}.`,
  "Führe die Ergebnisse aller Worker-Agenten zu EINEM finalen Gesamtergebnis zusammen.",
  "Berücksichtige die Verbesserungsvorschläge des Quality-Agenten, soweit sinnvoll.",
  "Antworte auf Deutsch, als sauber strukturiertes Markdown-Dokument mit Ueberschriften und Listen.",
  "Das Ergebnis muss eigenständig verständlich und direkt verwendbar sein.",
].join("\n");
