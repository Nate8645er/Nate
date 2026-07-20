/**
 * Zentrale Typdefinitionen fuer das Agenten-System.
 *
 * Alle Module (providers, team, orchestrator, API-Route, Dashboard)
 * arbeiten ausschliesslich gegen diese Typen, damit Phase 2/3
 * (Persistenz, Billing-Limits pro Plan) ohne Umbau andocken koennen.
 */

/** Unterstuetzte LLM-Provider. */
export type Provider = "anthropic" | "openai" | "moonshot";

/** Abo-Plaene. FREE gilt ohne (gueltiges) Lizenz-Token. */
export type PlanId = "FREE" | "STARTER" | "PROFESSIONAL" | "BUSINESS";

/**
 * Unternehmenskontext aus dem Branchen-Onboarding.
 * Wird optional mit POST /api/mission gesendet und vom Orchestrator
 * als Kontextzeile an den Commander-System-Prompt gehaengt.
 */
export interface MissionContext {
  branche: string;
  groesse: string;
}

/** Rollen der Agenten im Team (Kern + plan-abhaengige Zusatz-Worker). */
export type AgentRole =
  | "commander"
  | "builder"
  | "analyst"
  | "quality"
  | "marketing"
  | "coding"
  | "research"
  | "business";

/** Ausfuehrende Worker-Rollen (alle ausser Commander und Quality). */
export type WorkerRole = Exclude<AgentRole, "commander" | "quality">;

/** Konfiguration eines einzelnen Agenten. */
export interface AgentConfig {
  role: AgentRole;
  /** Anzeigename im UI, z. B. "Commander" */
  name: string;
  /** Kurzbeschreibung der Funktion (fuer Landing Page + Dashboard) */
  description: string;
  provider: Provider;
  model: string;
  /** Deutscher System-Prompt des Agenten */
  systemPrompt: string;
}

/**
 * Vom Commander erzeugter Plan: je eine Teilaufgabe pro aktivem Worker.
 * Welche Worker aktiv sind, bestimmt der Abo-Plan (WORKERS_BY_PLAN in team.ts).
 */
export type TaskPlan = Partial<Record<WorkerRole, string>>;

/** Ergebnis der Quality-Pruefung. */
export interface QualityReport {
  /** Gesamtbewertung 0-100 */
  score: number;
  /** Konkrete Verbesserungsvorschlaege */
  improvements: string[];
}

/**
 * Discriminated Union fuer Server-Sent Events der Mission-API.
 * Das Dashboard rendert den Live-Status ausschliesslich aus diesen Events.
 */
export type AgentEvent =
  /** Statuswechsel eines Agenten (z. B. "plant", "arbeitet", "fertig") */
  | { type: "status"; agent: AgentRole; status: AgentStatus; message: string }
  /** Fertige Text-Ausgabe eines Agenten */
  | { type: "output"; agent: AgentRole; content: string }
  /** Quality-Score inkl. Verbesserungen */
  | { type: "score"; score: number; improvements: string[] }
  /** Finales, synthetisiertes Ergebnis (Markdown) */
  | { type: "final"; content: string }
  /**
   * Signiertes Usage-Token (stateless Tageszaehler). Der Client haelt das
   * Token in localStorage und sendet es beim naechsten Start als Header
   * "x-acc-usage" zurueck; der Server signiert es bei jeder Antwort neu.
   */
  | { type: "usage"; token: string; used: number; limit: number; plan: PlanId }
  /** Fehler eines Agenten oder der Pipeline */
  | { type: "error"; agent: AgentRole | null; message: string };

export type AgentStatus = "idle" | "working" | "done" | "error";

/** Callback, ueber den der Orchestrator Events an den SSE-Stream sendet. */
export type EmitFn = (event: AgentEvent) => void;

/** Einzelne Chat-Nachricht im providerneutralen Format. */
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

/** Ergebnis eines LLM-Aufrufs: entweder Text oder ein beschriebener Fehler. */
export type LLMResult =
  | { ok: true; text: string }
  | { ok: false; error: string };
