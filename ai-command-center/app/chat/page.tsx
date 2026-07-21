"use client";

/**
 * Kommandozentrale – der Chef gibt Befehle, die Belegschaft FÜHRT AUS.
 *
 * Bewusst KEIN Chatbot: Jeder Befehl startet eine echte Mission über
 * /api/mission. Im Verlauf sieht man live, welche Agenten arbeiten, und
 * am Ende stehen fertige Dateien (Download + Vorschau) plus Bericht –
 * nicht eine Chat-Antwort.
 *
 * Verlauf in localStorage (acc-kommandos); Lizenz-/Usage-Token und
 * Branchen-Kontext werden mit dem Dashboard geteilt.
 */

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import type { ArtifactFile } from "@/lib/agents/types";
import { SKILLS, skillSuche } from "@/lib/skills";

const KOMMANDOS_KEY = "acc-kommandos";
const LICENSE_TOKEN_KEY = "acc-license-token";
const USAGE_TOKEN_KEY = "acc-usage-token";
const BRANCHE_KEY = "acc-branche";
const GROESSE_KEY = "acc-groesse";
const MAX_ENTRIES = 20;

interface Kommando {
  id: string;
  befehl: string;
  at: string;
  score: number | null;
  final: string | null;
  artifacts: ArtifactFile[];
  workforce: number | null;
  fehler: string | null;
}

interface LiveState {
  entryId: string;
  aktivitaet: string[];
}

const BEISPIELE = [
  "Erstelle eine Landingpage für unsere neue Dienstleistung",
  "Kontrolliere dieses Angebot auf Schwachstellen: 3 Websites für 12'000 CHF, Lieferzeit 2 Wochen",
  "Erstelle einen kompletten Marketingplan für das nächste Quartal",
  "Analysiere unsere Preisstruktur und mach konkrete Verbesserungsvorschläge",
];

const MIME_BY_LANGUAGE: Record<string, string> = {
  html: "text/html",
  css: "text/css",
  javascript: "text/javascript",
  typescript: "text/plain",
  markdown: "text/markdown",
  json: "application/json",
};

export default function KommandoPage() {
  const [entries, setEntries] = useState<Kommando[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [live, setLive] = useState<LiveState | null>(null);
  const [usageInfo, setUsageInfo] = useState<{ used: number; limit: number; plan: string } | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const active = entries.find((e) => e.id === activeId) ?? null;
  const running = live !== null;

  useEffect(() => {
    try {
      const raw = localStorage.getItem(KOMMANDOS_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Kommando[];
        if (Array.isArray(parsed)) {
          setEntries(parsed);
          if (parsed.length > 0) setActiveId(parsed[0].id);
        }
      }
    } catch {
      /* defekter Storage => leer */
    }
  }, []);

  const persist = useCallback((next: Kommando[]) => {
    setEntries(next);
    try {
      localStorage.setItem(KOMMANDOS_KEY, JSON.stringify(next.slice(0, MAX_ENTRIES)));
    } catch {
      // Storage voll (grosse Artefakte): ohne Artefakte erneut versuchen.
      try {
        localStorage.setItem(
          KOMMANDOS_KEY,
          JSON.stringify(next.slice(0, 10).map((e) => ({ ...e, artifacts: [] }))),
        );
      } catch {
        /* endgültig voll */
      }
    }
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [live?.aktivitaet.length, active?.final]);

  /* ?befehl=/offerte aus der Skills-Seite -> Vorlage vorbefüllen. */
  useEffect(() => {
    try {
      const b = new URLSearchParams(window.location.search).get("befehl");
      if (!b) return;
      const skill = SKILLS.find((s) => s.befehl === b);
      if (skill) {
        setActiveId(null);
        setInput(skill.vorlage);
      }
    } catch {
      /* Query nicht lesbar */
    }
  }, []);

  const skillTreffer = skillSuche(input);

  /** Befehl ausführen = echte Mission starten und Events live rendern. */
  const ausfuehren = useCallback(
    async (text: string) => {
      const befehl = text.trim();
      if (!befehl || running) return;
      setInput("");

      const entry: Kommando = {
        id: `k${Date.now().toString(36)}`,
        befehl,
        at: new Date().toISOString(),
        score: null,
        final: null,
        artifacts: [],
        workforce: null,
        fehler: null,
      };
      const rest = entries;
      persist([entry, ...rest]);
      setActiveId(entry.id);
      setSidebarOpen(false);
      setLive({ entryId: entry.id, aktivitaet: ["Belegschaft wird zusammengestellt …"] });

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
        const context = { branche: safeGet(BRANCHE_KEY), groesse: safeGet(GROESSE_KEY) };
        const res = await fetch("/api/mission", {
          method: "POST",
          headers,
          body: JSON.stringify({ goal: befehl, context }),
        });
        if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        const ergebnis: Partial<Kommando> = {};

        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? "";
          for (const part of parts) {
            const line = part.split("\n").find((l) => l.startsWith("data: "));
            if (!line) continue;
            let ev: {
              type: string;
              status?: string;
              message?: string;
              label?: string;
              agent?: string;
              department?: string;
              workforce?: number;
              score?: number;
              content?: string;
              files?: ArtifactFile[];
              token?: string;
              used?: number;
              limit?: number;
              plan?: string;
            };
            try {
              ev = JSON.parse(line.slice(6));
            } catch {
              continue;
            }
            if (ev.type === "usage" && ev.token) {
              try {
                localStorage.setItem(USAGE_TOKEN_KEY, ev.token);
              } catch {
                /* voll */
              }
              if (typeof ev.used === "number" && typeof ev.limit === "number" && ev.plan) {
                setUsageInfo({ used: ev.used, limit: ev.limit, plan: ev.plan });
              }
            } else if (ev.type === "status" && ev.status === "working") {
              const wer = ev.label ?? rollenName(ev.agent) ?? "Team";
              const abteilung = ev.department ? ` (${ev.department})` : "";
              setLive((l) =>
                l ? { ...l, aktivitaet: [...l.aktivitaet.slice(-7), `${wer}${abteilung}: ${ev.message ?? "arbeitet"}`] } : l,
              );
            } else if (ev.type === "org" && typeof ev.workforce === "number") {
              ergebnis.workforce = ev.workforce;
              setLive((l) =>
                l
                  ? { ...l, aktivitaet: [...l.aktivitaet.slice(-7), `Virtuelle Firma gegründet: ${ev.workforce} Mitarbeitende`] }
                  : l,
              );
            } else if (ev.type === "score" && typeof ev.score === "number") {
              ergebnis.score = ev.score;
            } else if (ev.type === "artifact" && Array.isArray(ev.files)) {
              ergebnis.artifacts = ev.files;
            } else if (ev.type === "final" && typeof ev.content === "string") {
              ergebnis.final = ev.content;
            } else if (ev.type === "error" && typeof ev.message === "string") {
              ergebnis.fehler = ev.message;
            }
          }
        }

        persist([
          {
            ...entry,
            score: ergebnis.score ?? null,
            final: ergebnis.final ?? null,
            artifacts: ergebnis.artifacts ?? [],
            workforce: ergebnis.workforce ?? null,
            fehler: ergebnis.final ? null : (ergebnis.fehler ?? null),
          },
          ...rest,
        ]);
      } catch {
        persist([{ ...entry, fehler: "Netzwerkfehler – bitte erneut versuchen." }, ...rest]);
      } finally {
        setLive(null);
      }
    },
    [entries, running, persist],
  );

  return (
    <div className="flex h-dvh bg-[#0b0a08] text-zinc-200">
      <div className="hud-texture" aria-hidden="true" />

      {/* Seitenleiste: Befehls-Verlauf */}
      <aside
        className={`${sidebarOpen ? "flex" : "hidden"} fixed inset-y-0 left-0 z-40 w-72 flex-col border-r border-[#ff8c2a]/15 bg-[#0e0c0a] md:static md:flex`}
      >
        <div className="flex items-center gap-2 border-b border-[#ff8c2a]/15 px-4 py-4">
          <span className="hud-pulse inline-block h-2 w-2 rounded-full bg-[#ff8c2a]" />
          <span className="hud-label">AI Command Center</span>
        </div>
        <div className="p-3">
          <button
            onClick={() => {
              setActiveId(null);
              setSidebarOpen(false);
            }}
            className="shop-btn w-full rounded-lg border border-[#ff8c2a]/40 bg-[#ff8c2a]/10 px-4 py-2.5 text-sm font-semibold text-[#ffb35c] transition hover:bg-[#ff8c2a]/20"
          >
            + Neuer Befehl
          </button>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 pb-3" aria-label="Befehls-Verlauf">
          {entries.map((e) => (
            <button
              key={e.id}
              onClick={() => {
                setActiveId(e.id);
                setSidebarOpen(false);
              }}
              className={`block w-full truncate rounded-lg px-3 py-2 text-left text-sm ${
                e.id === activeId
                  ? "bg-[#ff8c2a]/15 text-[#ffb35c]"
                  : "text-zinc-400 hover:bg-[#ff8c2a]/5 hover:text-zinc-200"
              }`}
              title={e.befehl}
            >
              {e.artifacts.length > 0 && <span aria-hidden="true">📄 </span>}
              {e.befehl}
            </button>
          ))}
          {entries.length === 0 && <p className="px-3 py-2 text-xs text-zinc-600">Noch keine Befehle.</p>}
        </nav>
        <div className="border-t border-[#ff8c2a]/15 p-3 text-xs text-zinc-500">
          {usageInfo ? (
            <p>
              {usageInfo.plan} · {usageInfo.used} von {usageInfo.limit} Missionen heute
            </p>
          ) : (
            <p>Jeder Befehl ist eine echte Mission.</p>
          )}
        </div>
      </aside>

      {/* Hauptbereich */}
      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-[#ff8c2a]/15 bg-[#0b0a08]/80 px-4 py-3 backdrop-blur">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen((v) => !v)}
              className="rounded-md border border-[#ff8c2a]/25 px-2.5 py-1.5 text-sm text-[#ffb35c] md:hidden"
              aria-label="Befehls-Verlauf öffnen"
            >
              ☰
            </button>
            <h1 className="text-sm font-semibold text-white">Kommandozentrale</h1>
          </div>
          <nav className="flex items-center gap-4 text-sm text-zinc-400" aria-label="Bereiche">
            <Link href="/dashboard" className="hover:text-[#ffb35c]">Missionen</Link>
            <span className="text-[#ffb35c]">Kommando</span>
            <Link href="/email" className="hover:text-[#ffb35c]">E-Mail</Link>
            <Link href="/workflows" className="hover:text-[#ffb35c]">Autopilot</Link>
            <Link href="/berichte" className="hidden hover:text-[#ffb35c] sm:inline">Berichte</Link>
            <Link href="/team" className="hidden hover:text-[#ffb35c] sm:inline">Team</Link>
          </nav>
        </header>

        <main className="flex-1 overflow-y-auto px-4 py-6">
          <div className="mx-auto max-w-3xl">
            {!active && !running && (
              <div className="flex min-h-[50vh] flex-col items-center justify-center text-center">
                <p className="hud-label mb-4">Sie befehlen. Ihre Belegschaft liefert.</p>
                <h2 className="text-balance text-3xl font-semibold text-white sm:text-4xl">
                  Was soll Ihre Belegschaft erledigen?
                </h2>
                <p className="mt-3 max-w-md text-sm text-zinc-500">
                  Kein Chatbot: Jeder Befehl startet Ihr KI-Team und endet mit einem
                  fertigen Ergebnis – Dateien, Berichte, Analysen. Tippen Sie{" "}
                  <span className="font-mono text-[#ffb35c]">/</span> für alle{" "}
                  <Link href="/faehigkeiten" className="text-[#ffb35c] hover:underline">
                    {SKILLS.length} Befehle
                  </Link>
                  .
                </p>
                <div className="mt-8 grid w-full gap-2 sm:grid-cols-2">
                  {BEISPIELE.map((b) => (
                    <button
                      key={b}
                      onClick={() => ausfuehren(b)}
                      className="shop-btn rounded-xl border border-[#ff8c2a]/20 bg-[#ff8c2a]/[0.04] px-4 py-3 text-left text-sm text-zinc-300 transition hover:border-[#ff8c2a]/50 hover:bg-[#ff8c2a]/10"
                    >
                      {b}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {active && (
              <>
                {/* Befehl */}
                <div className="mb-6 flex justify-end">
                  <div className="max-w-[85%] rounded-2xl rounded-br-md border border-[#ff8c2a]/25 bg-[#ff8c2a]/10 px-4 py-3 text-sm leading-relaxed text-zinc-100">
                    {active.befehl}
                  </div>
                </div>

                {/* Live-Aktivität */}
                {running && live?.entryId === active.id && (
                  <div className="hud-panel mb-6 rounded-xl p-4">
                    <p className="hud-label mb-3">Belegschaft arbeitet</p>
                    <ul className="space-y-1.5 text-sm text-zinc-400">
                      {live.aktivitaet.map((a, i) => (
                        <li key={i} className="flex items-center gap-2">
                          <span
                            className={`inline-block h-1.5 w-1.5 rounded-full ${i === live.aktivitaet.length - 1 ? "hud-pulse bg-[#ff8c2a]" : "bg-[#ff8c2a]/30"}`}
                          />
                          {a}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Ergebnis */}
                {!running && active.fehler && (
                  <p className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                    {active.fehler}
                  </p>
                )}
                {active.final && (
                  <div className="hud-panel hud-corners relative mb-6 rounded-xl p-5">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="hud-label">Ausgeführt – Ihr Ergebnis</p>
                      <div className="flex items-center gap-3 text-xs text-zinc-400">
                        {active.workforce && <span>{active.workforce} Mitarbeitende im Einsatz</span>}
                        {typeof active.score === "number" && (
                          <span className="rounded-full border border-[#ffd257]/50 bg-[#ffd257]/10 px-2.5 py-0.5 font-semibold text-[#ffd257]">
                            Quality-Score {active.score}
                          </span>
                        )}
                      </div>
                    </div>

                    {active.artifacts.length > 0 && (
                      <div className="mt-4 space-y-2">
                        {active.artifacts.map((f) => (
                          <div
                            key={f.path}
                            className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[#ff8c2a]/25 bg-[#ff8c2a]/[0.05] px-4 py-3"
                          >
                            <div className="min-w-0">
                              <p className="truncate font-mono text-sm text-[#ffb35c]">📄 {f.path}</p>
                              <p className="text-xs text-zinc-500">
                                {f.language.toUpperCase()} · {Math.max(1, Math.round(f.content.length / 1024))} KB
                              </p>
                            </div>
                            <div className="flex gap-2">
                              {f.language === "html" && (
                                <button
                                  onClick={() => vorschau(f)}
                                  className="shop-btn rounded-md border border-[#ff8c2a]/40 px-3 py-1.5 text-xs font-semibold text-[#ffb35c]"
                                >
                                  Vorschau
                                </button>
                              )}
                              <button
                                onClick={() => download(f)}
                                className="shop-btn rounded-md bg-gradient-to-r from-[#ffb066] to-[#ff5f1f] px-3 py-1.5 text-xs font-bold text-[#1a0f04]"
                              >
                                Download
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    <details className="mt-4">
                      <summary className="cursor-pointer text-sm text-zinc-400 hover:text-[#ffb35c]">
                        Bericht der Belegschaft anzeigen
                      </summary>
                      <div className="mt-3 whitespace-pre-wrap border-t border-[#ff8c2a]/15 pt-3 text-sm leading-relaxed text-zinc-300">
                        {active.final}
                      </div>
                    </details>
                  </div>
                )}
              </>
            )}
            <div ref={bottomRef} />
          </div>
        </main>

        {/* Befehlseingabe */}
        <footer className="border-t border-[#ff8c2a]/15 bg-[#0b0a08]/90 px-4 py-4 backdrop-blur">
          {/* Slash-Befehlspalette */}
          {skillTreffer.length > 0 && !running && (
            <div className="mx-auto mb-2 max-w-3xl overflow-hidden rounded-xl border border-[#ff8c2a]/30 bg-[#12100d]">
              <p className="hud-label border-b border-[#ff8c2a]/15 px-4 py-2">Befehle</p>
              {skillTreffer.map((s) => (
                <button
                  key={s.befehl}
                  onClick={() => setInput(s.vorlage)}
                  className="flex w-full items-baseline gap-3 px-4 py-2.5 text-left hover:bg-[#ff8c2a]/10"
                >
                  <span className="shrink-0 font-mono text-sm font-bold text-[#ffb35c]">{s.befehl}</span>
                  <span className="truncate text-sm text-zinc-300">{s.name}</span>
                  <span className="hidden truncate text-xs text-zinc-500 sm:inline">{s.beschreibung}</span>
                </button>
              ))}
            </div>
          )}
          <form
            className="mx-auto flex max-w-3xl items-end gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              ausfuehren(input);
            }}
          >
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  ausfuehren(input);
                }
              }}
              rows={Math.min(6, Math.max(1, input.split("\n").length))}
              placeholder='Befehl an Ihre Belegschaft … («Erstelle …», «Kontrolliere …», «Analysiere …»)'
              className="min-h-[48px] flex-1 resize-none rounded-xl border border-[#ff8c2a]/25 bg-[#12100d] px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-[#ff8c2a]/60 focus:outline-none"
              aria-label="Befehl eingeben"
              disabled={running}
            />
            <button
              type="submit"
              disabled={running || !input.trim()}
              className="shop-btn rounded-xl bg-gradient-to-r from-[#ffb066] via-[#ff8c2a] to-[#ff5f1f] px-5 py-3 text-sm font-bold text-[#1a0f04] disabled:opacity-40"
            >
              {running ? "Läuft …" : "Ausführen"}
            </button>
          </form>
          <p className="mx-auto mt-2 max-w-3xl text-center text-[11px] text-zinc-600">
            Tippen Sie <span className="font-mono text-[#ffb35c]">/</span> für Befehle ·{" "}
            <Link href="/faehigkeiten" className="text-[#ffb35c]/80 hover:underline">
              alle {SKILLS.length} Fähigkeiten ansehen
            </Link>{" "}
            · Jeder Befehl endet mit einem fertigen Ergebnis.
          </p>
        </footer>
      </div>
    </div>
  );
}

function rollenName(agent: string | undefined): string | null {
  if (!agent) return null;
  const NAMEN: Record<string, string> = {
    commander: "Commander",
    builder: "Builder",
    analyst: "Analyst",
    quality: "Quality",
    marketing: "Marketing",
    coding: "Coding",
    research: "Research",
    business: "Business",
  };
  return NAMEN[agent] ?? agent.replace(/^dyn:/, "");
}

function download(f: ArtifactFile) {
  const blob = new Blob([f.content], {
    type: `${MIME_BY_LANGUAGE[f.language] ?? "text/plain"};charset=utf-8`,
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = f.path.split("/").pop() ?? "datei.txt";
  a.click();
  URL.revokeObjectURL(url);
}

function vorschau(f: ArtifactFile) {
  const blob = new Blob([f.content], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener");
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

function safeGet(key: string): string | undefined {
  try {
    return localStorage.getItem(key) ?? undefined;
  } catch {
    return undefined;
  }
}
