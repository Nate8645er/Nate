/**
 * Orchestrator: fuehrt eine Mission durch das Agenten-Team.
 *
 * Ablauf:
 *   1. Commander plant (zerlegt das Ziel in zwei Teilaufgaben)
 *   2. Builder + Analyst arbeiten PARALLEL (Promise.all)
 *   3. Quality bewertet beide Ergebnisse (Score 0-100 + Verbesserungen)
 *   4. Commander synthetisiert das finale Ergebnis
 *
 * Alle Zwischenstaende werden ueber emit() als AgentEvents gestreamt.
 *
 * Robustheit: Fehlt fuer einen Provider der API-Key oder scheitert ein
 * Call endgueltig (nach Retry), springt pro Phase ein deterministischer
 * DEMO-FALLBACK ein (lib/agents/demo.ts). Eine Mission laeuft dadurch
 * IMMER bis zum final-Event durch. Zusaetzlich haengt ueber der gesamten
 * Mission ein harter Timeout, der im Grenzfall sauber mit einem
 * final-Event abschliesst.
 */

import {
  demoAnalystOutput,
  demoBuilderOutput,
  demoPlan,
  demoQualityReport,
  demoSynthesis,
} from "./demo";
import { callLLM, hasApiKey } from "./providers";
import { AGENTS, SYNTHESIS_PROMPT } from "./team";
import type {
  AgentConfig,
  AgentRole,
  ChatMessage,
  EmitFn,
  MissionContext,
  QualityReport,
  TaskPlan,
} from "./types";

/** Harter Deckel ueber der Gesamtmission (Route erlaubt 300s). */
const MISSION_TIMEOUT_MS = 270_000;

/**
 * Kontextzeile aus dem Branchen-Onboarding fuer den Commander-System-Prompt
 * (Planung + Synthese). Ohne Kontext bleibt der Prompt unveraendert.
 */
function contextLine(context?: MissionContext): string {
  if (!context) return "";
  return (
    `\nDer Kunde ist ein Unternehmen aus der Branche "${context.branche}" ` +
    `mit ${context.groesse} Mitarbeitenden – passe Plan und Sprache darauf an.`
  );
}

export async function runMission(
  goal: string,
  emit: EmitFn,
  context?: MissionContext,
): Promise<void> {
  const trimmedGoal = goal.trim();
  if (!trimmedGoal) {
    emit({ type: "error", agent: null, message: "Kein Missionsziel angegeben." });
    return;
  }

  // Nach Missionsende (regulaer oder Timeout) keine Events mehr durchlassen,
  // damit ein noch laufender Rest-Task den Stream nicht "wiederbelebt".
  let finished = false;
  const guardedEmit: EmitFn = (event) => {
    if (!finished) emit(event);
  };

  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<"timeout">((resolve) => {
    timer = setTimeout(() => resolve("timeout"), MISSION_TIMEOUT_MS);
  });

  try {
    const outcome = await Promise.race([
      runMissionPhases(trimmedGoal, guardedEmit, context).then(() => "done" as const),
      timeout,
    ]);

    if (outcome === "timeout") {
      // Sauber abschliessen: alle Agenten auf "done", Demo-Ergebnis liefern.
      for (const role of Object.keys(AGENTS) as AgentRole[]) {
        guardedEmit(status(role, "done", "Zeitlimit erreicht – Demo-Abschluss"));
      }
      guardedEmit({
        type: "error",
        agent: null,
        message: "Zeitlimit der Mission erreicht – Ergebnis wurde im Demo-Modus abgeschlossen.",
      });
      guardedEmit({ type: "final", content: demoSynthesis(trimmedGoal, "") });
    }
  } finally {
    finished = true;
    clearTimeout(timer);
  }
}

/* ----------------------------- Missionsphasen ----------------------------- */

async function runMissionPhases(
  goal: string,
  emit: EmitFn,
  context?: MissionContext,
): Promise<void> {
  // 1. Commander plant
  emit(status("commander", "working", "Commander plant die Mission …"));
  const planCall = await callAgent(
    AGENTS.commander,
    AGENTS.commander.systemPrompt + contextLine(context),
    [{ role: "user", content: `Mission: ${goal}` }],
    () => JSON.stringify(demoPlan(goal)),
    emit,
  );
  const plan = parsePlan(planCall.text, goal);
  emit(status("commander", "done", planCall.demo ? "Plan erstellt (Demo-Modus)" : "Plan erstellt"));
  emit({
    type: "output",
    agent: "commander",
    content: [
      `**Teilaufgabe Builder:** ${plan.builderTask}`,
      `**Teilaufgabe Analyst:** ${plan.analystTask}`,
    ].join("\n\n"),
  });

  // 2. Builder + Analyst parallel
  emit(status("builder", "working", "Builder arbeitet …"));
  emit(status("analyst", "working", "Analyst recherchiert …"));
  const [builderCall, analystCall] = await Promise.all([
    callAgent(
      AGENTS.builder,
      AGENTS.builder.systemPrompt,
      workerMessages(goal, plan.builderTask),
      () => demoBuilderOutput(goal, plan.builderTask),
      emit,
    ),
    callAgent(
      AGENTS.analyst,
      AGENTS.analyst.systemPrompt,
      workerMessages(goal, plan.analystTask),
      () => demoAnalystOutput(goal, plan.analystTask),
      emit,
    ),
  ]);

  const workerOutputs: string[] = [];
  for (const { agent, call } of [
    { agent: AGENTS.builder, call: builderCall },
    { agent: AGENTS.analyst, call: analystCall },
  ]) {
    emit(status(agent.role, "done", call.demo ? `${agent.name} fertig (Demo-Modus)` : `${agent.name} fertig`));
    emit({ type: "output", agent: agent.role, content: call.text });
    workerOutputs.push(`## Ergebnis ${agent.name}\n\n${call.text}`);
  }
  const combined = workerOutputs.join("\n\n");

  // 3. Quality prueft
  emit(status("quality", "working", "Quality prueft die Ergebnisse …"));
  const qualityCall = await callAgent(
    AGENTS.quality,
    AGENTS.quality.systemPrompt,
    [
      {
        role: "user",
        content: `Mission: ${goal}\n\nZu bewertende Ergebnisse:\n\n${combined}`,
      },
    ],
    () => JSON.stringify(demoQualityReport(combined)),
    emit,
  );
  const quality = parseQuality(qualityCall.text) ?? demoQualityReport(combined);
  emit(
    status(
      "quality",
      "done",
      qualityCall.demo ? `Score: ${quality.score}/100 (Demo-Modus)` : `Score: ${quality.score}/100`,
    ),
  );
  emit({ type: "score", score: quality.score, improvements: quality.improvements });
  const improvementNotes = quality.improvements.length
    ? `\n\nVerbesserungsvorschlaege des Quality-Agenten:\n- ${quality.improvements.join("\n- ")}`
    : "";

  // 4. Commander-Synthese
  emit(status("commander", "working", "Commander erstellt das Gesamtergebnis …"));
  const synthesisCall = await callAgent(
    AGENTS.commander,
    SYNTHESIS_PROMPT + contextLine(context),
    [
      {
        role: "user",
        content: `Mission: ${goal}\n\n${combined}${improvementNotes}`,
      },
    ],
    () => demoSynthesis(goal, combined),
    emit,
  );
  emit(
    status(
      "commander",
      "done",
      synthesisCall.demo ? "Mission abgeschlossen (Demo-Modus)" : "Mission abgeschlossen",
    ),
  );
  emit({ type: "final", content: synthesisCall.text });
}

/* ----------------------------- interne Helfer ----------------------------- */

interface AgentCall {
  text: string;
  /** true, wenn die Antwort aus dem Demo-Fallback stammt */
  demo: boolean;
}

/**
 * Ruft einen Agenten auf und degradiert bei fehlendem Key oder
 * endgueltigem Fehler in den Demo-Fallback – wirft nie.
 */
async function callAgent(
  agent: AgentConfig,
  system: string,
  messages: ChatMessage[],
  demoFallback: () => string,
  emit: EmitFn,
): Promise<AgentCall> {
  if (!hasApiKey(agent.provider)) {
    emit(status(agent.role, "working", `Demo-Modus: kein API-Key fuer ${agent.provider}`));
    return { text: demoFallback(), demo: true };
  }
  const result = await callLLM(agent.provider, agent.model, system, messages);
  if (result.ok) return { text: result.text, demo: false };
  emit(status(agent.role, "working", `Demo-Modus: ${agent.provider} nicht erreichbar`));
  return { text: demoFallback(), demo: true };
}

function status(agent: AgentRole, s: "idle" | "working" | "done" | "error", message: string) {
  return { type: "status" as const, agent, status: s, message };
}

function workerMessages(goal: string, task: string): ChatMessage[] {
  return [
    {
      role: "user",
      content: `Gesamtmission: ${goal}\n\nDeine Teilaufgabe: ${task}`,
    },
  ];
}

/** Extrahiert den TaskPlan; unbrauchbares JSON faellt auf den Demo-Plan zurueck. */
function parsePlan(text: string, goal: string): TaskPlan {
  const parsed = parseJsonObject(text);
  if (
    parsed &&
    typeof parsed.builderTask === "string" &&
    typeof parsed.analystTask === "string" &&
    parsed.builderTask.trim() &&
    parsed.analystTask.trim()
  ) {
    return {
      builderTask: parsed.builderTask.trim(),
      analystTask: parsed.analystTask.trim(),
    };
  }
  return demoPlan(goal);
}

/** Extrahiert den QualityReport oder null bei unbrauchbarem JSON. */
function parseQuality(text: string): QualityReport | null {
  const parsed = parseJsonObject(text);
  const score = typeof parsed?.score === "number" ? parsed.score : NaN;
  if (!Number.isFinite(score)) return null;
  const improvements = Array.isArray(parsed?.improvements)
    ? parsed.improvements.filter((i): i is string => typeof i === "string")
    : [];
  return { score: clamp(Math.round(score), 0, 100), improvements };
}

/**
 * Robustes JSON-Parsing: toleriert Markdown-Codeblocks und
 * umgebenden Text, indem das erste {...}-Objekt extrahiert wird.
 */
function parseJsonObject(text: string): Record<string, unknown> | null {
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start === -1 || end <= start) return null;
  try {
    const parsed: unknown = JSON.parse(text.slice(start, end + 1));
    return typeof parsed === "object" && parsed !== null
      ? (parsed as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

function clamp(n: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, n));
}
