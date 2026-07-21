"use client";

/**
 * Autopilot / Workflow-Manager: wiederkehrende Aufträge, die die
 * KI-Belegschaft als Missionen abarbeitet.
 *
 * Ehrliche Funktionsweise (steht auch im UI): Workflows laufen, während
 * diese Seite geöffnet ist – jede Ausführung ist eine echte Mission über
 * /api/mission und zählt auf das Tageslimit. Vollautomatischer
 * Server-Betrieb (auch bei geschlossenem Browser) ist Teil des
 * Enterprise-Ausbaus.
 *
 * Datenhaltung: localStorage (acc-workflows), Lizenz-/Usage-Token werden
 * mit Dashboard und Chat geteilt.
 */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const WORKFLOWS_KEY = "acc-workflows";
const LICENSE_TOKEN_KEY = "acc-license-token";
const USAGE_TOKEN_KEY = "acc-usage-token";
const BRANCHE_KEY = "acc-branche";
const GROESSE_KEY = "acc-groesse";

type Frequenz = "manuell" | "taeglich" | "woechentlich";

interface Workflow {
  id: string;
  name: string;
  goal: string;
  frequenz: Frequenz;
  lastRun: number | null;
  lastScore: number | null;
  lastSummary: string | null;
}

type RunState = { status: "laeuft"; note: string } | { status: "fehler"; note: string } | null;

const FREQUENZ_LABEL: Record<Frequenz, string> = {
  manuell: "Manuell",
  taeglich: "Täglich",
  woechentlich: "Wöchentlich",
};

const VORLAGEN: { name: string; goal: string; frequenz: Frequenz }[] = [
  {
    name: "Social-Media-Woche",
    goal: "Erstelle einen Social-Media-Wochenplan mit 5 konkreten Post-Ideen inklusive Text-Entwürfen für unser Unternehmen.",
    frequenz: "woechentlich",
  },
  {
    name: "Tages-Angebotsidee",
    goal: "Entwickle eine konkrete Aktions- oder Angebotsidee für heute, inklusive Kurztext für Aushang und Social Media.",
    frequenz: "taeglich",
  },
  {
    name: "Wochenbericht Geschäftsleitung",
    goal: "Erstelle eine Vorlage für einen Wochenbericht an die Geschäftsleitung: Kennzahlen-Struktur, offene Punkte, Empfehlungen.",
    frequenz: "woechentlich",
  },
];

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [running, setRunning] = useState<Record<string, RunState>>({});
  const [name, setName] = useState("");
  const [goal, setGoal] = useState("");
  const [frequenz, setFrequenz] = useState<Frequenz>("woechentlich");
  const [formOpen, setFormOpen] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(WORKFLOWS_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Workflow[];
        if (Array.isArray(parsed)) setWorkflows(parsed);
      }
    } catch {
      /* defekter Storage => leer */
    }
  }, []);

  const persist = useCallback((next: Workflow[]) => {
    setWorkflows(next);
    try {
      localStorage.setItem(WORKFLOWS_KEY, JSON.stringify(next));
    } catch {
      /* Storage voll */
    }
  }, []);

  const addWorkflow = useCallback(
    (n: string, g: string, f: Frequenz) => {
      const wf: Workflow = {
        id: `w${Date.now().toString(36)}`,
        name: n.trim().slice(0, 60),
        goal: g.trim().slice(0, 2000),
        frequenz: f,
        lastRun: null,
        lastScore: null,
        lastSummary: null,
      };
      if (!wf.name || !wf.goal) return;
      persist([wf, ...workflows]);
      setName("");
      setGoal("");
      setFormOpen(false);
    },
    [workflows, persist],
  );

  const removeWorkflow = useCallback(
    (id: string) => persist(workflows.filter((w) => w.id !== id)),
    [workflows, persist],
  );

  /** Fällig = laut Frequenz seit letzter Ausführung überschritten. */
  const isDue = (w: Workflow): boolean => {
    if (w.frequenz === "manuell") return false;
    if (!w.lastRun) return true;
    const alter = Date.now() - w.lastRun;
    return w.frequenz === "taeglich" ? alter > 20 * 3600e3 : alter > 6.5 * 86400e3;
  };

  /** Führt einen Workflow als echte Mission aus (SSE lesen bis final). */
  const run = useCallback(
    async (wf: Workflow) => {
      setRunning((r) => ({ ...r, [wf.id]: { status: "laeuft", note: "Team arbeitet …" } }));
      try {
        const headers: Record<string, string> = { "content-type": "application/json" };
        try {
          const lic = localStorage.getItem(LICENSE_TOKEN_KEY);
          const use = localStorage.getItem(USAGE_TOKEN_KEY);
          if (lic) headers["x-acc-license"] = lic;
          if (use) headers["x-acc-usage"] = use;
        } catch {
          /* Storage nicht lesbar */
        }
        const context = {
          branche: safeGet(BRANCHE_KEY),
          groesse: safeGet(GROESSE_KEY),
        };
        const res = await fetch("/api/mission", {
          method: "POST",
          headers,
          body: JSON.stringify({ goal: wf.goal, context }),
        });
        if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let score: number | null = null;
        let finalText: string | null = null;
        let errorText: string | null = null;
        let artifactCount = 0;

        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? "";
          for (const part of parts) {
            const line = part.split("\n").find((l) => l.startsWith("data: "));
            if (!line) continue;
            try {
              const ev = JSON.parse(line.slice(6)) as {
                type: string;
                score?: number;
                content?: string;
                message?: string;
                token?: string;
                files?: unknown[];
                status?: string;
                label?: string;
                agent?: string;
              };
              if (ev.type === "usage" && ev.token) {
                try {
                  localStorage.setItem(USAGE_TOKEN_KEY, ev.token);
                } catch {
                  /* voll */
                }
              } else if (ev.type === "score" && typeof ev.score === "number") {
                score = ev.score;
              } else if (ev.type === "artifact" && Array.isArray(ev.files)) {
                artifactCount = ev.files.length;
              } else if (ev.type === "final" && typeof ev.content === "string") {
                finalText = ev.content;
              } else if (ev.type === "error" && typeof ev.message === "string") {
                errorText = ev.message;
              } else if (ev.type === "status" && ev.status === "working") {
                const wer = ev.label ?? ev.agent ?? "Team";
                setRunning((r) => ({
                  ...r,
                  [wf.id]: { status: "laeuft", note: `${wer} arbeitet …` },
                }));
              }
            } catch {
              /* kaputtes Event überspringen */
            }
          }
        }

        if (errorText && !finalText) {
          setRunning((r) => ({ ...r, [wf.id]: { status: "fehler", note: errorText } }));
          return;
        }
        const summary = finalText
          ? `${artifactCount > 0 ? `${artifactCount} Datei(en) erzeugt. ` : ""}${firstSentence(finalText)}`
          : "Mission abgeschlossen.";
        persist(
          workflows.map((w) =>
            w.id === wf.id
              ? { ...w, lastRun: Date.now(), lastScore: score, lastSummary: summary.slice(0, 220) }
              : w,
          ),
        );
        setRunning((r) => ({ ...r, [wf.id]: null }));
      } catch {
        setRunning((r) => ({
          ...r,
          [wf.id]: { status: "fehler", note: "Netzwerkfehler – bitte erneut versuchen." },
        }));
      }
    },
    [workflows, persist],
  );

  const dueList = workflows.filter(isDue);

  return (
    <div className="min-h-dvh bg-[#0b0a08] text-zinc-200">
      <div className="hud-texture" aria-hidden="true" />
      <div className="relative z-10 mx-auto max-w-5xl px-4 pb-24">
        {/* Kopfzeile */}
        <header className="flex items-center justify-between border-b border-[#ff8c2a]/15 py-4">
          <div className="flex items-center gap-2">
            <span className="hud-pulse inline-block h-2 w-2 rounded-full bg-[#ff8c2a]" />
            <span className="hud-label">AI Command Center</span>
          </div>
          <nav className="flex items-center gap-4 text-sm text-zinc-400" aria-label="Bereiche">
            <Link href="/dashboard" className="hover:text-[#ffb35c]">Missionen</Link>
            <Link href="/chat" className="hover:text-[#ffb35c]">Kommando</Link>
            <span className="text-[#ffb35c]">Autopilot</span>
            <Link href="/berichte" className="hidden hover:text-[#ffb35c] sm:inline">Berichte</Link>
            <Link href="/team" className="hidden hover:text-[#ffb35c] sm:inline">Team</Link>
          </nav>
        </header>

        <div className="pt-10">
          <p className="hud-label mb-3">Workflow-Manager</p>
          <h1 className="text-3xl font-semibold text-white sm:text-4xl">
            Autopilot: wiederkehrende Aufträge
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-zinc-400">
            Legen Sie Aufträge an, die Ihre KI-Belegschaft regelmässig erledigt –
            vom Social-Media-Wochenplan bis zum Bericht für die Geschäftsleitung.
            Fällige Workflows starten Sie mit einem Klick; jede Ausführung ist
            eine echte Mission und zählt auf Ihr Tageslimit.
          </p>
          <p className="mt-3 max-w-2xl rounded-lg border border-[#ff8c2a]/20 bg-[#ff8c2a]/[0.05] px-4 py-3 text-xs leading-relaxed text-[#ffb35c]/90">
            Ehrlich gesagt: Der Autopilot arbeitet, solange diese Seite geöffnet
            ist. Vollautomatischer Betrieb rund um die Uhr (Server-seitig, ohne
            Browser) gehört zum Enterprise-Ausbau und wird pro Kunde eingerichtet.
          </p>
        </div>

        {/* Fällige Workflows */}
        {dueList.length > 0 && (
          <div className="mt-8 flex items-center justify-between rounded-xl border border-[#ffd257]/40 bg-[#ffd257]/[0.06] px-4 py-3">
            <p className="text-sm text-[#ffd257]">
              {dueList.length} Workflow{dueList.length > 1 ? "s" : ""} fällig
            </p>
            <button
              onClick={() => dueList.forEach((w) => run(w))}
              className="shop-btn rounded-lg bg-[#ffd257] px-4 py-2 text-sm font-bold text-[#1a0f04]"
            >
              Alle fälligen ausführen
            </button>
          </div>
        )}

        {/* Neuer Workflow */}
        <div className="mt-8">
          {!formOpen ? (
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => setFormOpen(true)}
                className="shop-btn rounded-lg bg-gradient-to-r from-[#ffb066] via-[#ff8c2a] to-[#ff5f1f] px-5 py-2.5 text-sm font-bold text-[#1a0f04]"
              >
                + Eigener Workflow
              </button>
              <span className="text-xs text-zinc-500">oder Vorlage übernehmen:</span>
              {VORLAGEN.map((v) => (
                <button
                  key={v.name}
                  onClick={() => addWorkflow(v.name, v.goal, v.frequenz)}
                  className="shop-btn rounded-lg border border-[#ff8c2a]/25 px-3 py-2 text-xs text-[#ffb35c] hover:border-[#ff8c2a]/60"
                >
                  {v.name}
                </button>
              ))}
            </div>
          ) : (
            <form
              className="hud-panel hud-corners relative rounded-xl p-5"
              onSubmit={(e) => {
                e.preventDefault();
                addWorkflow(name, goal, frequenz);
              }}
            >
              <h2 className="text-lg font-semibold text-white">Neuer Workflow</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-[1fr_180px]">
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Name, z. B. Social-Media-Woche"
                  className="rounded-lg border border-[#ff8c2a]/25 bg-[#12100d] px-4 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-[#ff8c2a]/60 focus:outline-none"
                  aria-label="Workflow-Name"
                />
                <select
                  value={frequenz}
                  onChange={(e) => setFrequenz(e.target.value as Frequenz)}
                  className="rounded-lg border border-[#ff8c2a]/25 bg-[#12100d] px-3 py-2.5 text-sm text-zinc-100 focus:border-[#ff8c2a]/60 focus:outline-none"
                  aria-label="Frequenz"
                >
                  <option value="taeglich">Täglich</option>
                  <option value="woechentlich">Wöchentlich</option>
                  <option value="manuell">Manuell</option>
                </select>
              </div>
              <textarea
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                rows={3}
                placeholder="Auftrag an Ihre KI-Belegschaft …"
                className="mt-4 w-full resize-none rounded-lg border border-[#ff8c2a]/25 bg-[#12100d] px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-[#ff8c2a]/60 focus:outline-none"
                aria-label="Workflow-Auftrag"
              />
              <div className="mt-4 flex gap-3">
                <button
                  type="submit"
                  disabled={!name.trim() || !goal.trim()}
                  className="shop-btn rounded-lg bg-gradient-to-r from-[#ffb066] via-[#ff8c2a] to-[#ff5f1f] px-5 py-2.5 text-sm font-bold text-[#1a0f04] disabled:opacity-40"
                >
                  Anlegen
                </button>
                <button
                  type="button"
                  onClick={() => setFormOpen(false)}
                  className="rounded-lg border border-[#ff8c2a]/25 px-5 py-2.5 text-sm text-zinc-400"
                >
                  Abbrechen
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Liste */}
        <div className="mt-8 space-y-4">
          {workflows.length === 0 && (
            <p className="rounded-xl border border-[#ff8c2a]/15 px-5 py-8 text-center text-sm text-zinc-500">
              Noch keine Workflows. Übernehmen Sie eine Vorlage oder legen Sie
              einen eigenen an.
            </p>
          )}
          {workflows.map((w) => {
            const state = running[w.id] ?? null;
            return (
              <article key={w.id} className="hud-panel relative rounded-xl p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold text-white">{w.name}</h3>
                      <span className="rounded-full border border-[#ff8c2a]/30 px-2 py-0.5 text-[11px] text-[#ffb35c]">
                        {FREQUENZ_LABEL[w.frequenz]}
                      </span>
                      {isDue(w) && (
                        <span className="rounded-full border border-[#ffd257]/50 bg-[#ffd257]/10 px-2 py-0.5 text-[11px] text-[#ffd257]">
                          Fällig
                        </span>
                      )}
                    </div>
                    <p className="mt-1.5 max-w-2xl text-sm text-zinc-400">{w.goal}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <button
                      onClick={() => run(w)}
                      disabled={state?.status === "laeuft"}
                      className="shop-btn rounded-lg border border-[#ff8c2a]/40 bg-[#ff8c2a]/10 px-4 py-2 text-sm font-semibold text-[#ffb35c] hover:bg-[#ff8c2a]/20 disabled:opacity-40"
                    >
                      {state?.status === "laeuft" ? "Läuft …" : "Jetzt ausführen"}
                    </button>
                    <button
                      onClick={() => removeWorkflow(w.id)}
                      className="rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-500 hover:border-red-500/50 hover:text-red-400"
                      aria-label={`Workflow "${w.name}" löschen`}
                    >
                      ✕
                    </button>
                  </div>
                </div>

                {state?.status === "laeuft" && (
                  <p className="mt-3 flex items-center gap-2 text-sm text-[#ffb35c]">
                    <span className="hud-pulse inline-block h-2 w-2 rounded-full bg-[#ff8c2a]" />
                    {state.note}
                  </p>
                )}
                {state?.status === "fehler" && (
                  <p className="mt-3 text-sm text-red-300">{state.note}</p>
                )}
                {!state && w.lastRun && (
                  <p className="mt-3 text-xs text-zinc-500">
                    Zuletzt: {new Date(w.lastRun).toLocaleString("de-CH")}
                    {typeof w.lastScore === "number" && ` · Quality-Score ${w.lastScore}`}
                    {w.lastSummary && ` · ${w.lastSummary}`}
                    {" · "}
                    <Link href="/dashboard" className="text-[#ffb35c] hover:underline">
                      Ergebnis im Dashboard
                    </Link>
                  </p>
                )}
              </article>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function firstSentence(text: string): string {
  const clean = text.replace(/[#*`]/g, "").trim();
  const punkt = clean.indexOf(". ");
  return punkt > 20 ? clean.slice(0, punkt + 1) : clean.slice(0, 160);
}

function safeGet(key: string): string | undefined {
  try {
    return localStorage.getItem(key) ?? undefined;
  } catch {
    return undefined;
  }
}
