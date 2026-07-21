"use client";

/**
 * Admin-Konsole // Lizenzschluessel erzeugen (JARVIS-HUD-Stil).
 *
 * Interne Seite (KEIN Link von Landing/Dashboard – nur ueber die URL /admin
 * erreichbar). Erzeugt Lizenzschluessel per Klick gegen POST
 * /api/admin/generate: Passwort + Plan + Anzahl -> Liste von Schluesseln
 * mit Kopier-Funktion. Das Passwort wird bis zum Schliessen des Tabs in
 * sessionStorage gehalten, aber nie im localStorage persistiert.
 */

import { useCallback, useEffect, useState } from "react";

const PLANS = ["STARTER", "PROFESSIONAL", "BUSINESS", "ENTERPRISE"] as const;
type Plan = (typeof PLANS)[number];

const PASSWORD_KEY = "acc-admin-password";
const FOCUS_RING =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#ff8c2a]/70";

/** Kopiert Text; gibt true bei Erfolg. Fallback fuer aeltere Browser. */
async function copyText(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    /* faellt unten auf execCommand zurueck */
  }
  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return ok;
  } catch {
    return false;
  }
}

/** Zeile mit einem erzeugten Schluessel + Kopieren-Button. */
function KeyRow({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  const onCopy = useCallback(async () => {
    if (await copyText(value)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  }, [value]);
  return (
    <li className="flex items-center gap-2 rounded-sm border border-[#ff8c2a]/15 bg-[#ff8c2a]/[0.03] px-3 py-2">
      <code className="flex-1 break-all font-mono text-xs text-[#fff3e2] sm:text-sm">
        {value}
      </code>
      <button
        onClick={onCopy}
        className={`shrink-0 rounded-sm border border-[#ff8c2a]/40 px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.14em] text-[#ffb35c] transition-colors hover:bg-[#ff8c2a]/15 ${FOCUS_RING}`}
      >
        {copied ? "Kopiert" : "Kopieren"}
      </button>
    </li>
  );
}

export default function AdminPage() {
  const [password, setPassword] = useState("");
  const [plan, setPlan] = useState<Plan>("STARTER");
  const [count, setCount] = useState(1);
  const [keys, setKeys] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [copiedAll, setCopiedAll] = useState(false);

  // Passwort bis zum Tab-Schliessen merken (sessionStorage, nicht localStorage).
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(PASSWORD_KEY);
      if (saved) setPassword(saved);
    } catch {
      /* sessionStorage nicht verfuegbar */
    }
  }, []);

  useEffect(() => {
    try {
      if (password) sessionStorage.setItem(PASSWORD_KEY, password);
      else sessionStorage.removeItem(PASSWORD_KEY);
    } catch {
      /* ignorieren */
    }
  }, [password]);

  const generate = useCallback(async () => {
    if (busy || !password.trim()) return;
    setBusy(true);
    setError("");
    setKeys([]);
    try {
      const res = await fetch("/api/admin/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password, plan, count }),
      });
      const data = (await res.json().catch(() => null)) as
        | { keys?: string[]; error?: string }
        | null;
      if (res.ok && Array.isArray(data?.keys)) {
        setKeys(data.keys);
      } else {
        setError(data?.error ?? `Server antwortete mit ${res.status}.`);
      }
    } catch {
      setError("Verbindung fehlgeschlagen. Bitte erneut versuchen.");
    } finally {
      setBusy(false);
    }
  }, [busy, password, plan, count]);

  const copyAll = useCallback(async () => {
    if (keys.length === 0) return;
    if (await copyText(keys.join("\n"))) {
      setCopiedAll(true);
      setTimeout(() => setCopiedAll(false), 1500);
    }
  }, [keys]);

  return (
    <main className="relative min-h-screen bg-[#0b0a08] text-[#e8dcc8]">
      <div className="hud-texture" aria-hidden />

      <header className="border-b border-[#ff8c2a]/15 bg-[#0b0a08]/85 backdrop-blur">
        <div className="mx-auto flex min-h-16 max-w-3xl items-center justify-between px-5 py-2">
          <div>
            <span className="text-lg font-bold tracking-tight text-[#fff3e2]">
              AI <span className="text-[#ff8c2a]">Command Center</span>
            </span>
            <div className="hud-label">Admin // Lizenz-Konsole</div>
          </div>
          <span className="hud-pulse h-1.5 w-1.5 rounded-full bg-[#ff8c2a]" aria-hidden />
        </div>
      </header>

      <div className="relative z-10 mx-auto max-w-3xl px-5 py-8">
        <section aria-label="Schluessel erzeugen" className="hud-panel hud-corners rounded-sm p-5 sm:p-6">
          <div className="hud-label mb-2">Lizenz // Generator</div>
          <h1 className="text-2xl font-bold text-[#fff3e2]">Lizenzschluessel erzeugen</h1>
          <p className="mt-1 text-sm text-[#c9b391]">
            Pro Kundenkauf einen Schluessel erzeugen und per E-Mail senden. Die
            Schluessel passen zum LICENSE_SECRET dieser Installation.
          </p>

          <div className="mt-6 grid grid-cols-1 gap-4">
            <label className="block">
              <span className="hud-label">Admin-Passwort</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && generate()}
                autoComplete="current-password"
                placeholder="••••••••"
                disabled={busy}
                aria-label="Admin-Passwort"
                className={`mt-1.5 w-full rounded-sm border border-[#ff8c2a]/25 bg-[#ff8c2a]/[0.04] px-4 py-3 font-mono text-sm text-[#fff3e2] placeholder:text-[#8a7455] outline-none transition focus:border-[#ff8c2a]/70 focus:ring-2 focus:ring-[#ff8c2a]/20 ${FOCUS_RING}`}
              />
            </label>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="hud-label">Plan</span>
                <select
                  value={plan}
                  onChange={(e) => setPlan(e.target.value as Plan)}
                  disabled={busy}
                  aria-label="Plan"
                  className={`mt-1.5 w-full rounded-sm border border-[#ff8c2a]/25 bg-[#ff8c2a]/[0.04] px-4 py-3 font-mono text-sm text-[#fff3e2] outline-none transition focus:border-[#ff8c2a]/70 focus:ring-2 focus:ring-[#ff8c2a]/20 ${FOCUS_RING}`}
                >
                  {PLANS.map((p) => (
                    <option key={p} value={p} className="bg-[#0b0a08]">
                      {p}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="hud-label">Anzahl (1–50)</span>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={count}
                  onChange={(e) => {
                    const n = Number.parseInt(e.target.value, 10);
                    setCount(Number.isNaN(n) ? 1 : Math.min(50, Math.max(1, n)));
                  }}
                  disabled={busy}
                  aria-label="Anzahl"
                  className={`mt-1.5 w-full rounded-sm border border-[#ff8c2a]/25 bg-[#ff8c2a]/[0.04] px-4 py-3 font-mono text-sm text-[#fff3e2] outline-none transition focus:border-[#ff8c2a]/70 focus:ring-2 focus:ring-[#ff8c2a]/20 ${FOCUS_RING}`}
                />
              </label>
            </div>

            <button
              onClick={generate}
              disabled={!password.trim() || busy}
              className={`mt-1 w-full rounded-sm bg-[#ff8c2a] px-6 py-3 font-semibold text-[#1a0f04] transition hover:bg-[#ffb35c] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 ${FOCUS_RING}`}
            >
              {busy ? "Erzeuge …" : "Schluessel erzeugen"}
            </button>
          </div>

          {error && (
            <p
              role="alert"
              className="mt-4 rounded-sm border border-red-400/30 bg-red-400/10 px-4 py-2 text-sm text-red-300"
            >
              {error}
            </p>
          )}
        </section>

        {keys.length > 0 && (
          <section
            aria-label="Erzeugte Schluessel"
            className="hud-panel hud-corners mt-6 rounded-sm p-5 sm:p-6"
          >
            <div className="mb-3 flex items-center justify-between gap-2">
              <div className="hud-label">
                Ergebnis // {keys.length} {keys.length === 1 ? "Schluessel" : "Schluessel"} ({plan})
              </div>
              <button
                onClick={copyAll}
                className={`shrink-0 rounded-sm border border-[#ffb35c]/40 bg-[#ff8c2a]/[0.06] px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-[#ffb35c] transition-colors hover:bg-[#ff8c2a]/15 ${FOCUS_RING}`}
              >
                {copiedAll ? "Alle kopiert" : "Alle kopieren"}
              </button>
            </div>
            <ul className="space-y-2">
              {keys.map((k) => (
                <KeyRow key={k} value={k} />
              ))}
            </ul>
          </section>
        )}
      </div>
    </main>
  );
}
