"use client";

/**
 * E-Mail-Zentrale: Die KI erledigt die E-Mail-Arbeit des Unternehmens.
 *
 * - "Antworten": eingehende E-Mail einfügen -> versandfertige Antwort.
 * - "Neu schreiben": Auftrag -> versandfertige E-Mail.
 * - Ergebnis mit einem Klick in Gmail geöffnet (Empfänger, Betreff und
 *   Text vorausgefüllt) oder kopiert – Handarbeit entfällt bis auf den
 *   Klick auf «Senden».
 * - Signatur wird lokal gespeichert (acc-email-signatur) und in jede
 *   E-Mail eingesetzt; Lizenz-/Usage-Token wie überall geteilt.
 *
 * Ehrlich im UI ausgewiesen: Vollautomatischer Versand direkt aus dem
 * Kunden-Postfach (ohne Klick) braucht die Google-OAuth-Freigabe des
 * Kunden und ist Teil der Enterprise-Anbindung.
 */

import Link from "next/link";
import { useEffect, useState } from "react";

const LICENSE_TOKEN_KEY = "acc-license-token";
const USAGE_TOKEN_KEY = "acc-usage-token";
const BRANCHE_KEY = "acc-branche";
const SIGNATUR_KEY = "acc-email-signatur";

type Modus = "antwort" | "neu";

interface Ergebnis {
  betreff: string;
  text: string;
}

export default function EmailPage() {
  const [modus, setModus] = useState<Modus>("antwort");
  const [eingehend, setEingehend] = useState("");
  const [auftrag, setAuftrag] = useState("");
  const [empfaenger, setEmpfaenger] = useState("");
  const [signatur, setSignatur] = useState("");
  const [ergebnis, setErgebnis] = useState<Ergebnis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [kopiert, setKopiert] = useState(false);
  const [usage, setUsage] = useState<{ used: number; limit: number; plan: string } | null>(null);

  useEffect(() => {
    try {
      const s = localStorage.getItem(SIGNATUR_KEY);
      if (s) setSignatur(s);
    } catch {
      /* Storage nicht lesbar */
    }
  }, []);

  const signaturSpeichern = (v: string) => {
    setSignatur(v);
    try {
      localStorage.setItem(SIGNATUR_KEY, v);
    } catch {
      /* voll */
    }
  };

  const erstellen = async () => {
    if (loading) return;
    if (modus === "antwort" && !eingehend.trim()) return;
    if (modus === "neu" && !auftrag.trim()) return;
    setLoading(true);
    setError(null);
    setErgebnis(null);
    setKopiert(false);
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
      const res = await fetch("/api/email", {
        method: "POST",
        headers,
        body: JSON.stringify({
          modus,
          auftrag: auftrag.trim() || undefined,
          eingehend: modus === "antwort" ? eingehend.trim() : undefined,
          branche: safeGet(BRANCHE_KEY),
          signatur: signatur.trim() || undefined,
        }),
      });
      const data = (await res.json()) as {
        ok: boolean;
        betreff?: string;
        text?: string;
        error?: string;
        usage?: { token: string; used: number; limit: number; plan: string };
      };
      if (data.usage) {
        setUsage({ used: data.usage.used, limit: data.usage.limit, plan: data.usage.plan });
        try {
          localStorage.setItem(USAGE_TOKEN_KEY, data.usage.token);
        } catch {
          /* voll */
        }
      }
      if (!data.ok || !data.betreff || !data.text) {
        setError(data.error ?? "Die E-Mail konnte nicht erstellt werden.");
      } else {
        setErgebnis({ betreff: data.betreff, text: data.text });
      }
    } catch {
      setError("Netzwerkfehler – bitte erneut versuchen.");
    } finally {
      setLoading(false);
    }
  };

  const gmailLink = ergebnis
    ? `https://mail.google.com/mail/?view=cm&fs=1${empfaenger.trim() ? `&to=${encodeURIComponent(empfaenger.trim())}` : ""}&su=${encodeURIComponent(ergebnis.betreff)}&body=${encodeURIComponent(ergebnis.text)}`
    : "#";

  const kopieren = async () => {
    if (!ergebnis) return;
    try {
      await navigator.clipboard.writeText(`Betreff: ${ergebnis.betreff}\n\n${ergebnis.text}`);
      setKopiert(true);
      setTimeout(() => setKopiert(false), 2000);
    } catch {
      /* Clipboard verweigert */
    }
  };

  return (
    <div className="min-h-dvh bg-[#0b0a08] text-zinc-200">
      <div className="hud-texture" aria-hidden="true" />
      <div className="relative z-10 mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#ff8c2a]/15 py-4">
          <div className="flex items-center gap-2">
            <span className="hud-pulse inline-block h-2 w-2 rounded-full bg-[#ff8c2a]" />
            <span className="hud-label">AI Command Center</span>
          </div>
          <nav className="flex items-center gap-4 text-sm text-zinc-400" aria-label="Bereiche">
            <Link href="/dashboard" className="hover:text-[#ffb35c]">Missionen</Link>
            <Link href="/chat" className="hover:text-[#ffb35c]">Kommando</Link>
            <span className="text-[#ffb35c]">E-Mail</span>
            <Link href="/workflows" className="hidden hover:text-[#ffb35c] sm:inline">Autopilot</Link>
            <Link href="/berichte" className="hidden hover:text-[#ffb35c] sm:inline">Berichte</Link>
          </nav>
        </header>

        <div className="pt-10">
          <p className="hud-label mb-3">E-Mail-Zentrale</p>
          <h1 className="text-3xl font-semibold text-white sm:text-4xl">
            Ihre KI erledigt die E-Mail-Arbeit
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-zinc-400">
            Eingehende E-Mail einfügen und die fertige Antwort erhalten – oder
            der KI sagen, welche E-Mail sie schreiben soll. Ein Klick öffnet
            Gmail mit Empfänger, Betreff und Text bereits ausgefüllt: Sie
            drücken nur noch auf Senden.
          </p>
          <p className="mt-3 max-w-2xl rounded-lg border border-[#ff8c2a]/20 bg-[#ff8c2a]/[0.05] px-4 py-3 text-xs leading-relaxed text-[#ffb35c]/90">
            Transparenz: Vollautomatischer Versand direkt aus Ihrem Postfach
            (ganz ohne Klick) braucht die OAuth-Freigabe Ihres Google-Kontos –
            das richten wir als Enterprise-Anbindung pro Kunde ein.
          </p>
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_1fr]">
          {/* Eingabe */}
          <section className="hud-panel hud-corners relative rounded-xl p-5">
            <div className="flex gap-2" role="group" aria-label="Modus">
              <button
                onClick={() => setModus("antwort")}
                aria-pressed={modus === "antwort"}
                className={`shop-btn rounded-lg px-4 py-2 text-sm font-semibold ${
                  modus === "antwort"
                    ? "bg-[#ff8c2a] text-[#1a0f04]"
                    : "border border-[#ff8c2a]/30 text-[#ffb35c]"
                }`}
              >
                Antworten
              </button>
              <button
                onClick={() => setModus("neu")}
                aria-pressed={modus === "neu"}
                className={`shop-btn rounded-lg px-4 py-2 text-sm font-semibold ${
                  modus === "neu"
                    ? "bg-[#ff8c2a] text-[#1a0f04]"
                    : "border border-[#ff8c2a]/30 text-[#ffb35c]"
                }`}
              >
                Neu schreiben
              </button>
            </div>

            {modus === "antwort" && (
              <textarea
                value={eingehend}
                onChange={(e) => setEingehend(e.target.value)}
                rows={8}
                placeholder="Eingehende E-Mail hier einfügen …"
                className="mt-4 w-full resize-y rounded-lg border border-[#ff8c2a]/25 bg-[#12100d] px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-[#ff8c2a]/60 focus:outline-none"
                aria-label="Eingehende E-Mail"
              />
            )}

            <textarea
              value={auftrag}
              onChange={(e) => setAuftrag(e.target.value)}
              rows={modus === "neu" ? 6 : 2}
              placeholder={
                modus === "neu"
                  ? "Was soll die E-Mail sagen? z. B. «Offerte an Firma Muster: Website-Redesign, 4'500 CHF, Lieferzeit 3 Wochen, freundlich aber bestimmt»"
                  : "Optionale Vorgabe für die Antwort, z. B. «Preisnachlass ablehnen, aber Alternativtermin anbieten»"
              }
              className="mt-3 w-full resize-y rounded-lg border border-[#ff8c2a]/25 bg-[#12100d] px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-[#ff8c2a]/60 focus:outline-none"
              aria-label="Auftrag an die KI"
            />

            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <input
                value={empfaenger}
                onChange={(e) => setEmpfaenger(e.target.value)}
                type="email"
                placeholder="Empfänger (optional)"
                className="rounded-lg border border-[#ff8c2a]/25 bg-[#12100d] px-4 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-[#ff8c2a]/60 focus:outline-none"
                aria-label="Empfänger-Adresse"
              />
              <input
                value={signatur}
                onChange={(e) => signaturSpeichern(e.target.value)}
                placeholder="Ihre Signatur, z. B. «Blin Murseli, ZEHNTAGE»"
                className="rounded-lg border border-[#ff8c2a]/25 bg-[#12100d] px-4 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-[#ff8c2a]/60 focus:outline-none"
                aria-label="Signatur (wird gespeichert)"
              />
            </div>

            <button
              onClick={erstellen}
              disabled={loading || (modus === "antwort" ? !eingehend.trim() : !auftrag.trim())}
              className="shop-btn mt-4 w-full rounded-lg bg-gradient-to-r from-[#ffb066] via-[#ff8c2a] to-[#ff5f1f] px-5 py-3 text-sm font-bold text-[#1a0f04] disabled:opacity-40"
            >
              {loading ? "Ihre E-Mail-Abteilung schreibt …" : "E-Mail erstellen lassen"}
            </button>
            {usage && (
              <p className="mt-2 text-center text-[11px] text-zinc-600">
                {usage.plan} · {usage.used} von {usage.limit} heute
              </p>
            )}
          </section>

          {/* Ergebnis */}
          <section className="hud-panel relative rounded-xl p-5">
            <p className="hud-label">Versandfertige E-Mail</p>
            {!ergebnis && !loading && !error && (
              <p className="mt-4 text-sm text-zinc-500">
                Hier erscheint Ihre fertige E-Mail – mit Betreff, Text und
                Ihrer Signatur.
              </p>
            )}
            {loading && (
              <p className="mt-4 flex items-center gap-2 text-sm text-[#ffb35c]">
                <span className="hud-pulse inline-block h-2 w-2 rounded-full bg-[#ff8c2a]" />
                Entwurf wird geschrieben …
              </p>
            )}
            {error && (
              <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                {error}
              </p>
            )}
            {ergebnis && (
              <>
                <div className="mt-4 rounded-lg border border-[#ff8c2a]/25 bg-[#12100d] p-4">
                  <p className="text-xs text-zinc-500">Betreff</p>
                  <p className="mt-0.5 font-semibold text-white">{ergebnis.betreff}</p>
                  <p className="mt-3 text-xs text-zinc-500">Text</p>
                  <p className="mt-0.5 whitespace-pre-wrap text-sm leading-relaxed text-zinc-200">
                    {ergebnis.text}
                  </p>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <a
                    href={gmailLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="shop-btn rounded-lg bg-gradient-to-r from-[#ffb066] via-[#ff8c2a] to-[#ff5f1f] px-4 py-2.5 text-sm font-bold text-[#1a0f04]"
                  >
                    In Gmail öffnen – nur noch senden
                  </a>
                  <button
                    onClick={kopieren}
                    className="shop-btn rounded-lg border border-[#ff8c2a]/40 px-4 py-2.5 text-sm font-semibold text-[#ffb35c]"
                  >
                    {kopiert ? "Kopiert ✓" : "Kopieren"}
                  </button>
                  <a
                    href={`mailto:${encodeURIComponent(empfaenger.trim())}?subject=${encodeURIComponent(ergebnis.betreff)}&body=${encodeURIComponent(ergebnis.text.slice(0, 1800))}`}
                    className="shop-btn rounded-lg border border-[#ff8c2a]/25 px-4 py-2.5 text-sm text-zinc-400"
                  >
                    Anderes Mailprogramm
                  </a>
                </div>
              </>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

function safeGet(key: string): string | undefined {
  try {
    return localStorage.getItem(key) ?? undefined;
  } catch {
    return undefined;
  }
}
