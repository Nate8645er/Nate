"use client";

/**
 * KI-Chat – der vollwertige AI-Assistent des AI Command Center.
 *
 * Funktioniert wie ChatGPT/Claude: freie Unterhaltung, Antworten erscheinen
 * gestreamt Token für Token. Mit einem Klick auf den Globus schaltet sich der
 * eingebaute KI-Browser dazu: der Assistent recherchiert dann live im Web und
 * belegt seine Antwort mit echten Quellen.
 *
 * Serverkontakt: POST /api/chat (SSE-Stream). Lizenz-/Usage-/Ultra-Token
 * werden – wie überall in der Plattform – aus localStorage mitgesendet; jede
 * Antwort zählt auf das Tageslimit. Verlauf bleibt lokal (acc-assistent).
 */

import { useEffect, useRef, useState } from "react";
import WorkNav from "@/app/components/WorkNav";
import WorkFooter from "@/app/components/WorkFooter";

const LICENSE_TOKEN_KEY = "acc-license-token";
const USAGE_TOKEN_KEY = "acc-usage-token";
const ULTRA_TOKEN_KEY = "acc-ultra-token";
const BRANCHE_KEY = "acc-branche";
const GROESSE_KEY = "acc-groesse";
const HISTORY_KEY = "acc-assistent";

interface Quelle {
  titel: string;
  url: string;
}
interface Nachricht {
  role: "user" | "assistant";
  content: string;
  sources?: Quelle[];
}

const VORSCHLAEGE = [
  "Erkläre mir in 5 Punkten, wie ich mit dem AI Command Center meine Firma verbinde.",
  "Schreibe eine freundliche Absage an einen Kunden, der 20 % Rabatt möchte.",
  "Was sind aktuell die wichtigsten KI-Trends für kleine Unternehmen?",
  "Gib mir eine Checkliste für einen sicheren Online-Shop.",
];

export default function AssistentPage() {
  const [messages, setMessages] = useState<Nachricht[]>([]);
  const [input, setInput] = useState("");
  const [browse, setBrowse] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [liveQuellen, setLiveQuellen] = useState<Quelle[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [usage, setUsage] = useState<{ used: number; limit: number; plan: string } | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Verlauf laden.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      if (raw) {
        const parsed: unknown = JSON.parse(raw);
        if (Array.isArray(parsed)) setMessages(parsed.slice(-40) as Nachricht[]);
      }
    } catch {
      /* nichts */
    }
  }, []);

  // Verlauf speichern + ans Ende scrollen.
  useEffect(() => {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(messages.slice(-40)));
    } catch {
      /* voll */
    }
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, status, liveQuellen]);

  async function senden(text: string) {
    const frage = text.trim();
    if (!frage || streaming) return;
    setError(null);
    setInput("");
    setLiveQuellen([]);

    const verlauf: Nachricht[] = [...messages, { role: "user", content: frage }];
    // Platzhalter für die Assistenten-Antwort (wird gestreamt gefüllt).
    setMessages([...verlauf, { role: "assistant", content: "" }]);
    setStreaming(true);
    if (browse) setStatus("KI-Browser startet …");

    let kontext: { branche?: string; groesse?: string } = {};
    let lizenz = "";
    let usageTok = "";
    let ultraTok = "";
    try {
      kontext = {
        branche: localStorage.getItem(BRANCHE_KEY) ?? undefined,
        groesse: localStorage.getItem(GROESSE_KEY) ?? undefined,
      };
      lizenz = localStorage.getItem(LICENSE_TOKEN_KEY) ?? "";
      usageTok = localStorage.getItem(USAGE_TOKEN_KEY) ?? "";
      ultraTok = localStorage.getItem(ULTRA_TOKEN_KEY) ?? "";
    } catch {
      /* Storage nicht lesbar */
    }

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          ...(lizenz ? { "x-acc-license": lizenz } : {}),
          ...(usageTok ? { "x-acc-usage": usageTok } : {}),
          ...(ultraTok ? { "x-acc-ultra": ultraTok } : {}),
        },
        body: JSON.stringify({
          messages: verlauf.map((m) => ({ role: m.role, content: m.content })),
          context: kontext,
          browse,
        }),
      });
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

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
          const line = part.split("\n").find((l) => l.startsWith("data:"));
          if (!line) continue;
          let ev: {
            type: string;
            text?: string;
            message?: string;
            titel?: string;
            url?: string;
            quellen?: Quelle[];
            token?: string;
            used?: number;
            limit?: number;
            plan?: string;
          };
          try {
            ev = JSON.parse(line.slice(line.indexOf(":") + 1).trim());
          } catch {
            continue;
          }
          if (ev.type === "browsing") {
            setStatus(ev.message ?? "KI-Browser recherchiert …");
          } else if (ev.type === "reading" && ev.titel) {
            setLiveQuellen((q) => [...q.slice(-5), { titel: ev.titel!, url: ev.url ?? "#" }]);
          } else if (ev.type === "sources" && Array.isArray(ev.quellen)) {
            setStatus(null);
            setLiveQuellen([]);
            const quellen = ev.quellen;
            // Immutable: neues Objekt statt Mutation (sonst doppelt bei
            // StrictMode-Doppelaufruf des Updaters).
            setMessages((ms) => {
              const last = ms[ms.length - 1];
              if (last?.role !== "assistant") return ms;
              return [...ms.slice(0, -1), { ...last, sources: quellen }];
            });
          } else if (ev.type === "delta" && typeof ev.text === "string") {
            const t = ev.text;
            setStatus(null);
            setMessages((ms) => {
              const last = ms[ms.length - 1];
              if (last?.role !== "assistant") return ms;
              return [...ms.slice(0, -1), { ...last, content: last.content + t }];
            });
          } else if (ev.type === "usage") {
            if (ev.token) {
              try {
                localStorage.setItem(USAGE_TOKEN_KEY, ev.token);
              } catch {
                /* voll */
              }
            }
            if (typeof ev.used === "number" && typeof ev.limit === "number" && ev.plan) {
              setUsage({ used: ev.used, limit: ev.limit, plan: ev.plan });
            }
          } else if (ev.type === "error") {
            setError(ev.message ?? "Es ist ein Fehler aufgetreten.");
          }
        }
      }
    } catch {
      setError("Verbindung unterbrochen. Bitte erneut senden.");
    } finally {
      setStreaming(false);
      setStatus(null);
      setLiveQuellen([]);
    }
  }

  function neu() {
    if (streaming) return;
    setMessages([]);
    setError(null);
    try {
      localStorage.removeItem(HISTORY_KEY);
    } catch {
      /* nichts */
    }
  }

  const leer = messages.length === 0;

  return (
    <div className="flex min-h-screen flex-col bg-[#08070c] text-zinc-100">
      <header className="sticky top-0 z-40 flex items-center justify-between gap-3 px-4 py-3 backdrop-blur-xl sm:px-6">
        <div className="flex items-center gap-2 text-[13px] font-medium tracking-tight">
          <span className="inline-block h-2 w-2 rounded-full bg-[#ff8c2a] shadow-[0_0_10px_2px_rgba(255,140,42,0.7)]" />
          <span className="font-mono text-[11px] tracking-[0.22em] text-zinc-400">AI COMMAND CENTER</span>
        </div>
        <WorkNav aktiv="assistent" variante="dunkel" />
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 pb-40 sm:px-6">
        <div className="pt-4 pb-2">
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">KI-Chat</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Ihr persönlicher KI-Assistent – wie ChatGPT oder Claude, mit eingebautem Browser für
            aktuelle Fakten und Quellen.
          </p>
        </div>

        <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto py-4">
          {leer && (
            <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-6">
              <p className="text-sm text-zinc-300">
                Stellen Sie eine Frage oder starten Sie mit einem Vorschlag:
              </p>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {VORSCHLAEGE.map((v) => (
                  <button
                    key={v}
                    onClick={() => senden(v)}
                    className="rounded-xl border border-white/8 bg-white/[0.02] px-3 py-2.5 text-left text-[13px] text-zinc-300 transition-colors hover:border-[#ff8c2a]/40 hover:bg-[#ff8c2a]/[0.06] hover:text-white"
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
              <div
                className={
                  m.role === "user"
                    ? "max-w-[85%] rounded-2xl rounded-br-md bg-gradient-to-br from-[#ff8c2a] to-[#ff5f1f] px-4 py-2.5 text-[14px] text-white shadow-[0_6px_20px_-8px_rgba(255,110,30,0.6)]"
                    : "max-w-[92%] rounded-2xl rounded-bl-md border border-white/8 bg-white/[0.03] px-4 py-3 text-[14px] leading-relaxed text-zinc-100"
                }
              >
                {m.role === "assistant" ? (
                  <>
                    {m.content ? (
                      <div
                        className="acc-md"
                        dangerouslySetInnerHTML={{ __html: renderMarkdown(m.content) }}
                      />
                    ) : (
                      !status && <span className="inline-flex gap-1 py-1 align-middle"><Dot /><Dot /><Dot /></span>
                    )}
                    {m.sources && m.sources.length > 0 && (
                      <div className="mt-3 border-t border-white/8 pt-2.5">
                        <p className="mb-1.5 font-mono text-[10px] uppercase tracking-[0.18em] text-zinc-500">
                          Quellen ({m.sources.length})
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {m.sources.map((q, j) => (
                            <a
                              key={j}
                              href={q.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="max-w-[220px] truncate rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[11px] text-zinc-300 transition-colors hover:border-[#ff8c2a]/40 hover:text-[#ffb35c]"
                              title={q.titel}
                            >
                              {j + 1}. {q.titel}
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <span className="whitespace-pre-wrap">{m.content}</span>
                )}
              </div>
            </div>
          ))}

          {/* Live-Browser-Status während der Recherche */}
          {status && (
            <div className="flex justify-start">
              <div className="max-w-[92%] rounded-2xl rounded-bl-md border border-[#ff8c2a]/25 bg-[#ff8c2a]/[0.06] px-4 py-3 text-[13px]">
                <div className="flex items-center gap-2 font-medium text-[#ffb35c]">
                  <GlobeSpin />
                  {status}
                </div>
                {liveQuellen.length > 0 && (
                  <ul className="mt-2 space-y-1 text-[12px] text-zinc-400">
                    {liveQuellen.map((q, j) => (
                      <li key={j} className="truncate">↳ liest: {q.titel}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}

          {error && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-[13px] text-red-300">
              {error}
            </div>
          )}
        </div>
      </main>

      {/* Eingabeleiste (fixiert) */}
      <div className="fixed inset-x-0 bottom-0 z-40 border-t border-white/8 bg-[#08070c]/85 backdrop-blur-xl">
        <div className="mx-auto w-full max-w-3xl px-4 py-3 sm:px-6">
          <div className="flex items-end gap-2 rounded-2xl border border-white/10 bg-white/[0.04] p-2 focus-within:border-[#ff8c2a]/40">
            <button
              type="button"
              onClick={() => setBrowse((b) => !b)}
              aria-pressed={browse}
              title={
                browse
                  ? "KI-Browser AN: Der Assistent recherchiert im Web und belegt Antworten mit Quellen. Klicken zum Ausschalten."
                  : "KI-Browser AUS. Klicken zum Einschalten für aktuelle Fakten mit Quellen."
              }
              className={`flex shrink-0 items-center gap-1.5 rounded-xl px-2.5 py-2 text-[12px] font-medium transition-colors ${
                browse
                  ? "bg-[#ff8c2a]/15 text-[#ffb35c] ring-1 ring-[#ff8c2a]/40"
                  : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
              }`}
            >
              <GlobeIcon />
              <span className="hidden sm:inline">{browse ? "Browser an" : "Browser"}</span>
            </button>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  senden(input);
                }
              }}
              rows={1}
              placeholder="Fragen Sie den KI-Assistenten … (Enter sendet, Shift+Enter = neue Zeile)"
              className="max-h-40 flex-1 resize-none bg-transparent px-2 py-2 text-[14px] text-zinc-100 outline-none placeholder:text-zinc-500"
              disabled={streaming}
            />
            <button
              type="button"
              onClick={() => senden(input)}
              disabled={streaming || !input.trim()}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#ff8c2a] to-[#ff5f1f] text-white shadow-[0_4px_14px_-4px_rgba(255,110,30,0.6)] transition-opacity disabled:opacity-40"
              aria-label="Senden"
            >
              {streaming ? <Spinner /> : <SendIcon />}
            </button>
          </div>
          <div className="mt-1.5 flex items-center justify-between px-1 text-[11px] text-zinc-500">
            <span>
              {browse ? "🌐 Browser aktiv – Antworten mit Web-Quellen" : "Tipp: Globus einschalten für aktuelle Fakten"}
            </span>
            <div className="flex items-center gap-3">
              {usage && (
                <span>
                  {usage.plan} · {usage.used}/{usage.limit} heute
                </span>
              )}
              {messages.length > 0 && (
                <button onClick={neu} disabled={streaming} className="hover:text-zinc-300 disabled:opacity-40">
                  Neuer Chat
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="hidden">
        <WorkFooter variante="dunkel" />
      </div>

      <style>{acsStyles}</style>
    </div>
  );
}

/* ---------- Mini-Markdown (sicher: erst escapen, dann eigene Tags) ---------- */
function renderMarkdown(src: string): string {
  // Auch Anführungszeichen escapen, damit Text NICHT aus einem
  // href="…"-Attribut ausbrechen kann (Attribut-Injection / XSS).
  const esc = (s: string) =>
    s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  // Code-Blöcke zuerst herausziehen (Platzhalter), damit ihr Inhalt roh bleibt.
  const bloecke: string[] = [];
  let text = src.replace(/```(\w+)?\n?([\s\S]*?)```/g, (_m, _lang, code) => {
    bloecke.push(`<pre class="acc-code"><code>${esc(code.replace(/\n$/, ""))}</code></pre>`);
    return ` B${bloecke.length - 1} `;
  });

  text = esc(text);

  const zeilen = text.split("\n");
  const out: string[] = [];
  let listeOffen: "ul" | "ol" | null = null;
  const listeSchliessen = () => {
    if (listeOffen) {
      out.push(`</${listeOffen}>`);
      listeOffen = null;
    }
  };

  const inline = (s: string) =>
    s
      .replace(/`([^`]+)`/g, '<code class="acc-inline">$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>")
      .replace(
        /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>',
      )
      .replace(
        /(^|[\s(])((https?:\/\/[^\s<)]+))/g,
        '$1<a href="$2" target="_blank" rel="noopener noreferrer">$2</a>',
      );

  for (const zeile of zeilen) {
    const z = zeile.trimEnd();
    if (z.startsWith(" B")) {
      listeSchliessen();
      const idx = Number(z.replace(/ B(\d+) /, "$1"));
      out.push(bloecke[idx] ?? "");
      continue;
    }
    const h = /^(#{1,4})\s+(.*)$/.exec(z);
    if (h) {
      listeSchliessen();
      const stufe = Math.min(h[1].length + 1, 5);
      out.push(`<h${stufe} class="acc-h">${inline(h[2])}</h${stufe}>`);
      continue;
    }
    const uli = /^[-*]\s+(.*)$/.exec(z);
    if (uli) {
      if (listeOffen !== "ul") {
        listeSchliessen();
        out.push('<ul class="acc-ul">');
        listeOffen = "ul";
      }
      out.push(`<li>${inline(uli[1])}</li>`);
      continue;
    }
    const oli = /^\d+[.)]\s+(.*)$/.exec(z);
    if (oli) {
      if (listeOffen !== "ol") {
        listeSchliessen();
        out.push('<ol class="acc-ol">');
        listeOffen = "ol";
      }
      out.push(`<li>${inline(oli[1])}</li>`);
      continue;
    }
    if (!z.trim()) {
      listeSchliessen();
      continue;
    }
    listeSchliessen();
    out.push(`<p>${inline(z)}</p>`);
  }
  listeSchliessen();
  return out.join("\n");
}

/* ---------- kleine Icons/Effekte ---------- */
function Dot() {
  return <span className="acc-dot inline-block h-1.5 w-1.5 rounded-full bg-zinc-500" />;
}
function Spinner() {
  return (
    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" opacity="0.3" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}
function SendIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 12l16-8-6 8 6 8-16-8z" fill="currentColor" />
    </svg>
  );
}
function GlobeIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
      <path d="M3 12h18M12 3c2.5 2.5 2.5 15.5 0 18M12 3c-2.5 2.5-2.5 15.5 0 18" stroke="currentColor" strokeWidth="1.6" fill="none" />
    </svg>
  );
}
function GlobeSpin() {
  return (
    <svg className="h-4 w-4 acc-spin-slow" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
      <path d="M3 12h18M12 3c2.5 2.5 2.5 15.5 0 18M12 3c-2.5 2.5-2.5 15.5 0 18" stroke="currentColor" strokeWidth="1.6" fill="none" />
    </svg>
  );
}

const acsStyles = `
.acc-md > * + * { margin-top: 0.55rem; }
.acc-md .acc-h { font-weight: 700; letter-spacing: -0.01em; margin-top: 0.9rem; }
.acc-md h2.acc-h { font-size: 1.05rem; }
.acc-md h3.acc-h { font-size: 0.98rem; }
.acc-md .acc-ul, .acc-md .acc-ol { padding-left: 1.15rem; }
.acc-md .acc-ul { list-style: disc; }
.acc-md .acc-ol { list-style: decimal; }
.acc-md li { margin-top: 0.2rem; }
.acc-md a { color: #ffb35c; text-decoration: underline; text-underline-offset: 2px; }
.acc-md strong { color: #fff; font-weight: 700; }
.acc-md .acc-inline { background: rgba(255,255,255,0.08); border-radius: 5px; padding: 0.05rem 0.32rem; font-family: ui-monospace,monospace; font-size: 0.86em; }
.acc-md .acc-code { background: rgba(0,0,0,0.45); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 0.7rem 0.85rem; overflow-x: auto; font-family: ui-monospace,monospace; font-size: 0.82rem; line-height: 1.5; }
.acc-dot { animation: accBlink 1.2s infinite ease-in-out; }
.acc-dot:nth-child(2){ animation-delay: 0.2s; } .acc-dot:nth-child(3){ animation-delay: 0.4s; }
@keyframes accBlink { 0%,80%,100%{ opacity: 0.25; } 40%{ opacity: 1; } }
.acc-spin-slow { animation: accSpin 2.2s linear infinite; }
@keyframes accSpin { to { transform: rotate(360deg); } }
`;
