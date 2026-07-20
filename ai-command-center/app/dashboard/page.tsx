"use client";

/**
 * Mission Control Dashboard — JARVIS Command Center HUD.
 *
 * Startet Missionen gegen POST /api/mission und rendert den SSE-Stream
 * (AgentEvent) live: Status je Agent, Terminal-Feed, Telemetrie,
 * Quality-Gauge und finales Ergebnis. Verlauf + Plan in localStorage.
 *
 * Abo-Stufen (FREE/STARTER/PROFESSIONAL/BUSINESS) schalten HUD-Module
 * rein visuell frei — die Mission-Pipeline ist fuer alle identisch.
 *
 * TODO Phase 2: Verlauf + Plan serverseitig je Benutzer persistieren.
 */

import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { AgentEvent, AgentRole, AgentStatus } from "@/lib/agents/types";

/* ------------------------------- Konstanten ------------------------------- */

const AGENT_META: Record<AgentRole, { name: string; tagline: string }> = {
  commander: { name: "Commander", tagline: "Der digitale CEO" },
  builder: { name: "Builder", tagline: "Der Entwickler" },
  analyst: { name: "Analyst", tagline: "Der Stratege" },
  quality: { name: "Quality", tagline: "Der Pruefer" },
};

/** Zusatz-Einheiten ab PROFESSIONAL (Dummy-Status "bereit"). */
const EXTRA_AGENTS = [
  { name: "Marketing", tagline: "Kampagnen & Content" },
  { name: "Coding", tagline: "Software & Automation" },
  { name: "Research", tagline: "Tiefenrecherche" },
  { name: "Business", tagline: "Strategie & Finanzen" },
] as const;

const STATUS_LABEL: Record<AgentStatus, string> = {
  idle: "Bereit",
  working: "Arbeitet",
  done: "Fertig",
  error: "Fehler",
};

type Plan = "FREE" | "STARTER" | "PROFESSIONAL" | "BUSINESS";
const PLANS: Plan[] = ["FREE", "STARTER", "PROFESSIONAL", "BUSINESS"];
const PLAN_LEVEL: Record<Plan, number> = {
  FREE: 0,
  STARTER: 1,
  PROFESSIONAL: 2,
  BUSINESS: 3,
};

const HISTORY_KEY = "acc-mission-history";
const PLAN_KEY = "acc-plan";
/** Lizenz-Token (30 Tage, HMAC-signiert) aus POST /api/license. */
const LICENSE_TOKEN_KEY = "acc-license-token";
/** Usage-Token (Tageszaehler), vom Server per SSE-Event "usage" erneuert. */
const USAGE_TOKEN_KEY = "acc-usage-token";
const BRANCHE_KEY = "acc-branche";
const GROESSE_KEY = "acc-groesse";
const MAX_LOG_LINES = 300;

const BRANCHEN = [
  "Marketing/Agentur",
  "Handel/E-Commerce",
  "Handwerk/Bau",
  "Treuhand/Finanzen",
  "Gesundheit",
  "Software/IT",
  "Gastronomie",
  "Andere",
] as const;

const GROESSEN = ["Solo", "2-10", "11-50", "50+"] as const;

interface HistoryEntry {
  goal: string;
  final: string;
  score: number | null;
  at: string;
}

/* ------------------------------ kleine Helfer ----------------------------- */

function timestamp(): string {
  return new Date().toLocaleTimeString("de-CH", { hour12: false });
}

function formatElapsed(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = String(Math.floor(total / 60)).padStart(2, "0");
  const s = String(total % 60).padStart(2, "0");
  return `${m}:${s}`;
}

/**
 * Liest das Payload eines signierten Tokens ("base64url(JSON).hmac") zur
 * ANZEIGE. Die HMAC-Pruefung passiert ausschliesslich serverseitig.
 */
function decodeTokenPayload(token: string): Record<string, unknown> | null {
  const dot = token.lastIndexOf(".");
  if (dot <= 0) return null;
  try {
    const b64 = token.slice(0, dot).replace(/-/g, "+").replace(/_/g, "/");
    const parsed: unknown = JSON.parse(atob(b64));
    return typeof parsed === "object" && parsed !== null
      ? (parsed as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

/** Minimaler Markdown-Renderer (Ueberschriften, Listen, fett) ohne externe Lib. */
function renderMarkdown(md: string): React.ReactNode[] {
  return md.split("\n").map((line, i) => {
    const bold = (s: string) =>
      s.split(/\*\*(.+?)\*\*/g).map((part, j) =>
        j % 2 === 1 ? <strong key={j}>{part}</strong> : part,
      );
    if (line.startsWith("### ")) return <h4 key={i} className="mt-4 mb-1 font-semibold text-[#fff3e2]">{bold(line.slice(4))}</h4>;
    if (line.startsWith("## ")) return <h3 key={i} className="mt-5 mb-2 text-lg font-semibold text-[#fff3e2]">{bold(line.slice(3))}</h3>;
    if (line.startsWith("# ")) return <h2 key={i} className="mt-5 mb-2 text-xl font-bold text-[#fff3e2]">{bold(line.slice(2))}</h2>;
    if (/^\s*[-*] /.test(line)) return <li key={i} className="ml-5 list-disc">{bold(line.replace(/^\s*[-*] /, ""))}</li>;
    if (/^\s*\d+\. /.test(line)) return <li key={i} className="ml-5 list-decimal">{bold(line.replace(/^\s*\d+\. /, ""))}</li>;
    if (!line.trim()) return <div key={i} className="h-2" />;
    return <p key={i} className="my-1">{bold(line)}</p>;
  });
}

/* ------------------------------ HUD-Bausteine ------------------------------ */

/** Rotierender Drahtgitter-Globus — reines SVG/CSS, keine externen Libs. */
const WireframeGlobe = memo(function WireframeGlobe() {
  const stroke = "rgba(255,179,92,0.55)";
  const thin = 0.6;
  return (
    <div className="relative mx-auto h-48 w-48 sm:h-60 sm:w-60" aria-hidden>
      <svg viewBox="0 0 200 200" className="h-full w-full">
        {/* Aeussere Ringe */}
        <g className="hud-spin-rev">
          <circle cx="100" cy="100" r="95" fill="none" stroke="rgba(255,140,42,0.4)" strokeWidth="0.8" strokeDasharray="2 7" />
        </g>
        <circle cx="100" cy="100" r="88" fill="none" stroke="rgba(255,140,42,0.18)" strokeWidth="0.6" />
        {/* Globus */}
        <g className="hud-spin-slow">
          <circle cx="100" cy="100" r="76" fill="none" stroke={stroke} strokeWidth="0.9" />
          {/* Meridiane */}
          <ellipse cx="100" cy="100" rx="12" ry="76" fill="none" stroke={stroke} strokeWidth={thin} />
          <ellipse cx="100" cy="100" rx="36" ry="76" fill="none" stroke={stroke} strokeWidth={thin} />
          <ellipse cx="100" cy="100" rx="58" ry="76" fill="none" stroke={stroke} strokeWidth={thin} />
          {/* Breitengrade */}
          <ellipse cx="100" cy="100" rx="76" ry="22" fill="none" stroke={stroke} strokeWidth={thin} />
          <ellipse cx="100" cy="68" rx="60" ry="15" fill="none" stroke={stroke} strokeWidth={thin} />
          <ellipse cx="100" cy="132" rx="60" ry="15" fill="none" stroke={stroke} strokeWidth={thin} />
          <ellipse cx="100" cy="46" rx="36" ry="9" fill="none" stroke={stroke} strokeWidth={thin} />
          <ellipse cx="100" cy="154" rx="36" ry="9" fill="none" stroke={stroke} strokeWidth={thin} />
        </g>
        {/* Fadenkreuz */}
        <line x1="100" y1="2" x2="100" y2="14" stroke="rgba(255,140,42,0.7)" strokeWidth="1" />
        <line x1="100" y1="186" x2="100" y2="198" stroke="rgba(255,140,42,0.7)" strokeWidth="1" />
        <line x1="2" y1="100" x2="14" y2="100" stroke="rgba(255,140,42,0.7)" strokeWidth="1" />
        <line x1="186" y1="100" x2="198" y2="100" stroke="rgba(255,140,42,0.7)" strokeWidth="1" />
        <circle cx="100" cy="100" r="2" fill="#ff8c2a" />
      </svg>
      <div className="pointer-events-none absolute inset-0 rounded-full" style={{ boxShadow: "0 0 60px rgba(255,140,42,0.12) inset, 0 0 40px rgba(255,140,42,0.08)" }} />
    </div>
  );
});

/** Radial-HUD-Gauge fuer den Quality-Score (animierter Kreisbogen). */
const RadialGauge = memo(function RadialGauge({ score }: { score: number | null }) {
  const r = 54;
  const c = 2 * Math.PI * r;
  const pct = score ?? 0;
  const offset = c * (1 - Math.min(100, Math.max(0, pct)) / 100);
  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 140 140" className="h-36 w-36 sm:h-44 sm:w-44" role="img" aria-label={`Quality-Score ${score ?? "unbekannt"} von 100`}>
        <circle cx="70" cy="70" r={r} fill="none" stroke="rgba(255,140,42,0.14)" strokeWidth="5" />
        <circle cx="70" cy="70" r={r + 8} fill="none" stroke="rgba(255,140,42,0.2)" strokeWidth="0.6" strokeDasharray="1 5" />
        <circle
          cx="70" cy="70" r={r} fill="none"
          stroke={pct >= 80 ? "#ff8c2a" : pct >= 60 ? "#ffb35c" : "#ff5c3a"}
          strokeWidth="5" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={offset}
          transform="rotate(-90 70 70)"
          className="hud-gauge-arc"
          style={{ filter: "drop-shadow(0 0 6px rgba(255,140,42,0.55))" }}
        />
        <text x="70" y="72" textAnchor="middle" fill="#fff3e2" fontSize="26" fontWeight="700" fontFamily="var(--font-geist-mono), monospace">
          {score ?? "--"}
        </text>
        <text x="70" y="90" textAnchor="middle" fill="rgba(255,179,92,0.7)" fontSize="8" letterSpacing="3" fontFamily="var(--font-geist-mono), monospace">
          QUALITY %
        </text>
      </svg>
    </div>
  );
});

/** Telemetrie-Kacheln: Missionen, aktive Agenten, Events/s, Laufzeit (live). */
const TelemetryTiles = memo(function TelemetryTiles({
  missions,
  activeAgents,
  totalAgents,
  running,
  startedAt,
  eventTimesRef,
}: {
  missions: number;
  activeAgents: number;
  totalAgents: number;
  running: boolean;
  startedAt: number | null;
  eventTimesRef: React.RefObject<number[]>;
}) {
  const [, setTick] = useState(0);
  const lastElapsedRef = useRef(0);

  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, [running]);

  const now = Date.now();
  if (running && startedAt) lastElapsedRef.current = now - startedAt;
  const eps = running
    ? (eventTimesRef.current ?? []).filter((t) => now - t < 5000).length / 5
    : 0;

  const tiles = [
    { label: "Missionen", value: String(missions) },
    { label: "Agenten aktiv", value: `${activeAgents}/${totalAgents}` },
    { label: "Events/s", value: eps.toFixed(1) },
    { label: "Laufzeit", value: formatElapsed(lastElapsedRef.current) },
  ];

  return (
    <div className="grid grid-cols-2 gap-3">
      {tiles.map((t) => (
        <div key={t.label} className="hud-panel hud-corners rounded-sm px-3 py-3 text-center">
          <div className="hud-label">{t.label}</div>
          <div className="mt-1 font-mono text-xl font-bold text-[#fff3e2] sm:text-2xl">{t.value}</div>
        </div>
      ))}
    </div>
  );
});

/** Terminal-Feed: alle AgentEvents als scrollende Log-Zeilen. */
const TerminalFeed = memo(function TerminalFeed({ logs }: { logs: string[] }) {
  const boxRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const el = boxRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [logs]);
  return (
    <section aria-label="Terminal-Feed" className="hud-panel hud-corners mt-8 rounded-sm">
      <div className="flex items-center justify-between border-b border-[#ff8c2a]/15 px-4 py-2">
        <span className="hud-label">Mission Log // Live-Feed</span>
        <span className="hud-pulse h-1.5 w-1.5 rounded-full bg-[#ff8c2a]" aria-hidden />
      </div>
      <div ref={boxRef} className="max-h-56 overflow-y-auto px-4 py-3 font-mono text-[11px] leading-5 text-[#ffb35c]/85">
        {logs.length === 0 ? (
          <p className="text-[#ffb35c]/40">[SYSTEM] Bereit. Warte auf Mission …</p>
        ) : (
          logs.map((line, i) => <p key={i} className="whitespace-pre-wrap">{line}</p>)
        )}
      </div>
    </section>
  );
});

/** Live-Telemetrie-Leiste (nur BUSINESS), fix am unteren Rand. */
const BusinessTicker = memo(function BusinessTicker({
  running,
  startedAt,
  activeAgents,
  totalAgents,
  missions,
  totalEventsRef,
}: {
  running: boolean;
  startedAt: number | null;
  activeAgents: number;
  totalAgents: number;
  missions: number;
  totalEventsRef: React.RefObject<number>;
}) {
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);
  const uptime = running && startedAt ? formatElapsed(Date.now() - startedAt) : "00:00";
  const items = [
    `UPTIME ${uptime}`,
    `EVENTS ${totalEventsRef.current ?? 0}`,
    `AGENTS ${activeAgents}/${totalAgents}`,
    `MISSIONS ${missions}`,
    `LINK ${running ? "ACTIVE" : "STABLE"}`,
    "PLAN BUSINESS",
  ];
  return (
    <div className="fixed inset-x-0 bottom-0 z-30 border-t border-[#ffd257]/40 bg-[#0b0a08]/90 backdrop-blur" role="status" aria-label="Live-Telemetrie">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-1 px-5 py-1.5 font-mono text-[10px] tracking-[0.18em] text-[#ffd257]/80">
        <span className="hud-pulse h-1.5 w-1.5 rounded-full bg-[#ffd257]" aria-hidden />
        {items.map((it) => <span key={it}>{it}</span>)}
      </div>
    </div>
  );
});

/** Agenten-Statuskarte mit Puls-Glow. */
const AgentCard = memo(function AgentCard({
  role,
  name,
  tagline,
  status,
  message,
  hasOutput,
  isOpen,
  onToggle,
  fancy,
}: {
  role: AgentRole;
  name: string;
  tagline: string;
  status: AgentStatus;
  message: string;
  hasOutput: boolean;
  isOpen: boolean;
  onToggle: (role: AgentRole) => void;
  fancy: boolean;
}) {
  const borderCls =
    status === "working"
      ? "border-[#ff8c2a]/70"
      : status === "done"
        ? "border-[#ffb35c]/40"
        : status === "error"
          ? "border-red-400/50"
          : "border-[#ff8c2a]/20";
  return (
    <div
      className={`relative rounded-sm border bg-[#ff8c2a]/[0.03] p-4 transition-colors ${borderCls} ${fancy ? "hud-corners" : ""}`}
      style={
        fancy && status === "working"
          ? { boxShadow: "0 0 18px rgba(255,140,42,0.25), inset 0 0 18px rgba(255,140,42,0.06)" }
          : undefined
      }
    >
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-[#fff3e2]">{name}</h3>
        <span
          aria-hidden
          className={`h-2 w-2 rounded-full ${
            status === "working"
              ? "hud-pulse bg-[#ff8c2a]"
              : status === "done"
                ? "bg-[#ffb35c]"
                : status === "error"
                  ? "bg-red-400"
                  : "bg-[#5a4a35]"
          }`}
          style={status === "working" ? { boxShadow: "0 0 8px rgba(255,140,42,0.9)" } : undefined}
        />
      </div>
      <p className="hud-label mt-0.5">{tagline}</p>
      <p className="mt-3 text-sm">
        <span className="font-medium text-[#fff3e2]">{STATUS_LABEL[status]}</span>
        <span className="text-[#c9b391]"> · {message}</span>
      </p>
      {hasOutput && (
        <button
          onClick={() => onToggle(role)}
          className="mt-3 font-mono text-[10px] uppercase tracking-[0.18em] text-[#ff8c2a] underline-offset-2 hover:underline"
        >
          {isOpen ? "Ausgabe verbergen" : "Ausgabe ansehen"}
        </button>
      )}
    </div>
  );
});

/** Statische Zusatz-Einheit (PROFESSIONAL+): Dummy-Status "bereit". */
const ExtraAgentCard = memo(function ExtraAgentCard({ name, tagline }: { name: string; tagline: string }) {
  return (
    <div className="hud-corners relative rounded-sm border border-[#ff8c2a]/20 bg-[#ff8c2a]/[0.02] p-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-[#fff3e2]">{name}</h3>
        <span aria-hidden className="h-2 w-2 rounded-full bg-[#7a6a4a]" />
      </div>
      <p className="hud-label mt-0.5">{tagline}</p>
      <p className="mt-3 text-sm">
        <span className="font-medium text-[#fff3e2]">Bereit</span>
        <span className="text-[#c9b391]"> · Einheit im Standby</span>
      </p>
    </div>
  );
});

/* --------------------------------- Seite ---------------------------------- */

export default function DashboardPage() {
  const [goal, setGoal] = useState("");
  const [running, setRunning] = useState(false);
  const [plan, setPlan] = useState<Plan>("PROFESSIONAL");
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
  const [logs, setLogs] = useState<string[]>([]);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const eventTimesRef = useRef<number[]>([]);
  const totalEventsRef = useRef(0);

  const level = PLAN_LEVEL[plan];
  const showGlobe = level >= 1;
  const showTelemetry = level >= 1;
  const showGauge = level >= 2;
  const showFeed = level >= 2;
  const showExtraAgents = level >= 2;
  const isBusiness = level >= 3;
  const fancy = level >= 1;
  const totalAgents = showExtraAgents ? 8 : 4;

  useEffect(() => {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      if (raw) setHistory(JSON.parse(raw) as HistoryEntry[]);
      const storedPlan = localStorage.getItem(PLAN_KEY);
      if (storedPlan && (PLANS as string[]).includes(storedPlan)) setPlan(storedPlan as Plan);
    } catch { /* korrupter Zustand wird ignoriert */ }
  }, []);

  const selectPlan = useCallback((p: Plan) => {
    setPlan(p);
    try { localStorage.setItem(PLAN_KEY, p); } catch { /* voll */ }
  }, []);

  const saveHistory = useCallback((entry: HistoryEntry) => {
    setHistory((prev) => {
      const next = [entry, ...prev].slice(0, 20);
      try { localStorage.setItem(HISTORY_KEY, JSON.stringify(next)); } catch { /* voll */ }
      return next;
    });
  }, []);

  const pushLog = useCallback((who: string, text: string) => {
    setLogs((prev) => {
      const next = [...prev, `[${timestamp()}] ${who.toUpperCase()} > ${text}`];
      return next.length > MAX_LOG_LINES ? next.slice(next.length - MAX_LOG_LINES) : next;
    });
  }, []);

  const handleEvent = useCallback((ev: AgentEvent, ctx: { goal: string; score: number | null; final: string }) => {
    const now = Date.now();
    totalEventsRef.current += 1;
    eventTimesRef.current = [...eventTimesRef.current.filter((t) => now - t < 10_000), now];

    switch (ev.type) {
      case "status":
        setStatuses((s) => ({ ...s, [ev.agent]: { status: ev.status, message: ev.message } }));
        pushLog(ev.agent, ev.message);
        break;
      case "output":
        setOutputs((o) => ({ ...o, [ev.agent]: ev.content }));
        pushLog(ev.agent, `Ausgabe empfangen (${ev.content.length} Zeichen)`);
        break;
      case "score":
        ctx.score = ev.score;
        setScore(ev.score);
        setImprovements(ev.improvements);
        pushLog("quality", `Score ${ev.score}/100`);
        break;
      case "final":
        ctx.final = ev.content;
        setFinalResult(ev.content);
        pushLog("commander", "Finales Ergebnis uebermittelt");
        break;
      case "error":
        setError(ev.message);
        if (ev.agent) setStatuses((s) => ({ ...s, [ev.agent as AgentRole]: { status: "error", message: ev.message } }));
        pushLog(ev.agent ?? "system", `FEHLER: ${ev.message}`);
        break;
    }
  }, [pushLog]);

  const startMission = useCallback(async () => {
    const missionGoal = goal.trim();
    if (!missionGoal || running) return;
    // Optimistische UI-Reaktion (<100ms): Status, Log und Timer sofort setzen.
    setRunning(true);
    setError("");
    setFinalResult("");
    setScore(null);
    setImprovements([]);
    setOutputs({});
    setOpenOutput(null);
    setLogs([`[${timestamp()}] SYSTEM > Mission gestartet: ${missionGoal}`]);
    setStartedAt(Date.now());
    eventTimesRef.current = [];
    totalEventsRef.current = 0;
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
  const toggleOutput = useCallback(
    (role: AgentRole) => setOpenOutput((prev) => (prev === role ? null : role)),
    [],
  );

  const activeAgents = useMemo(
    () => Object.values(statuses).filter((s) => s.status === "working").length,
    [statuses],
  );
  const missionCount = history.length + (running ? 1 : 0);
  const agentRoles = useMemo(() => Object.keys(AGENT_META) as AgentRole[], []);

  return (
    <main className="relative min-h-screen bg-[#0b0a08] text-[#e8dcc8]">
      {fancy && <div className="hud-texture" aria-hidden />}

      <header className="sticky top-0 z-20 border-b border-[#ff8c2a]/15 bg-[#0b0a08]/85 backdrop-blur">
        <div className="mx-auto flex min-h-16 max-w-7xl flex-wrap items-center justify-between gap-3 px-5 py-2">
          <div>
            <a href="/" className="text-lg font-bold tracking-tight text-[#fff3e2]">
              AI <span className="text-[#ff8c2a]">Command Center</span>
            </a>
            <div className="hud-label">Mission Control // Online</div>
          </div>
          <div className="flex items-center gap-3">
            {isBusiness && (
              <span className="hidden rounded-sm border border-[#ffd257]/50 bg-[#ffd257]/10 px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-[#ffd257] sm:inline">
                Team-Arbeitsbereich
              </span>
            )}
            <div className="flex overflow-hidden rounded-sm border border-[#ff8c2a]/30" role="group" aria-label="Abo-Stufe">
              {PLANS.map((p) => (
                <button
                  key={p}
                  onClick={() => selectPlan(p)}
                  aria-pressed={plan === p}
                  className={`px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] transition-colors ${
                    plan === p
                      ? p === "BUSINESS"
                        ? "bg-[#ffd257] text-[#1a0f04]"
                        : "bg-[#ff8c2a] text-[#1a0f04]"
                      : "text-[#ffb35c]/70 hover:bg-[#ff8c2a]/10"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      <div className={`relative z-10 mx-auto max-w-7xl px-5 py-8 ${isBusiness ? "pb-16" : ""}`}>
        <div className={isBusiness ? "hud-gold-frame rounded-sm p-4 sm:p-6" : ""}>
          {/* Eingabe */}
          <section aria-label="Neue Mission" className={fancy ? "hud-panel hud-corners rounded-sm p-5" : ""}>
            {fancy && <div className="hud-label mb-2">Mission Input</div>}
            <h1 className="text-2xl font-bold text-[#fff3e2]">Was soll Ihre KI-Abteilung erledigen?</h1>
            <p className="mt-1 text-sm text-[#c9b391]">
              Commander plant, Builder und Analyst arbeiten parallel, Quality prueft. Sie erhalten ein fertiges Ergebnis.
            </p>
            <div className="mt-5 flex flex-col gap-3 sm:flex-row">
              <input
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && startMission()}
                placeholder='z. B. "Erstelle eine Marketingstrategie fuer eine Zuercher Baeckerei"'
                disabled={running}
                className="flex-1 rounded-sm border border-[#ff8c2a]/25 bg-[#ff8c2a]/[0.04] px-4 py-3 text-[#fff3e2] placeholder:text-[#8a7455] outline-none transition focus:border-[#ff8c2a]/70 focus:ring-2 focus:ring-[#ff8c2a]/20"
              />
              {running ? (
                <button onClick={stopMission} className="rounded-sm border border-red-400/40 px-6 py-3 font-semibold text-red-300 transition hover:bg-red-400/10 active:scale-[0.98]">
                  Abbrechen
                </button>
              ) : (
                <button onClick={startMission} disabled={!goal.trim()} className="rounded-sm bg-[#ff8c2a] px-6 py-3 font-semibold text-[#1a0f04] transition hover:bg-[#ffb35c] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40">
                  Mission starten
                </button>
              )}
            </div>
            {error && (
              <p role="alert" className="mt-3 rounded-sm border border-red-400/30 bg-red-400/10 px-4 py-2 text-sm text-red-300">
                {error}
              </p>
            )}
          </section>

          {/* HUD-Zentrum: Telemetrie / Globus / Gauge */}
          {(showTelemetry || showGlobe || showGauge) && (
            <section aria-label="HUD" className="mt-8 grid grid-cols-1 items-center gap-6 lg:grid-cols-3">
              {showTelemetry ? (
                <TelemetryTiles
                  missions={missionCount}
                  activeAgents={activeAgents}
                  totalAgents={totalAgents}
                  running={running}
                  startedAt={startedAt}
                  eventTimesRef={eventTimesRef}
                />
              ) : <div />}
              {showGlobe ? (
                <div className="text-center">
                  <WireframeGlobe />
                  <div className="hud-label mt-2">Orbital Uplink // {running ? "Mission aktiv" : "Standby"}</div>
                </div>
              ) : <div />}
              {showGauge ? (
                <div className="hud-panel hud-corners rounded-sm p-4 text-center lg:justify-self-end">
                  <div className="hud-label mb-1">Quality Score</div>
                  <RadialGauge score={score} />
                </div>
              ) : <div />}
            </section>
          )}

          {/* Agenten-Status */}
          <section aria-label="Agenten-Status" className="mt-8">
            {fancy && <div className="hud-label mb-3">Einheiten // Agenten-Status</div>}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {agentRoles.map((role) => (
                <AgentCard
                  key={role}
                  role={role}
                  name={AGENT_META[role].name}
                  tagline={AGENT_META[role].tagline}
                  status={statuses[role].status}
                  message={statuses[role].message}
                  hasOutput={Boolean(outputs[role])}
                  isOpen={openOutput === role}
                  onToggle={toggleOutput}
                  fancy={fancy}
                />
              ))}
              {showExtraAgents &&
                EXTRA_AGENTS.map((a) => <ExtraAgentCard key={a.name} name={a.name} tagline={a.tagline} />)}
            </div>
          </section>

          {openOutput && outputs[openOutput] && (
            <section aria-label="Agenten-Ausgabe" className={`mt-4 rounded-sm border border-[#ff8c2a]/20 bg-[#ff8c2a]/[0.02] p-5 text-sm leading-relaxed ${fancy ? "hud-corners relative" : ""}`}>
              <h3 className="mb-2 font-semibold text-[#fff3e2]">{AGENT_META[openOutput].name}: Rohausgabe</h3>
              <div className="max-h-72 overflow-y-auto whitespace-pre-wrap text-[#e8dcc8]">{outputs[openOutput]}</div>
            </section>
          )}

          {/* Terminal-Feed (PROFESSIONAL+) */}
          {showFeed && <TerminalFeed logs={logs} />}

          {/* Quality-Score als Text (unterhalb PROFESSIONAL) */}
          {!showGauge && score !== null && (
            <section aria-label="Qualitaetsbewertung" className="mt-8 rounded-sm border border-[#ff8c2a]/20 bg-[#ff8c2a]/[0.02] p-5">
              <div className="flex items-center gap-4">
                <div className={`font-mono text-3xl font-extrabold ${score >= 80 ? "text-[#ffb35c]" : score >= 60 ? "text-amber-400" : "text-red-400"}`}>{score}/100</div>
                <div className="text-sm text-[#c9b391]">Bewertung durch Quality AI</div>
              </div>
            </section>
          )}
          {improvements.length > 0 && (
            <section aria-label="Verbesserungen" className={`mt-4 rounded-sm border border-[#ff8c2a]/15 bg-[#ff8c2a]/[0.02] p-5 ${fancy ? "hud-corners relative" : ""}`}>
              <div className={fancy ? "hud-label mb-2" : "mb-2 text-sm font-semibold text-[#fff3e2]"}>Verbesserungsvorschlaege</div>
              <ul className="space-y-1 text-sm text-[#e8dcc8]">
                {improvements.map((imp, i) => (
                  <li key={i} className="ml-5 list-disc">{imp}</li>
                ))}
              </ul>
            </section>
          )}

          {/* Finales Ergebnis */}
          {finalResult && (
            <section aria-label="Ergebnis" className={`mt-8 rounded-sm border border-[#ff8c2a]/30 bg-gradient-to-b from-[#ff8c2a]/[0.07] to-transparent p-6 ${fancy ? "hud-corners relative" : ""}`}>
              {fancy && <div className="hud-label mb-1">Mission Complete</div>}
              <h2 className="text-lg font-bold text-[#fff3e2]">Ergebnis Ihrer KI-Abteilung</h2>
              <div className="mt-3 text-sm leading-relaxed text-[#e8dcc8]">{renderMarkdown(finalResult)}</div>
            </section>
          )}

          {/* Verlauf */}
          {history.length > 0 && (
            <section aria-label="Missionsverlauf" className="mt-12">
              <h2 className="hud-label mb-3">Verlauf</h2>
              <ul className="space-y-2">
                {history.map((h, i) => (
                  <li key={i}>
                    <button
                      onClick={() => { setFinalResult(h.final); setScore(h.score); setImprovements([]); setError(""); }}
                      className="w-full rounded-sm border border-[#ff8c2a]/15 bg-[#ff8c2a]/[0.02] px-4 py-3 text-left text-sm transition hover:border-[#ff8c2a]/50"
                    >
                      <span className="font-medium text-[#fff3e2]">{h.goal}</span>
                      <span className="ml-2 font-mono text-xs text-[#8a7455]">
                        {new Date(h.at).toLocaleString("de-CH")} {h.score !== null ? `· ${h.score}/100` : ""}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      </div>

      {isBusiness && (
        <BusinessTicker
          running={running}
          startedAt={startedAt}
          activeAgents={activeAgents}
          totalAgents={totalAgents}
          missions={missionCount}
          totalEventsRef={totalEventsRef}
        />
      )}
    </main>
  );
}
