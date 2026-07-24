"use client";

/**
 * „Mein KI-Zugang" — der Kunde hinterlegt seinen EIGENEN LLM-Schlüssel, um sein
 * Unternehmen mit dem KI-System zu verbinden. Der Schlüssel bleibt
 * ausschliesslich in diesem Browser (localStorage) und wird pro Mission als
 * Header mitgeschickt — er wird nie an einen Server gespeichert. So trägt der
 * Kunde seine KI-Nutzungskosten selbst (Bring your own key).
 */

import { useEffect, useState } from "react";
import { PROVIDER_LABEL, PROVIDER_LISTE } from "@/lib/agents/kundenschluessel";
import {
  kundenSchluesselLaden,
  kundenSchluesselLoeschen,
  kundenSchluesselSpeichern,
} from "@/lib/kundenschluessel-client";

const DOKU: Partial<Record<string, string>> = {
  anthropic: "console.anthropic.com → API Keys",
  openai: "platform.openai.com → API keys",
  google: "aistudio.google.com → Get API key",
  xai: "console.x.ai",
  deepseek: "platform.deepseek.com",
  mistral: "console.mistral.ai",
  qwen: "dashscope.console.aliyun.com",
  moonshot: "platform.moonshot.cn",
};

export default function KiZugang() {
  const [provider, setProvider] = useState<string>("anthropic");
  const [key, setKey] = useState("");
  const [gespeichert, setGespeichert] = useState<string | null>(null);
  const [zeigen, setZeigen] = useState(false);

  useEffect(() => {
    const s = kundenSchluesselLaden();
    if (s) {
      setProvider(s.provider);
      setGespeichert(s.provider);
    }
  }, []);

  const speichern = () => {
    const k = key.trim();
    if (k.length < 12) return;
    kundenSchluesselSpeichern(provider, k);
    setGespeichert(provider);
    setKey("");
    setZeigen(false);
  };

  const entfernen = () => {
    kundenSchluesselLoeschen();
    setGespeichert(null);
    setKey("");
  };

  const feldKlasse =
    "rounded-xl border border-[#e0d8c6] bg-[#faf8f3] px-4 py-2.5 text-sm focus:border-[#ffb066] focus:outline-none";

  return (
    <section className="mt-6 rounded-2xl acc-card p-6">
      <h2 className="text-lg font-semibold">Mein KI-Zugang</h2>
      <p className="mt-1 text-sm text-[#6f6557]">
        Verbinden Sie Ihr Unternehmen mit Ihrem <strong>eigenen KI-Schlüssel</strong>.
        Die KI läuft dann auf Ihrem Konto — Ihr Schlüssel bleibt nur in diesem
        Browser und wird nie auf unseren Servern gespeichert.
      </p>

      {gespeichert ? (
        <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
          <span className="inline-flex items-center rounded-full bg-[#e7f6ee] px-3 py-1 font-medium text-[#177245]">
            ✓ Verbunden: {PROVIDER_LABEL[gespeichert as keyof typeof PROVIDER_LABEL] ?? gespeichert}
          </span>
          <button onClick={entfernen} className="text-[#6f6557] underline hover:text-[#3a3428]">
            Schlüssel entfernen
          </button>
        </div>
      ) : (
        <p className="mt-3 text-sm font-medium text-[#b45309]">Noch kein eigener Schlüssel hinterlegt.</p>
      )}

      <div className="mt-4 grid gap-3 sm:grid-cols-[minmax(0,220px)_1fr_auto] sm:items-end">
        <label className="text-sm">
          <span className="text-[#6f6557]">Anbieter</span>
          <select value={provider} onChange={(e) => setProvider(e.target.value)} className={`mt-1 w-full ${feldKlasse}`}>
            {PROVIDER_LISTE.filter((p) => p !== "meta" && p !== "local").map((p) => (
              <option key={p} value={p}>{PROVIDER_LABEL[p]}</option>
            ))}
          </select>
        </label>

        <label className="text-sm">
          <span className="text-[#6f6557]">API-Schlüssel</span>
          <input
            type={zeigen ? "text" : "password"}
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="sk-…"
            autoComplete="off"
            spellCheck={false}
            className={`mt-1 w-full font-mono ${feldKlasse}`}
          />
        </label>

        <button
          onClick={speichern}
          disabled={key.trim().length < 12}
          className="rounded-xl bg-[#ff8c2a] px-5 py-2.5 font-medium text-white transition hover:brightness-105 disabled:opacity-40"
        >
          Speichern
        </button>
      </div>

      <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-[#8a7f6d]">
        <button onClick={() => setZeigen((v) => !v)} className="underline">
          {zeigen ? "Schlüssel verbergen" : "Schlüssel anzeigen"}
        </button>
        {DOKU[provider] ? <span>Schlüssel holen: {DOKU[provider]}</span> : null}
      </div>
    </section>
  );
}
