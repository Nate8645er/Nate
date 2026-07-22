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

import { useEffect, useState } from "react";
import WorkNav from "@/app/components/WorkNav";
import WorkFooter from "@/app/components/WorkFooter";

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
    // Verbindung aus dem Kunden-Modul: ?an=empfaenger&auftrag=... vorbefüllen.
    try {
      const params = new URLSearchParams(window.location.search);
      const an = params.get("an");
      const auftragParam = params.get("auftrag");
      if (an) setEmpfaenger(an.slice(0, 120));
      if (auftragParam) {
        setModus("neu");
        setAuftrag(auftragParam.slice(0, 2000));
      }
    } catch {
      /* Query nicht lesbar */
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
    <div className="acc-page min-h-dvh text-[#1c1917]">
      <div className="mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#e8e1d2] py-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <WorkNav aktiv="email" variante="hell" />
        </header>

        <div className="acc-in pt-10">
          <p className="mb-3 text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">E-Mail-Zentrale</p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Ihre KI erledigt die <span className="acc-grad-text">E-Mail-Arbeit</span>
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#8d8172]">
            Eingehende E-Mail einfügen und die fertige Antwort erhalten – oder
            der KI sagen, welche E-Mail sie schreiben soll. Ein Klick öffnet
            Gmail mit Empfänger, Betreff und Text bereits ausgefüllt: Sie
            drücken nur noch auf Senden.
          </p>
          <p className="mt-3 max-w-2xl rounded-xl border border-[#ffb066]/40 bg-[#fff4e6] px-4 py-3 text-xs leading-relaxed text-[#c25e0e]">
            Transparenz: Vollautomatischer Versand direkt aus Ihrem Postfach
            (ganz ohne Klick) braucht die OAuth-Freigabe Ihres Google-Kontos –
            das richten wir als Enterprise-Anbindung pro Kunde ein.
          </p>
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_1fr]">
          {/* Eingabe */}
          <section className="acc-card rounded-2xl p-5">
            <div className="flex gap-2" role="group" aria-label="Modus">
              <button
                onClick={() => setModus("antwort")}
                aria-pressed={modus === "antwort"}
                className={`shop-btn rounded-xl px-4 py-2 text-sm font-semibold ${
                  modus === "antwort"
                    ? "bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] text-white shadow-[0_6px_20px_-6px_rgba(255,110,30,0.5)]"
                    : "border border-[#e0d8c6] bg-white/70 text-[#4a4335] hover:border-[#ffb066]"
                }`}
              >
                Antworten
              </button>
              <button
                onClick={() => setModus("neu")}
                aria-pressed={modus === "neu"}
                className={`shop-btn rounded-xl px-4 py-2 text-sm font-semibold ${
                  modus === "neu"
                    ? "bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] text-white shadow-[0_6px_20px_-6px_rgba(255,110,30,0.5)]"
                    : "border border-[#e0d8c6] bg-white/70 text-[#4a4335] hover:border-[#ffb066]"
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
                className="mt-4 w-full resize-y rounded-xl border border-[#e0d8c6] bg-white/70 px-4 py-3 text-sm placeholder:text-[#a89c8a] focus:border-[#ffb066] focus:outline-none"
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
              className="mt-3 w-full resize-y rounded-xl border border-[#e0d8c6] bg-white/70 px-4 py-3 text-sm placeholder:text-[#a89c8a] focus:border-[#ffb066] focus:outline-none"
              aria-label="Auftrag an die KI"
            />

            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <input
                value={empfaenger}
                onChange={(e) => setEmpfaenger(e.target.value)}
                type="email"
                placeholder="Empfänger (optional)"
                className="rounded-xl border border-[#e0d8c6] bg-white/70 px-4 py-2.5 text-sm placeholder:text-[#a89c8a] focus:border-[#ffb066] focus:outline-none"
                aria-label="Empfänger-Adresse"
              />
              <input
                value={signatur}
                onChange={(e) => signaturSpeichern(e.target.value)}
                placeholder="Ihre Signatur, z. B. «Blin Murseli, ZEHNTAGE»"
                className="rounded-xl border border-[#e0d8c6] bg-white/70 px-4 py-2.5 text-sm placeholder:text-[#a89c8a] focus:border-[#ffb066] focus:outline-none"
                aria-label="Signatur (wird gespeichert)"
              />
            </div>

            <button
              onClick={erstellen}
              disabled={loading || (modus === "antwort" ? !eingehend.trim() : !auftrag.trim())}
              className="shop-btn mt-4 w-full rounded-xl bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-5 py-3 text-sm font-bold text-white shadow-[0_6px_20px_-6px_rgba(255,110,30,0.5)] disabled:opacity-40"
            >
              {loading ? "Ihre E-Mail-Abteilung schreibt …" : "E-Mail erstellen lassen"}
            </button>
            {usage && (
              <p className="mt-2 text-center text-[11px] text-[#a89c8a]">
                {usage.plan} · {usage.used} von {usage.limit} heute
              </p>
            )}
          </section>

          {/* Ergebnis */}
          <section className="acc-card rounded-2xl p-5">
            <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Versandfertige E-Mail</p>
            {!ergebnis && !loading && !error && (
              <p className="mt-4 text-sm text-[#8d8172]">
                Hier erscheint Ihre fertige E-Mail – mit Betreff, Text und
                Ihrer Signatur.
              </p>
            )}
            {loading && (
              <p className="mt-4 flex items-center gap-2 text-sm text-[#c25e0e]">
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
                Entwurf wird geschrieben …
              </p>
            )}
            {error && (
              <p className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                {error}
              </p>
            )}
            {ergebnis && (
              <>
                <div className="mt-4 rounded-xl border border-[#e0d8c6] bg-white/70 p-4">
                  <p className="text-xs text-[#8d8172]">Betreff</p>
                  <p className="mt-0.5 font-semibold text-[#1c1917]">{ergebnis.betreff}</p>
                  <p className="mt-3 text-xs text-[#8d8172]">Text</p>
                  <p className="mt-0.5 whitespace-pre-wrap text-sm leading-relaxed text-[#4a4335]">
                    {ergebnis.text}
                  </p>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <a
                    href={gmailLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="shop-btn rounded-xl bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-4 py-2.5 text-sm font-bold text-white shadow-[0_6px_20px_-6px_rgba(255,110,30,0.5)]"
                  >
                    In Gmail öffnen – nur noch senden
                  </a>
                  <button
                    onClick={kopieren}
                    className="shop-btn rounded-xl border border-[#e0d8c6] bg-white/70 px-4 py-2.5 text-sm font-semibold text-[#4a4335] hover:border-[#ffb066]"
                  >
                    {kopiert ? "Kopiert ✓" : "Kopieren"}
                  </button>
                  <a
                    href={`mailto:${encodeURIComponent(empfaenger.trim())}?subject=${encodeURIComponent(ergebnis.betreff)}&body=${encodeURIComponent(ergebnis.text.slice(0, 1800))}`}
                    className="shop-btn rounded-xl border border-[#e0d8c6] bg-white/70 px-4 py-2.5 text-sm text-[#8d8172] hover:border-[#ffb066]"
                  >
                    Anderes Mailprogramm
                  </a>
                </div>
              </>
            )}
          </section>
        </div>
        <WorkFooter variante="hell" />
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
