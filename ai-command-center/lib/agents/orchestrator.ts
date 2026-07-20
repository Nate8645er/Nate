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
 * Faellt ein Worker aus, laeuft die Mission mit dem verbleibenden
 * Ergebnis weiter; nur ein Totalausfall bricht ab.
 */

import { callLLM } from "./providers";
import { AGENTS, SYNTHESIS_PROMPT } from "./team";
import type { AgentConfig, EmitFn, QualityReport, TaskPlan } from "./types";

export async function runMission(goal: string, emit: EmitFn): Promise<void> {
  const trimmedGoal = goal.trim();
  if (!trimmedGoal) {
    emit({ type: "error", agent: null, message: "Kein Missionsziel angegeben." });
    return;
  }

  // 1. Commander plant
  emit(status("commander", "working", "Commander plant die Mission …"));
  const plan = await planMission(trimmedGoal);
  if (!plan.ok) {
    emit(status("commander", "error", "Planung fehlgeschlagen"));
    emit({ type: "error", agent: "commander", message: plan.error });
    return;
  }
  emit(status("commander", "done", "Plan erstellt"));
  emit({
    type: "output",
    agent: "commander",
    content: [
      `**Teilaufgabe Builder:** ${plan.value.builderTask}`,
      `**Teilaufgabe Analyst:** ${plan.value.analystTask}`,
    ].join("\n\n"),
  });

  // 2. Builder + Analyst parallel
  emit(status("builder", "working", "Builder arbeitet …"));
  emit(status("analyst", "working", "Analyst recherchiert …"));
  const [builderResult, analystResult] = await Promise.all([
    runWorker(AGENTS.builder, trimmedGoal, plan.value.builderTask),
    runWorker(AGENTS.analyst, trimmedGoal, plan.value.analystTask),
  ]);

  const workerOutputs: string[] = [];
  for (const { agent, result } of [
    { agent: AGENTS.builder, result: builderResult },
    { agent: AGENTS.analyst, result: analystResult },
  ]) {
    if (result.ok) {
      emit(status(agent.role, "done", `${agent.name} fertig`));
      emit({ type: "output", agent: agent.role, content: result.text });
      workerOutputs.push(`## Ergebnis ${agent.name}\n\n${result.text}`);
    } else {
      emit(status(agent.role, "error", `${agent.name} ausgefallen`));
      emit({ type: "error", agent: agent.role, message: result.error });
    }
  }

  if (workerOutputs.length === 0) {
    emit({
      type: "error",
      agent: null,
      message: "Beide Worker sind ausgefallen – Mission abgebrochen.",
    });
    return;
  }

  const combined = workerOutputs.join("\n\n");

  // 3. Quality prueft
  emit(status("quality", "working", "Quality prueft die Ergebnisse …"));
  const quality = await reviewQuality(trimmedGoal, combined);
  let improvementNotes = "";
  if (quality.ok) {
    emit(status("quality", "done", `Score: ${quality.value.score}/100`));
    emit({
      type: "score",
      score: quality.value.score,
      improvements: quality.value.improvements,
    });
    improvementNotes = quality.value.improvements.length
      ? `\n\nVerbesserungsvorschlaege des Quality-Agenten:\n- ${quality.value.improvements.join("\n- ")}`
      : "";
  } else {
    // Quality-Ausfall ist nicht fatal: Synthese laeuft ohne Review weiter.
    emit(status("quality", "error", "Quality-Pruefung fehlgeschlagen"));
    emit({ type: "error", agent: "quality", message: quality.error });
  }

  // 4. Commander-Synthese
  emit(status("commander", "working", "Commander erstellt das Gesamtergebnis …"));
  const synthesis = await callLLM(
    AGENTS.commander.provider,
    AGENTS.commander.model,
    SYNTHESIS_PROMPT,
    [
      {
        role: "user",
        content: `Mission: ${trimmedGoal}\n\n${combined}${improvementNotes}`,
      },
    ],
  );

  if (!synthesis.ok) {
    emit(status("commander", "error", "Synthese fehlgeschlagen"));
    emit({ type: "error", agent: "commander", message: synthesis.error });
    return;
  }
  emit(status("commander", "done", "Mission abgeschlossen"));
  emit({ type: "final", content: synthesis.text });
}

/* ----------------------------- interne Helfer ----------------------------- */

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function status(
  agent: AgentConfig["role"],
  s: "idle" | "working" | "done" | "error",
  message: string,
) {
  return { type: "status" as const, agent, status: s, message };
}

/** Schritt 1: Commander erzeugt den TaskPlan (JSON). */
async function planMission(goal: string): Promise<Result<TaskPlan>> {
  const { provider, model, systemPrompt } = AGENTS.commander;
  const result = await callLLM(provider, model, systemPrompt, [
    { role: "user", content: `Mission: ${goal}` },
  ]);
  if (!result.ok) return { ok: false, error: result.error };

  const parsed = parseJsonObject(result.text);
  if (
    parsed &&
    typeof parsed.builderTask === "string" &&
    typeof parsed.analystTask === "string" &&
    parsed.builderTask.trim() &&
    parsed.analystTask.trim()
  ) {
    return {
      ok: true,
      value: {
        builderTask: parsed.builderTask.trim(),
        analystTask: parsed.analystTask.trim(),
      },
    };
  }

  // Fallback: Wenn der Commander kein valides JSON liefert, arbeiten
  // beide Worker mit dem Originalziel weiter, statt die Mission abzubrechen.
  return {
    ok: true,
    value: {
      builderTask: `Erstelle ein konkretes, verwendbares Ergebnis fuer: ${goal}`,
      analystTask: `Analysiere Kontext, Zielgruppe, Chancen und Risiken fuer: ${goal}`,
    },
  };
}

/** Schritt 2: Ein Worker (Builder oder Analyst) bearbeitet seine Teilaufgabe. */
function runWorker(agent: AgentConfig, goal: string, task: string) {
  return callLLM(agent.provider, agent.model, agent.systemPrompt, [
    {
      role: "user",
      content: `Gesamtmission: ${goal}\n\nDeine Teilaufgabe: ${task}`,
    },
  ]);
}

/** Schritt 3: Quality bewertet die kombinierten Ergebnisse. */
async function reviewQuality(
  goal: string,
  combinedOutputs: string,
): Promise<Result<QualityReport>> {
  const { provider, model, systemPrompt } = AGENTS.quality;
  const result = await callLLM(provider, model, systemPrompt, [
    {
      role: "user",
      content: `Mission: ${goal}\n\nZu bewertende Ergebnisse:\n\n${combinedOutputs}`,
    },
  ]);
  if (!result.ok) return { ok: false, error: result.error };

  const parsed = parseJsonObject(result.text);
  const score = typeof parsed?.score === "number" ? parsed.score : NaN;
  if (!Number.isFinite(score)) {
    return {
      ok: false,
      error: "Quality-Agent lieferte kein valides JSON mit Score.",
    };
  }
  const improvements = Array.isArray(parsed?.improvements)
    ? parsed.improvements.filter((i): i is string => typeof i === "string")
    : [];
  return {
    ok: true,
    value: { score: clamp(Math.round(score), 0, 100), improvements },
  };
}

/**
 * Robustes JSON-Parsing: toleriert Markdown-Codeblocks und
 * umgebenden Text, indem das erste {...}-Objekt extrahiert wird.
 */
function parseJsonObject(
  text: string,
): Record<string, unknown> | null {
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
