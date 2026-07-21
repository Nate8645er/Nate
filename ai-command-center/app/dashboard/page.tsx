"use client";

/**
 * Mission Control Dashboard — JARVIS Command Center HUD.
 *
 * Startet Missionen gegen POST /api/mission und rendert den SSE-Stream
 * (AgentEvent) live: Status je Agent, Terminal-Feed, Telemetrie,
 * Quality-Gauge und finales Ergebnis. Verlauf + Plan in localStorage.
 *
 * Abo-Stufen (FREE/STARTER/PROFESSIONAL/BUSINESS) schalten HUD-Module
 * frei; Stufen oberhalb der lizenzierten Stufe (Lizenz-Modal, POST
 * /api/license) sind gesperrt. Branchen-Onboarding-Modal liefert den
 * Mission-Kontext, das SSE-Event "usage" den Tageszähler im Header.
 *
 * TODO Phase 2: Verlauf + Plan serverseitig je Benutzer persistieren.
 */

import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { AgentEvent, AgentRole, AgentStatus, ArtifactFile } from "@/lib/agents/types";

/* ------------------------------- Konstanten ------------------------------- */

const AGENT_META: Record<AgentRole, { name: string; tagline: string }> = {
  commander: { name: "Commander", tagline: "Der digitale CEO" },
  builder: { name: "Builder", tagline: "Der Entwickler" },
  analyst: { name: "Analyst", tagline: "Der Stratege" },
  quality: { name: "Quality", tagline: "Der Prüfer" },
  marketing: { name: "Marketing", tagline: "Kampagnen & Content" },
  coding: { name: "Coding", tagline: "Software & Automation" },
  research: { name: "Research", tagline: "Tiefenrecherche" },
  business: { name: "Business", tagline: "Strategie & Finanzen" },
};

/** Kern-Team (immer aktiv). */
const BASE_ROLES: readonly AgentRole[] = ["commander", "builder", "analyst", "quality"];
/** Zusatz-Worker: ab PROFESSIONAL sichtbar/aktiv, darunter "Ab Professional". */
const EXTRA_ROLES: readonly AgentRole[] = ["marketing", "research", "coding", "business"];
/** Zusatz-Worker, die erst ab BUSINESS mitarbeiten. */
const BUSINESS_ONLY_ROLES: ReadonlySet<AgentRole> = new Set(["coding", "business"]);

const ALL_ROLES: readonly AgentRole[] = [...BASE_ROLES, ...EXTRA_ROLES];

function initialStatuses(): Record<AgentRole, { status: AgentStatus; message: string }> {
  return Object.fromEntries(
    ALL_ROLES.map((role) => [role, { status: "idle", message: "Bereit" }]),
  ) as Record<AgentRole, { status: AgentStatus; message: string }>;
}

const STATUS_LABEL: Record<AgentStatus, string> = {
  idle: "Bereit",
  working: "Arbeitet",
  done: "Fertig",
  error: "Fehler",
};

type Plan = "FREE" | "STARTER" | "PROFESSIONAL" | "BUSINESS" | "ENTERPRISE";
const PLANS: Plan[] = ["FREE", "STARTER", "PROFESSIONAL", "BUSINESS", "ENTERPRISE"];
const PLAN_LEVEL: Record<Plan, number> = {
  FREE: 0,
  STARTER: 1,
  PROFESSIONAL: 2,
  BUSINESS: 3,
  ENTERPRISE: 4,
};

/**
 * Sichtbare Gesamt-Belegschaft je Plan (Spiegel von WORKFORCE_BY_PLAN in
 * lib/agents/team.ts – dient nur der Anzeige vor dem ersten org-Event; die
 * verbindliche Zahl liefert der Server im org-Event).
 */
const WORKFORCE_BY_PLAN: Record<Plan, number> = {
  FREE: 4,
  STARTER: 8,
  PROFESSIONAL: 24,
  BUSINESS: 150,
  ENTERPRISE: 1000,
};

/** Pläne im Organisations-Modus (dynamische Firma + Belegschaft). */
const ORG_MODE_PLANS: ReadonlySet<Plan> = new Set<Plan>(["BUSINESS", "ENTERPRISE"]);

/** Eine Abteilung der virtuellen Firma im Dashboard (aus dem org-Event). */
interface OrgDepartment {
  name: string;
  roles: { id: string; label: string }[];
  assistants: { id: string; label: string }[];
}
interface OrgState {
  workforce: number;
  departments: OrgDepartment[];
}
type DynStatus = { status: AgentStatus; message: string };

/** Dokumenten-Analyse: Upload-Limit und Client-Kappung (Server kappt erneut). */
const MAX_DOC_BYTES = 2 * 1024 * 1024;
const MAX_DOC_CHARS = 20_000;
/** Endungen, die der Client selbst per FileReader als Text liest. */
const TEXT_DOC_EXTENSIONS = new Set(["txt", "md", "csv", "html", "htm"]);

const HISTORY_KEY = "acc-mission-history";
const PLAN_KEY = "acc-plan";
/** Lizenz-Token (30 Tage, HMAC-signiert) aus POST /api/license. */
const LICENSE_TOKEN_KEY = "acc-license-token";
/** Usage-Token (Tageszähler), vom Server per SSE-Event "usage" erneuert. */
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
  /** Erzeugte Dateien der Mission (optional, ältere Einträge haben keine). */
  artifacts?: ArtifactFile[];
}

/** MIME-Typ je Sprache für den Datei-Download (sonst text/plain). */
const MIME_BY_LANGUAGE: Record<string, string> = {
  html: "text/html",
  css: "text/css",
  javascript: "application/javascript",
  typescript: "text/plain",
  json: "application/json",
  markdown: "text/markdown",
  xml: "application/xml",
  csv: "text/csv",
};

/** Basisname (ohne Verzeichnis) eines Pfads. */
function baseName(path: string): string {
  return path.split("/").pop() || path;
}

/** Findet die index.html unter den Dateien (für die Live-Vorschau). */
function findIndexHtml(files: readonly ArtifactFile[]): ArtifactFile | undefined {
  return files.find((f) => baseName(f.path).toLowerCase() === "index.html");
}

/**
 * HTML-Datei für die Live-Vorschau: index.html bevorzugt, sonst die erste
 * .html/.htm-Datei (z. B. praesentation.html).
 */
function findPreviewHtml(files: readonly ArtifactFile[]): ArtifactFile | undefined {
  return findIndexHtml(files) ?? files.find((f) => /\.html?$/i.test(baseName(f.path)));
}

/** Lädt eine einzelne Datei über einen Blob herunter. */
function downloadArtifact(file: ArtifactFile): void {
  const mime = MIME_BY_LANGUAGE[file.language] ?? "text/plain";
  const blob = new Blob([file.content], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = baseName(file.path) || "datei.txt";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

/** Lädt alle Dateien nacheinander herunter (leichte Staffelung für Browser). */
function downloadAllArtifacts(files: readonly ArtifactFile[]): void {
  files.forEach((file, i) => {
    window.setTimeout(() => downloadArtifact(file), i * 250);
  });
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
 * ANZEIGE. Die HMAC-Prüfung passiert ausschliesslich serverseitig.
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

/** Radial-HUD-Gauge für den Quality-Score (animierter Kreisbogen). */
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
  workforce,
  running,
  startedAt,
  eventTimesRef,
}: {
  missions: number;
  activeAgents: number;
  totalAgents: number;
  workforce: number;
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
    { label: "Belegschaft", value: workforce >= 1000 ? workforce.toLocaleString("de-CH") : String(workforce) },
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
  workforce,
  plan,
  totalEventsRef,
}: {
  running: boolean;
  startedAt: number | null;
  activeAgents: number;
  totalAgents: number;
  missions: number;
  workforce: number;
  plan: Plan;
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
    `WORKFORCE ${workforce.toLocaleString("de-CH")}`,
    `MISSIONS ${missions}`,
    `LINK ${running ? "ACTIVE" : "STABLE"}`,
    `PLAN ${plan}`,
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

/** Gesperrte Zusatz-Einheit (unterhalb PROFESSIONAL): Hinweis auf das Upgrade. */
const LockedAgentCard = memo(function LockedAgentCard({ name, tagline }: { name: string; tagline: string }) {
  return (
    <div className="relative rounded-sm border border-[#ff8c2a]/15 bg-[#ff8c2a]/[0.02] p-4 opacity-70">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-[#fff3e2]">{name}</h3>
        <span aria-hidden className="h-2 w-2 rounded-full bg-[#5a4a35]" />
      </div>
      <p className="hud-label mt-0.5">{tagline}</p>
      <p className="mt-3 text-sm">
        <span className="font-medium text-[#8a7455]">Gesperrt</span>
        <span className="text-[#c9b391]"> · Ab Professional</span>
      </p>
    </div>
  );
});

/** Status-Punkt-Klassen für die dynamischen Rollen im Organigramm. */
function dynDotClass(status: AgentStatus): string {
  return status === "working"
    ? "hud-pulse bg-[#ff8c2a]"
    : status === "done"
      ? "bg-[#ffb35c]"
      : status === "error"
        ? "bg-red-400"
        : "bg-[#5a4a35]";
}

/** Wie viele Belegschafts-Chips maximal eingeklappt sichtbar sind. */
const WORKFORCE_CHIP_PREVIEW = 12;

/** Eine Abteilung im Organigramm: echte Live-Rollen + gedimmte Belegschaft. */
const DepartmentCard = memo(function DepartmentCard({
  dept,
  dynStatuses,
}: {
  dept: OrgDepartment;
  dynStatuses: Record<string, DynStatus>;
}) {
  const [expanded, setExpanded] = useState(false);
  const total = dept.assistants.length;
  const shown = expanded ? dept.assistants : dept.assistants.slice(0, WORKFORCE_CHIP_PREVIEW);
  const rest = total - shown.length;

  return (
    <div className="hud-panel hud-corners rounded-sm p-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-[#fff3e2]">{dept.name}</h3>
        <span className="hud-label">{dept.roles.length} live · {total} Assist.</span>
      </div>

      {/* Echte, live-arbeitende Spezialisten */}
      <ul className="mt-3 space-y-1.5">
        {dept.roles.map((r) => {
          const st = dynStatuses[r.id]?.status ?? "idle";
          return (
            <li key={r.id} className="flex items-center gap-2 text-sm">
              <span aria-hidden className={`h-2 w-2 rounded-full ${dynDotClass(st)}`} />
              <span className="text-[#e8dcc8]">{r.label}</span>
              <span className="ml-auto font-mono text-[10px] uppercase tracking-[0.14em] text-[#ffb35c]/60">
                {STATUS_LABEL[st]}
              </span>
            </li>
          );
        })}
      </ul>

      {/* Belegschaft: statische Assistenten (keine LLM-Aufrufe) */}
      {total > 0 && (
        <div className="mt-4 border-t border-[#ff8c2a]/10 pt-3">
          <button
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
            className={`hud-label transition-colors hover:text-[#ff8c2a] ${FOCUS_RING}`}
          >
            Belegschaft: {total} {expanded ? "▲ einklappen" : "▼ anzeigen"}
          </button>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {shown.map((a) => (
              <span
                key={a.id}
                className="rounded-sm border border-[#ff8c2a]/12 bg-[#ff8c2a]/[0.03] px-2 py-0.5 font-mono text-[10px] text-[#ffb35c]/55"
              >
                {a.label}
              </span>
            ))}
            {!expanded && rest > 0 && (
              <span className="rounded-sm px-2 py-0.5 font-mono text-[10px] text-[#8a7455]">
                +{rest} weitere
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
});

/** Organigramm der virtuellen Firma (nur Org-Pläne). */
const OrgChart = memo(function OrgChart({
  org,
  dynStatuses,
}: {
  org: OrgState;
  dynStatuses: Record<string, DynStatus>;
}) {
  return (
    <section aria-label="Virtuelle Firma" className="mt-8">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="hud-label">Virtuelle Firma // Organigramm</div>
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-[#ffd257]/80">
          Belegschaft {org.workforce.toLocaleString("de-CH")}
        </div>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {org.departments.map((d) => (
          <DepartmentCard key={d.name} dept={d} dynStatuses={dynStatuses} />
        ))}
      </div>
    </section>
  );
});

/**
 * "Erzeugte Dateien": Datei-Liste links, Code-Ansicht rechts (monospace,
 * scrollbar). Pro Datei Download, "Alle herunterladen" und eine automatisch
 * geöffnete Live-Vorschau der ersten HTML-Datei via <iframe srcdoc>.
 */
const ArtifactViewer = memo(function ArtifactViewer({ files }: { files: ArtifactFile[] }) {
  const [activeIndex, setActiveIndex] = useState(0);
  // Vorschau automatisch geöffnet: das gebaute Ergebnis führt die Ansicht an.
  const [previewOpen, setPreviewOpen] = useState(true);
  const previewHtml = useMemo(() => findPreviewHtml(files), [files]);
  const active = files[Math.min(activeIndex, files.length - 1)] ?? files[0];

  if (!active) return null;

  return (
    <section aria-label="Erzeugte Dateien" className="mt-8">
      <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="hud-label">Erzeugte Dateien // Direkt verwendbar</div>
          <h2 className="mt-1 text-lg font-bold text-[#fff3e2]">Ihr Ergebnis: fertig gebaut</h2>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {previewHtml && (
            <button
              onClick={() => setPreviewOpen((v) => !v)}
              aria-pressed={previewOpen}
              className={`rounded-sm border border-[#ff8c2a]/40 bg-[#ff8c2a]/[0.06] px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-[#ff8c2a] transition-colors hover:bg-[#ff8c2a]/15 ${FOCUS_RING}`}
            >
              {previewOpen ? "Vorschau schliessen" : "Live-Vorschau"}
            </button>
          )}
          <button
            onClick={() => downloadAllArtifacts(files)}
            className={`rounded-sm bg-[#ff8c2a] px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] font-semibold text-[#1a0f04] transition hover:bg-[#ffb35c] active:scale-[0.98] ${FOCUS_RING}`}
          >
            Alle herunterladen ({files.length})
          </button>
        </div>
      </div>

      {/* Live-Vorschau der ersten HTML-Datei im HUD-Panel (automatisch offen) */}
      {previewHtml && previewOpen && (
        <div className="hud-panel hud-corners mb-4 rounded-sm">
          <div className="flex items-center justify-between border-b border-[#ff8c2a]/15 px-4 py-2">
            <span className="hud-label">Live-Vorschau // {baseName(previewHtml.path)}</span>
            <span className="hud-pulse h-1.5 w-1.5 rounded-full bg-[#ff8c2a]" aria-hidden />
          </div>
          <iframe
            title="Live-Vorschau"
            srcDoc={previewHtml.content}
            sandbox="allow-scripts"
            className="h-[420px] w-full rounded-b-sm border-0 bg-white"
          />
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(200px,260px)_1fr]">
        {/* Datei-Liste / Tabs */}
        <div className="hud-panel hud-corners rounded-sm p-2">
          <ul className="space-y-1">
            {files.map((f, i) => {
              const selected = f.path === active.path;
              return (
                <li key={f.path}>
                  <button
                    onClick={() => setActiveIndex(i)}
                    aria-pressed={selected}
                    className={`flex w-full items-center gap-2 rounded-sm px-3 py-2 text-left font-mono text-xs transition-colors ${FOCUS_RING} ${
                      selected
                        ? "bg-[#ff8c2a]/15 text-[#fff3e2]"
                        : "text-[#ffb35c]/70 hover:bg-[#ff8c2a]/[0.06]"
                    }`}
                  >
                    <span className="truncate">{f.path}</span>
                    <span className="ml-auto shrink-0 text-[9px] uppercase tracking-[0.14em] text-[#8a7455]">
                      {f.language}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        {/* Code-Ansicht */}
        <div className="hud-panel hud-corners flex min-w-0 flex-col rounded-sm">
          <div className="flex items-center justify-between border-b border-[#ff8c2a]/15 px-4 py-2">
            <span className="truncate font-mono text-xs text-[#e8dcc8]">{active.path}</span>
            <button
              onClick={() => downloadArtifact(active)}
              className={`shrink-0 rounded-sm bg-[#ff8c2a] px-3 py-1 font-mono text-[10px] uppercase tracking-[0.14em] font-semibold text-[#1a0f04] transition hover:bg-[#ffb35c] active:scale-[0.98] ${FOCUS_RING}`}
            >
              Herunterladen
            </button>
          </div>
          <pre className="max-h-[420px] overflow-auto px-4 py-3 font-mono text-[11px] leading-5 text-[#e8dcc8]">
            <code>{active.content}</code>
          </pre>
        </div>
      </div>
    </section>
  );
});

/* --------------------------------- Modals --------------------------------- */

/** Fokus-Ring für Tastaturbedienung (focus-visible) im HUD-Stil. */
const FOCUS_RING =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#ff8c2a]/70";

/** Kleines Schloss-Symbol für gesperrte Plan-Stufen. */
const LockIcon = memo(function LockIcon() {
  return (
    <svg viewBox="0 0 12 12" className="h-2.5 w-2.5" aria-hidden fill="none" stroke="currentColor" strokeWidth="1.3">
      <rect x="2" y="5.2" width="8" height="5.3" rx="0.8" />
      <path d="M3.8 5.2V3.8a2.2 2.2 0 0 1 4.4 0v1.4" />
    </svg>
  );
});

/**
 * HUD-Modal-Shell: role=dialog, Escape schliesst, Klick auf den Hintergrund
 * schliesst, Fokus springt beim Öffnen in den Dialog und danach zurück.
 */
function HudModal({
  labelId,
  onClose,
  children,
}: {
  labelId: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  const dialogRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const previous = document.activeElement;
    dialogRef.current?.focus();
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      if (previous instanceof HTMLElement) previous.focus();
    };
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelId}
        tabIndex={-1}
        className="hud-panel hud-corners hud-modal-in relative w-full max-w-lg rounded-sm border border-[#ff8c2a]/30 bg-[#0b0a08] p-6 outline-none"
      >
        <button
          onClick={onClose}
          aria-label="Schliessen"
          className={`absolute right-3 top-3 rounded-sm px-2 py-1 font-mono text-xs text-[#ffb35c]/70 transition hover:text-[#fff3e2] ${FOCUS_RING}`}
        >
          ✕
        </button>
        {children}
      </div>
    </div>
  );
}

/** Auswahl-Button (Branche/Grösse) im Onboarding-Modal. */
const ChoiceButton = memo(function ChoiceButton({
  label,
  selected,
  onSelect,
}: {
  label: string;
  selected: boolean;
  onSelect: (label: string) => void;
}) {
  return (
    <button
      onClick={() => onSelect(label)}
      aria-pressed={selected}
      className={`rounded-sm border px-3 py-2.5 text-sm transition-colors ${FOCUS_RING} ${
        selected
          ? "border-[#ff8c2a] bg-[#ff8c2a]/15 text-[#fff3e2]"
          : "border-[#ff8c2a]/25 bg-[#ff8c2a]/[0.03] text-[#e8dcc8] hover:border-[#ff8c2a]/60"
      }`}
    >
      {label}
    </button>
  );
});

/** Branchen-Onboarding: Branche + Unternehmensgrösse wählen. */
function OnboardingModal({
  initialBranche,
  initialGroesse,
  onConfirm,
  onClose,
}: {
  initialBranche: string | null;
  initialGroesse: string | null;
  onConfirm: (branche: string, groesse: string) => void;
  onClose: () => void;
}) {
  const [branche, setBranche] = useState<string | null>(initialBranche);
  const [groesse, setGroesse] = useState<string | null>(initialGroesse);

  return (
    <HudModal labelId="onboarding-title" onClose={onClose}>
      <div className="hud-label mb-1">Onboarding // Kontext</div>
      <h2 id="onboarding-title" className="text-xl font-bold text-[#fff3e2]">Ihr Unternehmen</h2>
      <p className="mt-1 text-sm text-[#c9b391]">
        Ihre KI-Abteilung passt Pläne und Ergebnisse an Branche und Teamgrösse an.
      </p>

      <div className="hud-label mt-5 mb-2">Branche</div>
      <div className="grid grid-cols-2 gap-2">
        {BRANCHEN.map((b) => (
          <ChoiceButton key={b} label={b} selected={branche === b} onSelect={setBranche} />
        ))}
      </div>

      <div className="hud-label mt-5 mb-2">Unternehmensgrösse</div>
      <div className="grid grid-cols-4 gap-2">
        {GROESSEN.map((g) => (
          <ChoiceButton key={g} label={g} selected={groesse === g} onSelect={setGroesse} />
        ))}
      </div>

      <button
        onClick={() => branche && groesse && onConfirm(branche, groesse)}
        disabled={!branche || !groesse}
        className={`mt-6 w-full rounded-sm bg-[#ff8c2a] px-6 py-3 font-semibold text-[#1a0f04] transition hover:bg-[#ffb35c] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 ${FOCUS_RING}`}
      >
        Start
      </button>
    </HudModal>
  );
}

/** Lizenz-Aktivierung: Schlüssel eingeben, gegen POST /api/license tauschen. */
function LicenseModal({
  licensedPlan,
  onActivated,
  onClose,
}: {
  licensedPlan: Plan;
  onActivated: (plan: Plan, token: string) => void;
  onClose: () => void;
}) {
  const [key, setKey] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const activate = useCallback(async () => {
    const trimmed = key.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    setError("");
    try {
      const res = await fetch("/api/license", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: trimmed }),
      });
      const data = (await res.json().catch(() => null)) as
        | { valid?: boolean; plan?: string; token?: string; error?: string }
        | null;
      if (
        res.ok &&
        data?.valid &&
        typeof data.token === "string" &&
        typeof data.plan === "string" &&
        (PLANS as string[]).includes(data.plan)
      ) {
        onActivated(data.plan as Plan, data.token);
      } else {
        setError(data?.error ?? "Ungültiger Lizenzschlüssel.");
      }
    } catch {
      setError("Verbindung fehlgeschlagen. Bitte erneut versuchen.");
    } finally {
      setBusy(false);
    }
  }, [key, busy, onActivated]);

  return (
    <HudModal labelId="license-title" onClose={onClose}>
      <div className="hud-label mb-1">Zugang // Freischaltung</div>
      <h2 id="license-title" className="text-xl font-bold text-[#fff3e2]">Lizenz aktivieren</h2>
      <p className="mt-1 text-sm text-[#c9b391]">
        {licensedPlan === "FREE"
          ? "Geben Sie Ihren Lizenzschlüssel ein, um STARTER, PROFESSIONAL oder BUSINESS freizuschalten."
          : `Aktive Lizenz: ${licensedPlan}. Ein neuer Schlüssel ersetzt die aktuelle Lizenz.`}
      </p>
      <div className="mt-5 flex flex-col gap-3 sm:flex-row">
        <input
          value={key}
          onChange={(e) => setKey(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && activate()}
          placeholder="ACC-STARTER-..."
          disabled={busy}
          aria-label="Lizenzschlüssel"
          className={`flex-1 rounded-sm border border-[#ff8c2a]/25 bg-[#ff8c2a]/[0.04] px-4 py-3 font-mono text-sm text-[#fff3e2] placeholder:text-[#8a7455] outline-none transition focus:border-[#ff8c2a]/70 focus:ring-2 focus:ring-[#ff8c2a]/20 ${FOCUS_RING}`}
        />
        <button
          onClick={activate}
          disabled={!key.trim() || busy}
          className={`rounded-sm bg-[#ff8c2a] px-6 py-3 font-semibold text-[#1a0f04] transition hover:bg-[#ffb35c] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 ${FOCUS_RING}`}
        >
          {busy ? "Prüfe ..." : "Aktivieren"}
        </button>
      </div>
      {error && (
        <p role="alert" className="mt-3 rounded-sm border border-red-400/30 bg-red-400/10 px-4 py-2 text-sm text-red-300">
          {error}
        </p>
      )}
    </HudModal>
  );
}

/** Liest eine Textdatei per FileReader (Dokumenten-Analyse, TXT/MD/CSV/HTML). */
function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(typeof reader.result === "string" ? reader.result : "");
    reader.onerror = () => reject(reader.error ?? new Error("Datei konnte nicht gelesen werden."));
    reader.readAsText(file);
  });
}

/* --------------------------------- Seite ---------------------------------- */

export default function DashboardPage() {
  const [goal, setGoal] = useState("");
  const [running, setRunning] = useState(false);
  const [plan, setPlan] = useState<Plan>("FREE");
  /** Per Lizenz-Token freigeschalteter Plan; ohne Token FREE. */
  const [licensedPlan, setLicensedPlan] = useState<Plan>("FREE");
  const [licenseToken, setLicenseToken] = useState<string | null>(null);
  const [usageToken, setUsageToken] = useState<string | null>(null);
  const [usage, setUsage] = useState<{ used: number; limit: number } | null>(null);
  const [branche, setBranche] = useState<string | null>(null);
  const [groesse, setGroesse] = useState<string | null>(null);
  const [onboardingOpen, setOnboardingOpen] = useState(false);
  const [licenseOpen, setLicenseOpen] = useState(false);
  const [statuses, setStatuses] = useState<Record<AgentRole, { status: AgentStatus; message: string }>>(initialStatuses);
  const [outputs, setOutputs] = useState<Partial<Record<AgentRole, string>>>({});
  const [score, setScore] = useState<number | null>(null);
  const [improvements, setImprovements] = useState<string[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactFile[]>([]);
  const [finalResult, setFinalResult] = useState("");
  const [error, setError] = useState("");
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [openOutput, setOpenOutput] = useState<AgentRole | null>(null);
  const [org, setOrg] = useState<OrgState | null>(null);
  const [dynStatuses, setDynStatuses] = useState<Record<string, DynStatus>>({});
  const [logs, setLogs] = useState<string[]>([]);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  /** Angehängtes Dokument (Dokumenten-Analyse) für die nächste Mission. */
  const [dokument, setDokument] = useState<{ name: string; text: string } | null>(null);
  const [docBusy, setDocBusy] = useState(false);
  const [docError, setDocError] = useState("");
  const fileInputRef = useRef<HTMLInputElement | null>(null);
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
  const isOrgPlan = ORG_MODE_PLANS.has(plan);
  const fancy = level >= 1;
  // Belegschaft: verbindlich aus dem org-Event, sonst der Plan-Erwartungswert.
  const workforce = org?.workforce ?? WORKFORCE_BY_PLAN[plan];
  const dynRoleCount = useMemo(
    () => (org ? org.departments.reduce((n, d) => n + d.roles.length, 0) : 0),
    [org],
  );
  // Org-Modus zählt echte, LLM-aufrufende Rollen (+ Commander/Quality).
  const totalAgents = isOrgPlan
    ? (org ? dynRoleCount + 2 : 2)
    : showExtraAgents
      ? 8
      : 4;

  useEffect(() => {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      if (raw) setHistory(JSON.parse(raw) as HistoryEntry[]);

      // Lizenz-Token lesen (nur Anzeige; die HMAC-Prüfung macht der Server).
      let licensed: Plan = "FREE";
      const storedToken = localStorage.getItem(LICENSE_TOKEN_KEY);
      if (storedToken) {
        const payload = decodeTokenPayload(storedToken);
        const p = payload?.p;
        const exp = payload?.exp;
        if (
          typeof p === "string" && (PLANS as string[]).includes(p) &&
          typeof exp === "number" && exp > Date.now()
        ) {
          licensed = p as Plan;
          setLicensedPlan(licensed);
          setLicenseToken(storedToken);
        } else {
          localStorage.removeItem(LICENSE_TOKEN_KEY);
        }
      }

      // Gewählten Plan laden, aber auf die lizenzierte Stufe begrenzen.
      const storedPlan = localStorage.getItem(PLAN_KEY);
      if (storedPlan && (PLANS as string[]).includes(storedPlan)) {
        const wanted = storedPlan as Plan;
        setPlan(PLAN_LEVEL[wanted] > PLAN_LEVEL[licensed] ? licensed : wanted);
      }

      // Usage-Token nur weiterverwenden, wenn es vom heutigen UTC-Tag stammt.
      const storedUsage = localStorage.getItem(USAGE_TOKEN_KEY);
      if (storedUsage) {
        const payload = decodeTokenPayload(storedUsage);
        if (payload?.d === new Date().toISOString().slice(0, 10)) {
          setUsageToken(storedUsage);
        } else {
          localStorage.removeItem(USAGE_TOKEN_KEY);
        }
      }

      // Branchen-Onboarding: ohne gespeicherte Branche Modal öffnen.
      const storedBranche = localStorage.getItem(BRANCHE_KEY);
      const storedGroesse = localStorage.getItem(GROESSE_KEY);
      if (storedBranche) setBranche(storedBranche);
      if (storedGroesse) setGroesse(storedGroesse);
      if (!storedBranche) setOnboardingOpen(true);
    } catch { /* korrupter Zustand wird ignoriert */ }
  }, []);

  const selectPlan = useCallback((p: Plan) => {
    setPlan(p);
    try { localStorage.setItem(PLAN_KEY, p); } catch { /* voll */ }
  }, []);

  /** Plan-Schalter: gesperrte Stufen öffnen das Lizenz-Modal. */
  const handlePlanClick = useCallback((p: Plan) => {
    if (PLAN_LEVEL[p] > PLAN_LEVEL[licensedPlan]) {
      setLicenseOpen(true);
      return;
    }
    selectPlan(p);
  }, [licensedPlan, selectPlan]);

  const confirmOnboarding = useCallback((b: string, g: string) => {
    setBranche(b);
    setGroesse(g);
    setOnboardingOpen(false);
    try {
      localStorage.setItem(BRANCHE_KEY, b);
      localStorage.setItem(GROESSE_KEY, g);
    } catch { /* voll */ }
  }, []);

  const handleLicenseActivated = useCallback((p: Plan, token: string) => {
    setLicensedPlan(p);
    setLicenseToken(token);
    setLicenseOpen(false);
    // Plan-Schalter springt direkt auf die frisch lizenzierte Stufe.
    setPlan(p);
    try {
      localStorage.setItem(LICENSE_TOKEN_KEY, token);
      localStorage.setItem(PLAN_KEY, p);
    } catch { /* voll */ }
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

  const handleEvent = useCallback((ev: AgentEvent, ctx: { goal: string; score: number | null; final: string; artifacts: ArtifactFile[] }) => {
    const now = Date.now();
    totalEventsRef.current += 1;
    eventTimesRef.current = [...eventTimesRef.current.filter((t) => now - t < 10_000), now];

    switch (ev.type) {
      case "org": {
        // Firma übernehmen; Live-Rollen zunächst auf "Bereit" setzen.
        setOrg({ workforce: ev.workforce, departments: ev.departments });
        const roleCount = ev.departments.reduce((n, d) => n + d.roles.length, 0);
        const seed: Record<string, DynStatus> = {};
        for (const d of ev.departments) {
          for (const r of d.roles) seed[r.id] = { status: "idle", message: "Bereit" };
        }
        setDynStatuses(seed);
        pushLog("commander", `Firma gegründet: ${ev.departments.length} Abteilungen, ${roleCount} Rollen, Belegschaft ${ev.workforce}`);
        break;
      }
      case "status":
        if (typeof ev.agent === "string" && ev.agent.startsWith("dyn:")) {
          setDynStatuses((s) => ({ ...s, [ev.agent]: { status: ev.status, message: ev.message } }));
        } else {
          setStatuses((s) => ({ ...s, [ev.agent]: { status: ev.status, message: ev.message } }));
        }
        pushLog(ev.label ?? ev.agent, ev.message);
        break;
      case "output":
        if (!(typeof ev.agent === "string" && ev.agent.startsWith("dyn:"))) {
          setOutputs((o) => ({ ...o, [ev.agent]: ev.content }));
        }
        pushLog(ev.label ?? ev.agent, `Ausgabe empfangen (${ev.content.length} Zeichen)`);
        break;
      case "score":
        ctx.score = ev.score;
        setScore(ev.score);
        setImprovements(ev.improvements);
        pushLog("quality", `Score ${ev.score}/100`);
        break;
      case "artifact":
        ctx.artifacts = ev.files;
        setArtifacts(ev.files);
        pushLog("builder", `${ev.files.length} Datei(en) erzeugt: ${ev.files.map((f) => f.path).join(", ")}`);
        break;
      case "final":
        ctx.final = ev.content;
        setFinalResult(ev.content);
        pushLog("commander", "Finales Ergebnis übermittelt");
        break;
      case "usage":
        // Neu signierten Tageszähler übernehmen und für den nächsten
        // Start als Header "x-acc-usage" bereithalten.
        setUsage({ used: ev.used, limit: ev.limit });
        setUsageToken(ev.token);
        try { localStorage.setItem(USAGE_TOKEN_KEY, ev.token); } catch { /* voll */ }
        break;
      case "error":
        setError(ev.message);
        if (ev.agent) setStatuses((s) => ({ ...s, [ev.agent as AgentRole]: { status: "error", message: ev.message } }));
        pushLog(ev.agent ?? "system", `FEHLER: ${ev.message}`);
        break;
    }
  }, [pushLog]);

  /**
   * Dokumenten-Analyse: liest .txt/.md/.csv/.html direkt per FileReader,
   * schickt PDFs an POST /api/extract und hängt den Text (gekappt auf
   * MAX_DOC_CHARS) als Dokument an die nächste Mission.
   */
  const attachDocument = useCallback(async (file: File) => {
    setDocError("");
    if (file.size > MAX_DOC_BYTES) {
      setDocError("Datei zu gross – maximal 2 MB.");
      return;
    }
    const ext = file.name.toLowerCase().split(".").pop() ?? "";
    setDocBusy(true);
    try {
      let text: string;
      if (ext === "pdf") {
        const form = new FormData();
        form.append("file", file);
        const res = await fetch("/api/extract", { method: "POST", body: form });
        const data = (await res.json().catch(() => null)) as { text?: string; error?: string } | null;
        if (!res.ok) throw new Error(data?.error ?? `Server antwortete mit ${res.status}`);
        text = data?.text ?? "";
      } else if (TEXT_DOC_EXTENSIONS.has(ext)) {
        text = await readFileAsText(file);
      } else {
        setDocError("Nur .txt, .md, .csv, .html oder .pdf werden unterstützt.");
        return;
      }
      const clean = text.trim().slice(0, MAX_DOC_CHARS);
      if (!clean) {
        setDocError("Im Dokument wurde kein Text gefunden.");
        return;
      }
      setDokument({ name: file.name.slice(0, 80), text: clean });
    } catch (err) {
      setDocError(err instanceof Error ? err.message : "Dokument konnte nicht gelesen werden.");
    } finally {
      setDocBusy(false);
    }
  }, []);

  const removeDocument = useCallback(() => {
    setDokument(null);
    setDocError("");
  }, []);

  const startMission = useCallback(async () => {
    const missionGoal = goal.trim();
    if (!missionGoal || running) return;
    // Optimistische UI-Reaktion (<100ms): Status, Log und Timer sofort setzen.
    setRunning(true);
    setError("");
    setFinalResult("");
    setScore(null);
    setImprovements([]);
    setArtifacts([]);
    setOutputs({});
    setOpenOutput(null);
    setOrg(null);
    setDynStatuses({});
    setLogs([`[${timestamp()}] SYSTEM > Mission gestartet: ${missionGoal}`]);
    setStartedAt(Date.now());
    eventTimesRef.current = [];
    totalEventsRef.current = 0;
    // Fan-out bestimmt SERVERSEITIG das Lizenz-Token (licensedPlan) –
    // Zusatz-Worker ohne Freischaltung bleiben sichtbar im Standby.
    const licLevel = PLAN_LEVEL[licensedPlan];
    const extraReset = (role: AgentRole): { status: AgentStatus; message: string } => {
      const active = BUSINESS_ONLY_ROLES.has(role) ? licLevel >= 3 : licLevel >= 2;
      if (active) return { status: "idle", message: "Wartet auf den Plan" };
      return {
        status: "idle",
        message: BUSINESS_ONLY_ROLES.has(role) && licLevel >= 2 ? "Ab Business" : "Ab Professional",
      };
    };
    setStatuses({
      commander: { status: "working", message: "Analysiert die Aufgabe" },
      builder: { status: "idle", message: "Wartet auf den Plan" },
      analyst: { status: "idle", message: "Wartet auf den Plan" },
      quality: { status: "idle", message: "Wartet auf Ergebnisse" },
      marketing: extraReset("marketing"),
      research: extraReset("research"),
      coding: extraReset("coding"),
      business: extraReset("business"),
    });

    const ctx = { goal: missionGoal, score: null as number | null, final: "", artifacts: [] as ArtifactFile[] };
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (licenseToken) headers["x-acc-license"] = licenseToken;
      if (usageToken) headers["x-acc-usage"] = usageToken;
      const res = await fetch("/api/mission", {
        method: "POST",
        headers,
        body: JSON.stringify({
          goal: missionGoal,
          ...((branche && groesse) || dokument
            ? {
                context: {
                  ...(branche && groesse ? { branche, groesse } : {}),
                  ...(dokument ? { dokument } : {}),
                },
              }
            : {}),
        }),
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
          } catch { /* defektes Event überspringen */ }
        }
      }
      if (ctx.final) {
        saveHistory({
          goal: missionGoal,
          final: ctx.final,
          score: ctx.score,
          at: new Date().toISOString(),
          ...(ctx.artifacts.length ? { artifacts: ctx.artifacts } : {}),
        });
      }
    } catch (err) {
      if (!(err instanceof DOMException && err.name === "AbortError")) {
        setError(err instanceof Error ? err.message : "Unbekannter Fehler.");
      }
    } finally {
      setRunning(false);
      abortRef.current = null;
    }
  }, [goal, running, handleEvent, saveHistory, licenseToken, licensedPlan, usageToken, branche, groesse, dokument]);

  const stopMission = useCallback(() => abortRef.current?.abort(), []);
  const toggleOutput = useCallback(
    (role: AgentRole) => setOpenOutput((prev) => (prev === role ? null : role)),
    [],
  );

  const activeAgents = useMemo(
    () =>
      Object.values(statuses).filter((s) => s.status === "working").length +
      Object.values(dynStatuses).filter((s) => s.status === "working").length,
    [statuses, dynStatuses],
  );
  const missionCount = history.length + (running ? 1 : 0);

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
          <div className="flex flex-wrap items-center gap-3">
            {isBusiness && (
              <span className="hidden rounded-sm border border-[#ffd257]/50 bg-[#ffd257]/10 px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-[#ffd257] sm:inline">
                Team-Arbeitsbereich
              </span>
            )}
            {usage && (
              <span className="hidden font-mono text-[10px] uppercase tracking-[0.14em] text-[#ffb35c]/70 sm:inline" aria-live="polite">
                Missionen heute: {usage.used}/{usage.limit}
              </span>
            )}
            {branche && (
              <button
                onClick={() => setOnboardingOpen(true)}
                className={`rounded-sm border border-[#ff8c2a]/30 bg-[#ff8c2a]/[0.06] px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-[#ffb35c] transition-colors hover:bg-[#ff8c2a]/15 ${FOCUS_RING}`}
              >
                {branche}{" "}
                <span className="ml-1.5 text-[#ff8c2a] underline underline-offset-2">Ändern</span>
              </button>
            )}
            <button
              onClick={() => setLicenseOpen(true)}
              className={`rounded-sm border px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] transition-colors ${FOCUS_RING} ${
                licensedPlan === "FREE"
                  ? "border-[#ff8c2a]/40 text-[#ff8c2a] hover:bg-[#ff8c2a]/10"
                  : "border-[#ffb35c]/40 bg-[#ff8c2a]/[0.06] text-[#ffb35c] hover:bg-[#ff8c2a]/15"
              }`}
            >
              {licensedPlan === "FREE" ? "Lizenz aktivieren" : `Lizenz: ${licensedPlan}`}
            </button>
            <a
              href="/chat"
              className={`rounded-sm px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-[#ffb35c]/70 transition-colors hover:bg-[#ff8c2a]/10 hover:text-[#ffb35c] ${FOCUS_RING}`}
            >
              KI-Chat
            </a>
            <a
              href="/workflows"
              className={`rounded-sm px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-[#ffb35c]/70 transition-colors hover:bg-[#ff8c2a]/10 hover:text-[#ffb35c] ${FOCUS_RING}`}
            >
              Autopilot
            </a>
            <a
              href="/integrationen"
              className={`rounded-sm px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-[#ffb35c]/70 transition-colors hover:bg-[#ff8c2a]/10 hover:text-[#ffb35c] ${FOCUS_RING}`}
            >
              Integrationen
            </a>
            <div className="flex overflow-hidden rounded-sm border border-[#ff8c2a]/30" role="group" aria-label="Abo-Stufe">
              {PLANS.map((p) => {
                const locked = PLAN_LEVEL[p] > PLAN_LEVEL[licensedPlan];
                return (
                  <button
                    key={p}
                    onClick={() => handlePlanClick(p)}
                    aria-pressed={plan === p}
                    aria-label={locked ? `${p} (Lizenz erforderlich)` : p}
                    className={`flex items-center gap-1 px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] transition-colors ${FOCUS_RING} ${
                      plan === p
                        ? p === "BUSINESS" || p === "ENTERPRISE"
                          ? "bg-[#ffd257] text-[#1a0f04]"
                          : "bg-[#ff8c2a] text-[#1a0f04]"
                        : locked
                          ? "text-[#8a7455] hover:bg-[#ff8c2a]/10"
                          : "text-[#ffb35c]/70 hover:bg-[#ff8c2a]/10"
                    }`}
                  >
                    {locked && <LockIcon />}
                    {p}
                  </button>
                );
              })}
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
              Commander plant, Builder und Analyst arbeiten parallel, Quality prüft. Sie erhalten ein fertiges Ergebnis.
            </p>
            <div className="mt-5 flex flex-col gap-3 sm:flex-row">
              <input
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && startMission()}
                placeholder={
                  dokument
                    ? "z. B. Fasse dieses Dokument zusammen"
                    : 'z. B. "Erstelle eine Marketingstrategie für eine Zürcher Bäckerei"'
                }
                disabled={running}
                className="flex-1 rounded-sm border border-[#ff8c2a]/25 bg-[#ff8c2a]/[0.04] px-4 py-3 text-[#fff3e2] placeholder:text-[#8a7455] outline-none transition focus:border-[#ff8c2a]/70 focus:ring-2 focus:ring-[#ff8c2a]/20"
              />
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.md,.csv,.html,.pdf"
                className="hidden"
                aria-hidden
                tabIndex={-1}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  // Zurücksetzen, damit dieselbe Datei erneut wählbar ist.
                  e.target.value = "";
                  if (file) void attachDocument(file);
                }}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={running || docBusy}
                className={`rounded-sm border border-[#ff8c2a]/40 px-4 py-3 font-semibold text-[#ffb35c] transition hover:bg-[#ff8c2a]/10 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 ${FOCUS_RING}`}
              >
                {docBusy ? "Liest Dokument …" : "Dokument anhängen"}
              </button>
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
            {dokument && (
              <div className="mt-3 inline-flex max-w-full items-center gap-2 rounded-sm border border-[#ff8c2a]/30 bg-[#ff8c2a]/[0.08] px-3 py-1.5 font-mono text-xs text-[#ffb35c]">
                <span className="truncate" title={dokument.name}>{dokument.name}</span>
                <span className="shrink-0 text-[#8a7455]">{dokument.text.length} Zeichen</span>
                <button
                  onClick={removeDocument}
                  aria-label={`Dokument ${dokument.name} entfernen`}
                  className={`shrink-0 rounded-sm px-1 text-sm leading-none text-[#ffb35c]/70 transition-colors hover:bg-[#ff8c2a]/15 hover:text-[#fff3e2] ${FOCUS_RING}`}
                >
                  ×
                </button>
              </div>
            )}
            {docError && (
              <p role="alert" className="mt-3 rounded-sm border border-red-400/30 bg-red-400/10 px-4 py-2 text-sm text-red-300">
                {docError}
              </p>
            )}
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
                  workforce={workforce}
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
              {BASE_ROLES.map((role) => (
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
              {EXTRA_ROLES.map((role) =>
                showExtraAgents ? (
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
                ) : (
                  <LockedAgentCard key={role} name={AGENT_META[role].name} tagline={AGENT_META[role].tagline} />
                ),
              )}
            </div>
          </section>

          {/* Organigramm der virtuellen Firma (BUSINESS/ENTERPRISE) */}
          {isOrgPlan && org && <OrgChart org={org} dynStatuses={dynStatuses} />}

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
            <section aria-label="Qualitätsbewertung" className="mt-8 rounded-sm border border-[#ff8c2a]/20 bg-[#ff8c2a]/[0.02] p-5">
              <div className="flex items-center gap-4">
                <div className={`font-mono text-3xl font-extrabold ${score >= 80 ? "text-[#ffb35c]" : score >= 60 ? "text-amber-400" : "text-red-400"}`}>{score}/100</div>
                <div className="text-sm text-[#c9b391]">Bewertung durch Quality AI</div>
              </div>
            </section>
          )}
          {improvements.length > 0 && (
            <section aria-label="Verbesserungen" className={`mt-4 rounded-sm border border-[#ff8c2a]/15 bg-[#ff8c2a]/[0.02] p-5 ${fancy ? "hud-corners relative" : ""}`}>
              <div className={fancy ? "hud-label mb-2" : "mb-2 text-sm font-semibold text-[#fff3e2]"}>Verbesserungsvorschläge</div>
              <ul className="space-y-1 text-sm text-[#e8dcc8]">
                {improvements.map((imp, i) => (
                  <li key={i} className="ml-5 list-disc">{imp}</li>
                ))}
              </ul>
            </section>
          )}

          {/* Erzeugte Dateien (Artefakte) */}
          {artifacts.length > 0 && (
            <ArtifactViewer key={artifacts.map((f) => f.path).join("|")} files={artifacts} />
          )}

          {/* Finales Ergebnis: mit Dateien eingeklappt hinter den Artefakten */}
          {finalResult && artifacts.length > 0 && (
            <section aria-label="Ergebnis" className="mt-6">
              <details className={`rounded-sm border border-[#ff8c2a]/30 bg-gradient-to-b from-[#ff8c2a]/[0.07] to-transparent ${fancy ? "hud-corners relative" : ""}`}>
                <summary className={`cursor-pointer select-none p-5 text-lg font-bold text-[#fff3e2] transition-colors hover:text-[#ffb35c] ${FOCUS_RING}`}>
                  Vollständiger Bericht
                  <span className="ml-3 font-mono text-[10px] font-normal uppercase tracking-[0.18em] text-[#ffb35c]/70">Zum Aufklappen</span>
                </summary>
                <div className="px-6 pb-6 text-sm leading-relaxed text-[#e8dcc8]">{renderMarkdown(finalResult)}</div>
              </details>
            </section>
          )}
          {finalResult && artifacts.length === 0 && (
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
                      onClick={() => { setFinalResult(h.final); setScore(h.score); setImprovements([]); setArtifacts(h.artifacts ?? []); setError(""); }}
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

      {onboardingOpen && (
        <OnboardingModal
          initialBranche={branche}
          initialGroesse={groesse}
          onConfirm={confirmOnboarding}
          onClose={() => setOnboardingOpen(false)}
        />
      )}
      {licenseOpen && (
        <LicenseModal
          licensedPlan={licensedPlan}
          onActivated={handleLicenseActivated}
          onClose={() => setLicenseOpen(false)}
        />
      )}

      {isBusiness && (
        <BusinessTicker
          running={running}
          startedAt={startedAt}
          activeAgents={activeAgents}
          totalAgents={totalAgents}
          missions={missionCount}
          workforce={workforce}
          plan={plan}
          totalEventsRef={totalEventsRef}
        />
      )}
    </main>
  );
}
