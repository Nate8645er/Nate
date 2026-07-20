"use client";

/**
 * Mission Control Dashboard.
 *
 * Startet Missionen gegen POST /api/mission und rendert den
 * SSE-Stream (AgentEvent) live: Status je Agent, Ausgaben,
 * Quality-Score und finales Ergebnis. Verlauf in localStorage.
 *
 * TODO Phase 2: Verlauf serverseitig je Benutzer persistieren.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import type { AgentEvent, AgentRole, AgentStatus } from "@/lib/agents/types";

const AGENT_META: Record<AgentRole, { name: string; tagline: string }> = {
  commander: { name: "Commander", tagline: "Der digitale CEO" },
  builder: { name: "Builder", tagline: "Der Entwickler" },
  analyst: { name: "Analyst", tagline: "Der Stratege" },
  quality: { name: "Quality", tagline: "Der Pruefer" },
};

const STATUS_LABEL: Record<AgentStatus, string> = {
  idle: "Bereit",
  working: "Arbeitet",
  done: "Fertig",
  error: "Fehler",
};

interface HistoryEntry {
  goal: string;
  final: string;
  score: number | null;
  at: string;
}

const HISTORY_KEY = "acc-mission-history";

/** Minimaler Markdown-Renderer (Ueberschriften, Listen, fett) ohne externe Lib. */
function renderMarkdown(md: string): React.ReactNode[] {
  return md.split("\n").map((line, i) => {
    const bold = (s: string) =>
      s.split(/\*\*(.+?)\*\*/g).map((part, j) =>
        j % 2 === 1 ? <strong key={j}>{part}</strong> : part,
      );
    if (line.startsWith("### ")) return <h4 key={i} className="mt-4 mb-1 font-semibold text-white">{bold(line.slice(4))}</h4>;
    if (line.startsWith("## ")) return <h3 key={i} className="mt-5 mb-2 text-lg font-semibold text-white">{bold(line.slice(3))}</h3>;
    if (line.startsWith("# ")) return <h2 key={i} className="mt-5 mb-2 text-xl font-bold text-white">{bold(line.slice(2))}</h2>;
    if (/^\s*[-*] /.test(line)) return <li key={i} className="ml-5 list-disc">{bold(line.replace(/^\s*[-*] /, ""))}</li>;
    if (/^\s*\d+\. /.test(line)) return <li key={i} className="ml-5 list-decimal">{bold(line.replace(/^\s*\d+\. /, ""))}</li>;
    if (!line.trim()) return <div key={i} className="h-2" />;
    return <p key={i} className="my-1">{bold(line)}</p>;
  });
}

export default function DashboardPage() {
  const [goal, setGoal] = useState("");
  const [running, setRunning] = useState(false);
  const [statuses, setStatuses] = useState<Record<AgentRole, { status: AgentStatus; message: string }>>({
    commander: { status: "idle", message: "Bereit" },
    builder: { status: "idle", message: "Bereit" },
    analyst: { status: "idle", message: "Bereit" },
    quality: { status: "idle", message: "Bereit" },
  });
  const [outputs, setOutputs] = useState<Partial<Record<AgentRole, string>>>({});
  const [score, setScore] = useState<number | null>(null);
  const [improvements, setImprovements] = useState<string[]>([]);
  const [finalResult, setFinalResult] = useState("");
  const [error, setError] = useState("");
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [openOutput, setOpenOutput] = useState<AgentRole | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      if (raw) setHistory(JSON.parse(raw) as HistoryEntry[]);
    } catch { /* korrupter Verlauf wird ignoriert */ }
  }, []);

  const saveHistory = useCallback((entry: HistoryEntry) => {
    setHistory((prev) => {
      const next = [entry, ...prev].slice(0, 20);
      try { localStorage.setItem(HISTORY_KEY, JSON.stringify(next)); } catch { /* voll */ }
      return next;
    });
  }, []);

  const handleEvent = useCallback((ev: AgentEvent, ctx: { goal: string; score: number | null; final: string }) => {
    switch (ev.type) {
      case "status":
        setStatuses((s) => ({ ...s, [ev.agent]: { status: ev.status, message: ev.message } }));
        break;
      case "output":
        setOutputs((o) => ({ ...o, [ev.agent]: ev.content }));
        break;
      case "score":
        ctx.score = ev.score;
        setScore(ev.score);
        setImprovements(ev.improvements);
        break;
      case "final":
        ctx.final = ev.content;
        setFinalResult(ev.content);
        break;
      case "error":
        setError(ev.message);
        if (ev.agent) setStatuses((s) => ({ ...s, [ev.agent as AgentRole]: { status: "error", message: ev.message } }));
        break;
    }
  }, []);

  const startMission = useCallback(async () => {
    const missionGoal = goal.trim();
    if (!missionGoal || running) return;
    setRunning(true);
    setError("");
    setFinalResult("");
    setScore(null);
    setImprovements([]);
    setOutputs({});
    setStatuses({
      commander: { status: "working", message: "Analysiert die Aufgabe" },
      builder: { status: "idle", message: "Wartet auf den Plan" },
      analyst: { status: "idle", message: "Wartet auf den Plan" },
      quality: { status: "idle", message: "Wartet auf Ergebnisse" },
    });

    const ctx = { goal: missionGoal, score: null as number | null, final: "" };
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch("/api/mission", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal: missionGoal }),
        signal: controller.signal,
      });
      if (!res.ok || !res.body) {
        const data = (await res.json().catch(() => null)) as { error?: string } | null;
        throw new Error(data?.error ?? `Server antwortete mit ${res.status}`);
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data: ")) continue;
          try {
            handleEvent(JSON.parse(line.slice(6)) as AgentEvent, ctx);
          } catch { /* defektes Event ueberspringen */ }
        }
      }
      if (ctx.final) {
        saveHistory({ goal: missionGoal, final: ctx.final, score: ctx.score, at: new Date().toISOString() });
      }
    } catch (err) {
      if (!(err instanceof DOMException && err.name === "AbortError")) {
        setError(err instanceof Error ? err.message : "Unbekannter Fehler.");
      }
    } finally {
      setRunning(false);
      abortRef.current = null;
    }
  }, [goal, running, handleEvent, saveHistory]);

  const stopMission = useCallback(() => abortRef.current?.abort(), []);

  return (
    <main className="min-h-screen bg-[#0a0c10] text-slate-300">
      <header className="sticky top-0 z-20 border-b border-white/5 bg-[#0a0c10]/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
          <a href="/" className="text-lg font-bold tracking-tight text-white">
            AI <span className="text-cyan-400">Command Center</span>
          </a>
          <span className="rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-medium text-cyan-300">
            Mission Control · Demo
          </span>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-5 py-10">
        {/* Eingabe */}
        <section aria-label="Neue Mission">
          <h1 className="text-2xl font-bold text-white">Was soll Ihre KI-Abteilung erledigen?</h1>
          <p className="mt-1 text-sm text-slate-400">
            Commander plant, Builder und Analyst arbeiten parallel, Quality prueft. Sie erhalten ein fertiges Ergebnis.
          </p>
          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <input
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && startMission()}
              placeholder='z. B. "Erstelle eine Marketingstrategie fuer eine Zuercher Baeckerei"'
              disabled={running}
              className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-500 outline-none transition focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/20"
            />
            {running ? (
              <button onClick={stopMission} className="rounded-xl border border-red-400/40 px-6 py-3 font-semibold text-red-300 transition hover:bg-red-400/10 active:scale-[0.98]">
                Abbrechen
              </button>
            ) : (
              <button onClick={startMission} disabled={!goal.trim()} className="rounded-xl bg-cyan-500 px-6 py-3 font-semibold text-[#06272e] transition hover:bg-cyan-400 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40">
                Mission starten
              </button>
            )}
          </div>
          {error && (
            <p role="alert" className="mt-3 rounded-lg border border-red-400/30 bg-red-400/10 px-4 py-2 text-sm text-red-300">
              {error}
            </p>
          )}
        </section>

        {/* Agenten-Status */}
        <section aria-label="Agenten-Status" className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {(Object.keys(AGENT_META) as AgentRole[]).map((role) => {
            const st = statuses[role];
            const hasOutput = Boolean(outputs[role]);
            return (
              <div key={role} className={`rounded-2xl border p-4 transition ${st.status === "working" ? "border-cyan-400/50 bg-cyan-400/5" : st.status === "done" ? "border-emerald-400/30 bg-white/[0.03]" : st.status === "error" ? "border-red-400/40 bg-red-400/5" : "border-white/10 bg-white/[0.02]"}`}>
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-white">{AGENT_META[role].name}</h3>
                  <span aria-hidden className={`h-2.5 w-2.5 rounded-full ${st.status === "working" ? "animate-pulse bg-cyan-400" : st.status === "done" ? "bg-emerald-400" : st.status === "error" ? "bg-red-400" : "bg-slate-600"}`} />
                </div>
                <p className="text-xs text-slate-500">{AGENT_META[role].tagline}</p>
                <p className="mt-3 text-sm">
                  <span className="font-medium text-slate-200">{STATUS_LABEL[st.status]}</span>
                  <span className="text-slate-400"> · {st.message}</span>
                </p>
                {hasOutput && (
                  <button onClick={() => setOpenOutput(openOutput === role ? null : role)} className="mt-3 text-xs font-medium text-cyan-300 underline-offset-2 hover:underline">
                    {openOutput === role ? "Ausgabe verbergen" : "Ausgabe ansehen"}
                  </button>
                )}
              </div>
            );
          })}
        </section>

        {openOutput && outputs[openOutput] && (
          <section aria-label="Agenten-Ausgabe" className="mt-4 rounded-2xl border border-white/10 bg-white/[0.02] p-5 text-sm leading-relaxed">
            <h3 className="mb-2 font-semibold text-white">{AGENT_META[openOutput].name}: Rohausgabe</h3>
            <div className="max-h-72 overflow-y-auto whitespace-pre-wrap text-slate-300">{outputs[openOutput]}</div>
          </section>
        )}

        {/* Quality-Score */}
        {score !== null && (
          <section aria-label="Qualitaetsbewertung" className="mt-8 rounded-2xl border border-white/10 bg-white/[0.02] p-5">
            <div className="flex items-center gap-4">
              <div className={`text-3xl font-extrabold ${score >= 80 ? "text-emerald-400" : score >= 60 ? "text-amber-400" : "text-red-400"}`}>{score}/100</div>
              <div className="text-sm text-slate-400">Bewertung durch Quality AI</div>
            </div>
            {improvements.length > 0 && (
              <ul className="mt-3 space-y-1 text-sm text-slate-300">
                {improvements.map((imp, i) => (
                  <li key={i} className="ml-5 list-disc">{imp}</li>
                ))}
              </ul>
            )}
          </section>
        )}

        {/* Finales Ergebnis */}
        {finalResult && (
          <section aria-label="Ergebnis" className="mt-8 rounded-2xl border border-cyan-400/25 bg-gradient-to-b from-cyan-400/[0.06] to-transparent p-6">
            <h2 className="text-lg font-bold text-white">Ergebnis Ihrer KI-Abteilung</h2>
            <div className="mt-3 text-sm leading-relaxed text-slate-300">{renderMarkdown(finalResult)}</div>
          </section>
        )}

        {/* Verlauf */}
        {history.length > 0 && (
          <section aria-label="Missionsverlauf" className="mt-12">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-500">Verlauf</h2>
            <ul className="space-y-2">
              {history.map((h, i) => (
                <li key={i}>
                  <button
                    onClick={() => { setFinalResult(h.final); setScore(h.score); setImprovements([]); setError(""); }}
                    className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3 text-left text-sm transition hover:border-cyan-400/40"
                  >
                    <span className="font-medium text-slate-200">{h.goal}</span>
                    <span className="ml-2 text-xs text-slate-500">
                      {new Date(h.at).toLocaleString("de-CH")} {h.score !== null ? `· ${h.score}/100` : ""}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </main>
  );
}
