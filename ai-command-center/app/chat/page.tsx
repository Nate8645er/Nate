"use client";

/**
 * Kommandozentrale – heller, freundlicher Arbeitsbereich im Stil moderner
 * KI-Assistenten (warmes Creme, weisse Karten, Marken-Orange als Akzent).
 *
 * Kein Chatbot: Jeder Befehl startet eine echte Mission über /api/mission,
 * zeigt live die arbeitende Belegschaft und endet mit fertigen Dateien
 * (Vorschau/Download) plus Bericht und Quality-Score.
 *
 * Dateien: PDF (Server-Extraktion via /api/extract) sowie TXT/MD/CSV/HTML
 * (Client-seitig gelesen) können angehängt werden – die Belegschaft
 * arbeitet mit dem Inhalt (context.dokument der Mission).
 *
 * Verlauf in localStorage (acc-kommandos); Lizenz-/Usage-Token und
 * Branchen-Kontext werden mit dem Dashboard geteilt.
 */

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import type { ArtifactFile } from "@/lib/agents/types";
import { SKILLS, skillSuche, skillVerfuegbar, SKILL_AB_STUFE, type SkillStufe } from "@/lib/skills";
import WorkNav from "@/app/components/WorkNav";

const KOMMANDOS_KEY = "acc-kommandos";
const LICENSE_TOKEN_KEY = "acc-license-token";
const USAGE_TOKEN_KEY = "acc-usage-token";
const BRANCHE_KEY = "acc-branche";
const GROESSE_KEY = "acc-groesse";
const MAX_ENTRIES = 20;
const MAX_DOK_ZEICHEN = 20_000;

interface Kommando {
  id: string;
  befehl: string;
  at: string;
  score: number | null;
  final: string | null;
  artifacts: ArtifactFile[];
  workforce: number | null;
  fehler: string | null;
  dokumentName?: string;
}

interface LiveState {
  entryId: string;
  aktivitaet: string[];
}

interface Dok {
  name: string;
  text: string;
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
  const [dokument, setDokument] = useState<Dok | null>(null);
  const [dokFehler, setDokFehler] = useState<string | null>(null);
  const [dokLaedt, setDokLaedt] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

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
      const params = new URLSearchParams(window.location.search);
      const b = params.get("befehl");
      const t = params.get("text");
      if (t?.trim()) {
        // Vorbefüllter Befehl aus einem anderen Bereich (z. B. Kunden-Modul).
        setActiveId(null);
        setInput(t.trim().slice(0, 2000));
        return;
      }
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

  /* Eingebauter KI-Browser: Web-Recherche vor jeder Mission (abschaltbar). */
  const [webRecherche, setWebRecherche] = useState(true);

  /* Abo-Stufe des Nutzers (acc-plan aus der Lizenz-Aktivierung, sonst FREE):
   * verfügbare Skills sind wählbar, höhere zeigen die nötige Stufe. */
  const [stufe, setStufe] = useState<SkillStufe>("FREE");
  useEffect(() => {
    try {
      const reihenfolge = ["FREE", "PERSONAL", "STARTER", "PROFESSIONAL", "BUSINESS", "ENTERPRISE"];
      const p = localStorage.getItem("acc-plan");
      if (p && reihenfolge.includes(p)) {
        // Ultra-Levelup: passender Ultra-Code schaltet die Skills der
        // nächsthöheren Stufe frei (serverseitig steigen Limits/Budget).
        const ultraPlan = localStorage.getItem("acc-ultra-plan");
        const idx = reihenfolge.indexOf(p);
        const effektiv =
          ultraPlan === p && idx < reihenfolge.length - 1
            ? reihenfolge[idx + 1]
            : p;
        setStufe(effektiv as SkillStufe);
      }
    } catch {
      /* Storage nicht lesbar */
    }
  }, []);

  const alleTreffer = skillSuche(input);
  const skillTreffer = alleTreffer.filter((s) => skillVerfuegbar(s.befehl, stufe));
  const gesperrteTreffer = alleTreffer.filter((s) => !skillVerfuegbar(s.befehl, stufe));

  /** Datei anhängen: PDF via /api/extract, Text-Formate direkt lesen. */
  const dateiWaehlen = useCallback(async (file: File) => {
    setDokFehler(null);
    setDokLaedt(true);
    try {
      const name = file.name.replace(/\s+/g, " ").trim().slice(0, 80);
      if (/\.pdf$/i.test(file.name)) {
        const form = new FormData();
        form.append("file", file);
        const res = await fetch("/api/extract", { method: "POST", body: form });
        const data = (await res.json()) as { text?: string; error?: string };
        if (!res.ok || !data.text) {
          setDokFehler(data.error ?? "PDF konnte nicht gelesen werden.");
          return;
        }
        setDokument({ name, text: data.text.slice(0, MAX_DOK_ZEICHEN) });
      } else if (/\.(txt|md|csv|html?)$/i.test(file.name)) {
        const text = (await file.text()).slice(0, MAX_DOK_ZEICHEN).trim();
        if (!text) {
          setDokFehler("Die Datei ist leer.");
          return;
        }
        setDokument({ name, text });
      } else {
        setDokFehler("Unterstützt: PDF, TXT, MD, CSV, HTML (Word/Excel: bitte als PDF oder CSV speichern).");
      }
    } catch {
      setDokFehler("Datei konnte nicht gelesen werden.");
    } finally {
      setDokLaedt(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }, []);

  /** Befehl ausführen = echte Mission starten und Events live rendern. */
  const ausfuehren = useCallback(
    async (text: string) => {
      const befehl = text.trim();
      if (!befehl || running) return;
      setInput("");
      const dok = dokument;
      setDokument(null);

      const entry: Kommando = {
        id: `k${Date.now().toString(36)}`,
        befehl,
        at: new Date().toISOString(),
        score: null,
        final: null,
        artifacts: [],
        workforce: null,
        fehler: null,
        ...(dok ? { dokumentName: dok.name } : {}),
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
          const ult = localStorage.getItem("acc-ultra-token");
          if (lic) headers["x-acc-license"] = lic;
          if (use) headers["x-acc-usage"] = use;
          if (ult) headers["x-acc-ultra"] = ult;
        } catch {
          /* Storage nicht lesbar */
        }
        const context = {
          branche: safeGet(BRANCHE_KEY),
          groesse: safeGet(GROESSE_KEY),
          ...(dok ? { dokument: dok } : {}),
        };
        const res = await fetch("/api/mission", {
          method: "POST",
          headers,
          body: JSON.stringify({ goal: befehl, context, recherche: webRecherche }),
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
    [entries, running, persist, dokument],
  );

  return (
    <div className="acc-page flex h-dvh text-[#1c1917]">
      {/* Seitenleiste: Befehls-Verlauf */}
      <aside
        className={`${sidebarOpen ? "flex" : "hidden"} fixed inset-y-0 left-0 z-40 w-72 flex-col border-r border-[#e8e1d2] bg-[#f3efe6] md:static md:flex`}
      >
        <div className="flex items-center gap-2.5 px-5 py-5">
          <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
          <span className="text-sm font-bold tracking-tight">AI Command Center</span>
        </div>
        <div className="px-3">
          <button
            onClick={() => {
              setActiveId(null);
              setSidebarOpen(false);
            }}
            className="shop-btn w-full rounded-xl bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:shadow-md"
          >
            + Neuer Befehl
          </button>
        </div>
        <p className="px-5 pb-1 pt-5 text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">
          Verlauf
        </p>
        <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 pb-3" aria-label="Befehls-Verlauf">
          {entries.map((e) => (
            <button
              key={e.id}
              onClick={() => {
                setActiveId(e.id);
                setSidebarOpen(false);
              }}
              className={`block w-full truncate rounded-lg px-3 py-2 text-left text-sm ${
                e.id === activeId
                  ? "bg-[#ffe9d4] font-medium text-[#8a4a12]"
                  : "text-[#6f6557] hover:bg-[#ebe6da]"
              }`}
              title={e.befehl}
            >
              {e.artifacts.length > 0 && <span aria-hidden="true">📄 </span>}
              {e.befehl}
            </button>
          ))}
          {entries.length === 0 && (
            <p className="px-3 py-2 text-xs text-[#a2988a]">Noch keine Befehle.</p>
          )}
        </nav>
        <div className="border-t border-[#e8e1d2] p-4 text-xs text-[#6f6557]">
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
      <div className="relative flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-[#e8e1d2] bg-[#fbfaf6]/80 px-5 py-3 backdrop-blur">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen((v) => !v)}
              className="rounded-lg border border-[#e0d8c6] px-2.5 py-1.5 text-sm text-[#8a4a12] md:hidden"
              aria-label="Befehls-Verlauf öffnen"
            >
              ☰
            </button>
            <h1 className="text-sm font-bold tracking-tight">Kommandozentrale</h1>
          </div>
          <WorkNav aktiv="kommando" variante="hell" />
        </header>

        <main className="flex-1 overflow-y-auto px-4 py-8">
          <div className="mx-auto max-w-3xl">
            {!active && !running && (
              <div className="flex min-h-[52vh] flex-col items-center justify-center text-center">
                <span className="mb-6 inline-block h-11 w-11 rounded-2xl bg-gradient-to-br from-[#ffb066] to-[#ff5f1f] shadow-[0_8px_30px_rgba(255,120,40,0.35)]" />
                <h2 className="text-balance text-3xl font-semibold tracking-tight sm:text-[40px] sm:leading-tight">
                  Womit darf Ihre Belegschaft helfen?
                </h2>
                <p className="mt-3 max-w-md text-[15px] leading-relaxed text-[#6f6557]">
                  Geben Sie einen Befehl – Ihr KI-Team führt ihn aus und liefert
                  ein fertiges Ergebnis. Tippen Sie{" "}
                  <span className="rounded bg-[#f0ebe0] px-1.5 py-0.5 font-mono text-[#c25e0e]">/</span>{" "}
                  für alle{" "}
                  <Link href="/faehigkeiten" className="font-medium text-[#c25e0e] hover:underline">
                    {SKILLS.length} Befehle
                  </Link>
                  .
                </p>
                <div className="mt-9 grid w-full gap-2.5 sm:grid-cols-2">
                  {BEISPIELE.map((b) => (
                    <button
                      key={b}
                      onClick={() => ausfuehren(b)}
                      className="shop-btn rounded-2xl border border-[#e8e1d2] bg-white px-4 py-3.5 text-left text-sm leading-snug text-[#4a4335] transition hover:border-[#ffb066] hover:shadow-[0_4px_16px_rgba(255,140,42,0.14)]"
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
                  <div className="max-w-[85%] rounded-3xl rounded-br-lg bg-[#f0ebe0] px-5 py-3.5 text-[15px] leading-relaxed text-[#33291b]">
                    {active.befehl}
                    {active.dokumentName && (
                      <span className="mt-1.5 block text-xs text-[#6f6557]">📎 {active.dokumentName}</span>
                    )}
                  </div>
                </div>

                {/* Live-Aktivität */}
                {running && live?.entryId === active.id && (
                  <div className="mb-6 acc-card rounded-2xl p-5">
                    <p className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">
                      <span className="animate-pulse inline-block h-2 w-2 rounded-full bg-[#ff8c2a]" />
                      Ihre Belegschaft arbeitet
                    </p>
                    <ul className="mt-3 space-y-1.5 text-sm text-[#6f6557]">
                      {live.aktivitaet.map((a, i) => (
                        <li key={i} className="flex items-center gap-2.5">
                          <span
                            className={`inline-block h-1.5 w-1.5 rounded-full ${
                              i === live.aktivitaet.length - 1 ? "animate-pulse bg-[#ff8c2a]" : "bg-[#e5d9c4]"
                            }`}
                          />
                          {a}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Fehler */}
                {!running && active.fehler && (
                  <p className="mb-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-3.5 text-sm text-red-700">
                    {active.fehler}
                  </p>
                )}

                {/* Ergebnis */}
                {active.final && (
                  <div className="mb-6 rounded-2xl acc-card p-6 shadow-[0_2px_12px_rgba(40,30,10,0.06)]">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">
                        Ausgeführt – Ihr Ergebnis
                      </p>
                      <div className="flex items-center gap-3 text-xs text-[#6f6557]">
                        {active.workforce && <span>{active.workforce} Mitarbeitende im Einsatz</span>}
                        {typeof active.score === "number" && (
                          <span className="rounded-full bg-gradient-to-r from-[#ffb066] to-[#ff5f1f] px-3 py-1 text-[11px] font-bold text-white">
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
                            className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-[#f4e4cb] bg-[#fff8ef] px-4 py-3"
                          >
                            <div className="min-w-0">
                              <p className="truncate font-mono text-sm font-semibold text-[#8a4a12]">📄 {f.path}</p>
                              <p className="text-xs text-[#a2988a]">
                                {f.language.toUpperCase()} · {Math.max(1, Math.round(f.content.length / 1024))} KB
                              </p>
                            </div>
                            <div className="flex gap-2">
                              {f.language === "html" && (
                                <button
                                  onClick={() => vorschau(f)}
                                  className="shop-btn rounded-lg border border-[#f0ceA0] bg-white px-3.5 py-1.5 text-xs font-bold text-[#c25e0e]"
                                >
                                  Vorschau
                                </button>
                              )}
                              <button
                                onClick={() => download(f)}
                                className="shop-btn rounded-lg bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-3.5 py-1.5 text-xs font-bold text-white"
                              >
                                Download
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    <details className="mt-4">
                      <summary className="cursor-pointer text-sm font-medium text-[#6f6557] hover:text-[#c25e0e]">
                        Bericht der Belegschaft anzeigen
                      </summary>
                      <div className="mt-3 whitespace-pre-wrap border-t border-[#f0ebe0] pt-3 text-sm leading-relaxed text-[#4a4335]">
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
        <footer className="px-4 pb-5 pt-2">
          <div className="mx-auto max-w-3xl">
            {/* Slash-Befehlspalette */}
            {(skillTreffer.length > 0 || gesperrteTreffer.length > 0) && !running && (
              <div className="mb-2 overflow-hidden acc-card rounded-2xl shadow-[0_8px_30px_rgba(40,30,10,0.10)]">
                <p className="border-b border-[#f0ebe0] px-4 py-2 text-[11px] font-bold uppercase tracking-wider text-[#a2988a]">
                  Befehle · Ihr Abo: {stufe}
                </p>
                {skillTreffer.map((s) => (
                  <button
                    key={s.befehl}
                    onClick={() => setInput(s.vorlage)}
                    className="flex w-full items-baseline gap-3 px-4 py-2.5 text-left hover:bg-[#fff4e6]"
                  >
                    <span className="shrink-0 font-mono text-sm font-bold text-[#c25e0e]">{s.befehl}</span>
                    <span className="truncate text-sm text-[#33291b]">{s.name}</span>
                    <span className="hidden truncate text-xs text-[#a2988a] sm:inline">{s.beschreibung}</span>
                  </button>
                ))}
                {gesperrteTreffer.map((s) => (
                  <div
                    key={s.befehl}
                    className="flex w-full items-baseline gap-3 px-4 py-2.5 text-left opacity-55"
                    aria-disabled="true"
                  >
                    <span className="shrink-0 font-mono text-sm font-bold text-[#a2988a]">{s.befehl}</span>
                    <span className="truncate text-sm text-[#6f6557]">{s.name}</span>
                    <span className="ml-auto shrink-0 rounded-full border border-[#e0d8c6] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[#6f6557]">
                      ab {SKILL_AB_STUFE[s.befehl]}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Angehängte Datei */}
            {(dokument || dokFehler || dokLaedt) && (
              <div className="mb-2 flex items-center gap-2">
                {dokLaedt && <span className="text-xs text-[#6f6557]">Datei wird gelesen …</span>}
                {dokument && (
                  <span className="inline-flex items-center gap-2 rounded-full border border-[#f0ceA0] bg-[#fff4e6] px-3 py-1.5 text-xs font-medium text-[#8a4a12]">
                    📎 {dokument.name}
                    <button
                      onClick={() => setDokument(null)}
                      className="text-[#c25e0e] hover:text-red-600"
                      aria-label="Datei entfernen"
                    >
                      ✕
                    </button>
                  </span>
                )}
                {dokFehler && <span className="text-xs text-red-600">{dokFehler}</span>}
              </div>
            )}

            <form
              className="flex items-end gap-2 rounded-3xl border border-[#e0d8c6] bg-white p-2.5 shadow-[0_8px_30px_rgba(40,30,10,0.08)] focus-within:border-[#ffb066]"
              onSubmit={(e) => {
                e.preventDefault();
                ausfuehren(input);
              }}
            >
              <input
                ref={fileRef}
                type="file"
                accept=".pdf,.txt,.md,.csv,.html,.htm"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) dateiWaehlen(f);
                }}
                aria-label="Datei anhängen"
              />
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                disabled={running || dokLaedt}
                className="shrink-0 rounded-xl px-3 py-3 text-lg text-[#a2988a] transition hover:bg-[#f7f2e8] hover:text-[#c25e0e] disabled:opacity-40"
                aria-label="Datei anhängen (PDF, TXT, MD, CSV, HTML)"
                title="Datei anhängen (PDF, TXT, MD, CSV, HTML)"
              >
                📎
              </button>
              <button
                type="button"
                onClick={() => setWebRecherche((v) => !v)}
                disabled={running}
                aria-pressed={webRecherche}
                className={`shrink-0 rounded-xl px-3 py-3 text-lg transition disabled:opacity-40 ${
                  webRecherche
                    ? "bg-[#e7f6ee] text-[#177245] hover:bg-[#d8f0e4]"
                    : "text-[#a2988a] hover:bg-[#f7f2e8] hover:text-[#c25e0e]"
                }`}
                aria-label={webRecherche ? "KI-Browser an – Belegschaft recherchiert im Web" : "KI-Browser aus"}
                title={webRecherche ? "KI-Browser AN: Ihre Belegschaft recherchiert vor der Arbeit im Web (mit Quellen). Klicken zum Ausschalten." : "KI-Browser AUS. Klicken zum Einschalten."}
              >
                🌐
              </button>
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
                placeholder="Befehl an Ihre Belegschaft … («Erstelle …», «Kontrolliere …», «Analysiere …»)"
                className="min-h-[44px] flex-1 resize-none bg-transparent px-2 py-2.5 text-[15px] text-[#1c1917] placeholder:text-[#b3a894] focus:outline-none"
                aria-label="Befehl eingeben"
                disabled={running}
              />
              <button
                type="submit"
                disabled={running || !input.trim()}
                className="shop-btn shrink-0 rounded-2xl bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-5 py-3 text-sm font-bold text-white shadow-sm disabled:opacity-40"
              >
                {running ? "Läuft …" : "Ausführen"}
              </button>
            </form>
            <p className="mt-2 text-center text-[11px] text-[#b3a894]">
              📎 Dateien anhängen (PDF, Text, CSV) · 🌐 KI-Browser{" "}
              {webRecherche ? "an: Ihre Belegschaft recherchiert im Web, mit Quellenangaben" : "aus"} ·
              Jeder Befehl endet mit einem fertigen Ergebnis.
            </p>
          </div>
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
