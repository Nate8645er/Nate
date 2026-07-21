"use client";

/**
 * KI-Chat für Mitarbeitende – aufgeräumtes Chat-Interface im Stil moderner
 * KI-Assistenten, in der Markenwelt des AI Command Center (dunkel + Amber).
 *
 * - Konversationen liegen in localStorage (acc-chat-conversations).
 * - Lizenz-/Usage-Token werden mit dem Dashboard geteilt (gleiche Keys),
 *   jede Antwort zählt auf das Tageslimit des Plans.
 * - Kein Streaming: /api/chat antwortet als JSON; die UI zeigt einen
 *   Denk-Indikator und blendet die Antwort weich ein.
 */

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

const CONVERSATIONS_KEY = "acc-chat-conversations";
const LICENSE_TOKEN_KEY = "acc-license-token";
const USAGE_TOKEN_KEY = "acc-usage-token";
const BRANCHE_KEY = "acc-branche";
const GROESSE_KEY = "acc-groesse";
const MAX_CONVERSATIONS = 30;

interface ChatMsg {
  role: "user" | "assistant";
  content: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: ChatMsg[];
  updatedAt: number;
}

interface UsageInfo {
  used: number;
  limit: number;
  plan: string;
}

const BEISPIELE = [
  "Schreib mir eine freundliche Antwort auf eine Kundenreklamation",
  "5 Social-Media-Ideen für diese Woche",
  "Erkläre mir kurz, was ein Deckungsbeitrag ist",
  "Formuliere ein Angebot für einen Website-Auftrag über 4'500 CHF",
];

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [usage, setUsage] = useState<UsageInfo | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  const active = conversations.find((c) => c.id === activeId) ?? null;

  /* Konversationen laden */
  useEffect(() => {
    try {
      const raw = localStorage.getItem(CONVERSATIONS_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Conversation[];
        if (Array.isArray(parsed)) {
          setConversations(parsed);
          if (parsed.length > 0) setActiveId(parsed[0].id);
        }
      }
    } catch {
      /* defekter Storage => leer starten */
    }
  }, []);

  const persist = useCallback((next: Conversation[]) => {
    setConversations(next);
    try {
      localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(next.slice(0, MAX_CONVERSATIONS)));
    } catch {
      /* Storage voll */
    }
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [active?.messages.length, loading]);

  const newConversation = useCallback(() => {
    setActiveId(null);
    setError(null);
    setSidebarOpen(false);
    inputRef.current?.focus();
  }, []);

  const deleteConversation = useCallback(
    (id: string) => {
      const next = conversations.filter((c) => c.id !== id);
      persist(next);
      if (activeId === id) setActiveId(next[0]?.id ?? null);
    },
    [conversations, activeId, persist],
  );

  const send = useCallback(
    async (text: string) => {
      const frage = text.trim();
      if (!frage || loading) return;
      setError(null);
      setInput("");
      setLoading(true);

      /* Konversation anlegen oder erweitern */
      let conv: Conversation;
      let rest: Conversation[];
      if (active) {
        conv = {
          ...active,
          messages: [...active.messages, { role: "user", content: frage }],
          updatedAt: Date.now(),
        };
        rest = conversations.filter((c) => c.id !== active.id);
      } else {
        conv = {
          id: `c${Date.now().toString(36)}`,
          title: frage.slice(0, 60),
          messages: [{ role: "user", content: frage }],
          updatedAt: Date.now(),
        };
        rest = conversations;
        setActiveId(conv.id);
      }
      persist([conv, ...rest]);

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
        const res = await fetch("/api/chat", {
          method: "POST",
          headers,
          body: JSON.stringify({ messages: conv.messages, context }),
        });
        const data = (await res.json()) as {
          ok: boolean;
          text?: string;
          error?: string;
          usage?: { token: string; used: number; limit: number; plan: string };
        };
        if (data.usage) {
          setUsage({ used: data.usage.used, limit: data.usage.limit, plan: data.usage.plan });
          try {
            localStorage.setItem(USAGE_TOKEN_KEY, data.usage.token);
          } catch {
            /* Storage voll */
          }
        }
        if (!data.ok || !data.text) {
          setError(data.error ?? "Die Antwort konnte nicht erstellt werden.");
        } else {
          const withAnswer: Conversation = {
            ...conv,
            messages: [...conv.messages, { role: "assistant", content: data.text }],
            updatedAt: Date.now(),
          };
          persist([withAnswer, ...rest]);
        }
      } catch {
        setError("Netzwerkfehler – bitte erneut versuchen.");
      } finally {
        setLoading(false);
      }
    },
    [active, conversations, loading, persist],
  );

  return (
    <div className="flex h-dvh bg-[#0b0a08] text-zinc-200">
      <div className="hud-texture" aria-hidden="true" />

      {/* Sidebar */}
      <aside
        className={`${sidebarOpen ? "flex" : "hidden"} fixed inset-y-0 left-0 z-40 w-72 flex-col border-r border-[#ff8c2a]/15 bg-[#0e0c0a] md:static md:flex`}
      >
        <div className="flex items-center gap-2 border-b border-[#ff8c2a]/15 px-4 py-4">
          <span className="hud-pulse inline-block h-2 w-2 rounded-full bg-[#ff8c2a]" />
          <span className="hud-label">AI Command Center</span>
        </div>
        <div className="p-3">
          <button
            onClick={newConversation}
            className="shop-btn w-full rounded-lg border border-[#ff8c2a]/40 bg-[#ff8c2a]/10 px-4 py-2.5 text-sm font-semibold text-[#ffb35c] transition hover:bg-[#ff8c2a]/20"
          >
            + Neuer Chat
          </button>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 pb-3" aria-label="Chat-Verlauf">
          {conversations.map((c) => (
            <div
              key={c.id}
              className={`group flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
                c.id === activeId
                  ? "bg-[#ff8c2a]/15 text-[#ffb35c]"
                  : "text-zinc-400 hover:bg-[#ff8c2a]/5 hover:text-zinc-200"
              }`}
            >
              <button
                onClick={() => {
                  setActiveId(c.id);
                  setSidebarOpen(false);
                }}
                className="flex-1 truncate text-left"
                title={c.title}
              >
                {c.title}
              </button>
              <button
                onClick={() => deleteConversation(c.id)}
                className="hidden text-zinc-600 hover:text-red-400 group-hover:block"
                aria-label={`Chat "${c.title}" löschen`}
              >
                ✕
              </button>
            </div>
          ))}
          {conversations.length === 0 && (
            <p className="px-3 py-2 text-xs text-zinc-600">Noch keine Chats.</p>
          )}
        </nav>
        <div className="border-t border-[#ff8c2a]/15 p-3 text-xs text-zinc-500">
          {usage ? (
            <p>
              {usage.plan} · {usage.used} von {usage.limit} heute
            </p>
          ) : (
            <p>Jede Antwort zählt als Mission.</p>
          )}
        </div>
      </aside>

      {/* Hauptbereich */}
      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        {/* Kopfzeile */}
        <header className="flex items-center justify-between border-b border-[#ff8c2a]/15 bg-[#0b0a08]/80 px-4 py-3 backdrop-blur">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen((v) => !v)}
              className="rounded-md border border-[#ff8c2a]/25 px-2.5 py-1.5 text-sm text-[#ffb35c] md:hidden"
              aria-label="Chat-Verlauf öffnen"
            >
              ☰
            </button>
            <h1 className="text-sm font-semibold text-white">KI-Chat</h1>
          </div>
          <nav className="flex items-center gap-4 text-sm text-zinc-400" aria-label="Bereiche">
            <Link href="/dashboard" className="hover:text-[#ffb35c]">Missionen</Link>
            <span className="text-[#ffb35c]">Chat</span>
            <Link href="/workflows" className="hover:text-[#ffb35c]">Autopilot</Link>
            <Link href="/integrationen" className="hidden hover:text-[#ffb35c] sm:inline">Integrationen</Link>
          </nav>
        </header>

        {/* Nachrichten */}
        <main className="flex-1 overflow-y-auto px-4 py-6">
          <div className="mx-auto max-w-3xl">
            {!active && (
              <div className="flex min-h-[50vh] flex-col items-center justify-center text-center">
                <p className="hud-label mb-4">Ihr persönlicher Assistent</p>
                <h2 className="text-balance text-3xl font-semibold text-white sm:text-4xl">
                  Womit kann Ihr KI-Team helfen?
                </h2>
                <p className="mt-3 max-w-md text-sm text-zinc-500">
                  Schnelle Fragen, Texte und Ideen hier im Chat – grosse fertige
                  Ergebnisse als Mission im Dashboard.
                </p>
                <div className="mt-8 grid w-full gap-2 sm:grid-cols-2">
                  {BEISPIELE.map((b) => (
                    <button
                      key={b}
                      onClick={() => send(b)}
                      className="shop-btn rounded-xl border border-[#ff8c2a]/20 bg-[#ff8c2a]/[0.04] px-4 py-3 text-left text-sm text-zinc-300 transition hover:border-[#ff8c2a]/50 hover:bg-[#ff8c2a]/10"
                    >
                      {b}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {active?.messages.map((m, i) =>
              m.role === "user" ? (
                <div key={i} className="mb-6 flex justify-end">
                  <div className="max-w-[85%] rounded-2xl rounded-br-md border border-[#ff8c2a]/25 bg-[#ff8c2a]/10 px-4 py-3 text-sm leading-relaxed text-zinc-100">
                    {m.content}
                  </div>
                </div>
              ) : (
                <div key={i} className="mb-8 flex gap-3">
                  <span
                    className="mt-1.5 inline-block h-2.5 w-2.5 shrink-0 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]"
                    aria-hidden="true"
                  />
                  <div className="hud-modal-in min-w-0 flex-1 text-sm leading-relaxed text-zinc-200">
                    <Rendered text={m.content} />
                  </div>
                </div>
              ),
            )}

            {loading && (
              <div className="mb-8 flex items-center gap-3 text-sm text-zinc-500">
                <span className="hud-pulse inline-block h-2.5 w-2.5 rounded-full bg-[#ff8c2a]" />
                Ihr Assistent denkt nach …
              </div>
            )}
            {error && (
              <p className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                {error}
              </p>
            )}
            <div ref={bottomRef} />
          </div>
        </main>

        {/* Eingabe */}
        <footer className="border-t border-[#ff8c2a]/15 bg-[#0b0a08]/90 px-4 py-4 backdrop-blur">
          <form
            className="mx-auto flex max-w-3xl items-end gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
          >
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send(input);
                }
              }}
              rows={Math.min(6, Math.max(1, input.split("\n").length))}
              placeholder="Frage oder Auftrag eingeben … (Enter zum Senden)"
              className="min-h-[48px] flex-1 resize-none rounded-xl border border-[#ff8c2a]/25 bg-[#12100d] px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-[#ff8c2a]/60 focus:outline-none"
              aria-label="Chat-Eingabe"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="shop-btn rounded-xl bg-gradient-to-r from-[#ffb066] via-[#ff8c2a] to-[#ff5f1f] px-5 py-3 text-sm font-bold text-[#1a0f04] disabled:opacity-40"
            >
              Senden
            </button>
          </form>
          <p className="mx-auto mt-2 max-w-3xl text-center text-[11px] text-zinc-600">
            KI-Antworten können Fehler enthalten. Wichtige Angaben bitte prüfen.
          </p>
        </footer>
      </div>
    </div>
  );
}

/** Sehr schlanke Markdown-Darstellung: Absätze, Listen, **fett**. */
function Rendered({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/);
  return (
    <div className="space-y-3">
      {blocks.map((block, bi) => {
        const lines = block.split("\n");
        const isList = lines.every((l) => /^\s*([-*]|\d+\.)\s+/.test(l.trim()) || !l.trim());
        if (isList) {
          return (
            <ul key={bi} className="list-disc space-y-1 pl-5">
              {lines
                .filter((l) => l.trim())
                .map((l, li) => (
                  <li key={li}>
                    <Bold text={l.replace(/^\s*([-*]|\d+\.)\s+/, "")} />
                  </li>
                ))}
            </ul>
          );
        }
        return (
          <p key={bi} className="whitespace-pre-wrap">
            <Bold text={block} />
          </p>
        );
      })}
    </div>
  );
}

/** Ersetzt **fett** durch <strong>, alles andere bleibt Text. */
function Bold({ text }: { text: string }) {
  const parts = text.split(/\*\*(.+?)\*\*/g);
  return (
    <>
      {parts.map((p, i) =>
        i % 2 === 1 ? (
          <strong key={i} className="font-semibold text-white">
            {p}
          </strong>
        ) : (
          p
        ),
      )}
    </>
  );
}

function safeGet(key: string): string | undefined {
  try {
    return localStorage.getItem(key) ?? undefined;
  } catch {
    return undefined;
  }
}
