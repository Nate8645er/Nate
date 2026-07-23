"use client";

/**
 * Premium-Verkaufsseite (Kino-Look, schnell, ohne schwere 3D-Abhängigkeiten).
 * Monats-/Jahres-Umschalter, Pakete, Feature-Vergleich, Vertrauens-Bereich, FAQ.
 * Der Kauf-Button hinterlegt die gewählte Stufe lokal und führt ins Onboarding;
 * die sichere Zahlung (Stripe) wird separat angebunden (ENV/Keys).
 */

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PAKETE, VERGLEICH, FAQ, chf, type Paket } from "@/lib/preise";

export default function PreiseClient() {
  const router = useRouter();
  const [jahr, setJahr] = useState(false);
  const [offen, setOffen] = useState<number | null>(0);

  const [ladend, setLadend] = useState<string | null>(null);

  async function waehlen(p: Paket) {
    try {
      localStorage.setItem("acc-plan-wunsch", p.planId);
    } catch {
      /* ignore */
    }
    if (p.id === "enterprise") {
      window.location.assign(
        "mailto:kontakt@ihre-domain.ch?subject=" +
          encodeURIComponent("Enterprise-Anfrage AI Command Center"),
      );
      return;
    }
    // Stripe-Checkout versuchen; ohne Konfiguration ehrlich ins Onboarding.
    setLadend(p.id);
    try {
      const res = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ paket: p.id, jahr }),
      });
      if (res.ok) {
        const data = (await res.json()) as { url?: string };
        if (data.url) {
          window.location.assign(data.url);
          return;
        }
      }
    } catch {
      /* Netzwerk-/Serverfehler → Fallback unten */
    } finally {
      setLadend(null);
    }
    router.push("/onboarding");
  }

  return (
    <div>
      {/* Kino-Hero */}
      <section className="acc-hero-dark relative overflow-hidden px-6 py-24 text-center">
        <div className="acc-hero-glow" aria-hidden="true" />
        <div className="relative mx-auto max-w-3xl">
          <p className="mb-4 text-[11px] font-bold uppercase tracking-[0.28em] text-[#c9c6ff]">
            AI Command Center · Preise
          </p>
          <h1 className="text-4xl font-extrabold leading-tight tracking-tight text-white sm:text-6xl">
            Ihre <span className="acc-grad-text">KI-Abteilung</span>
            <br />ab Tag 1 – zu Ihrem Preis
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-lg text-[#b9b7d4]">
            Kein Chatbot. Ein ganzes Team, das Ihre Aufträge bis zum fertigen
            Ergebnis erledigt – für Einzelunternehmer bis Grosskonzern.
          </p>

          {/* Abrechnungs-Umschalter */}
          <div className="mt-9 inline-flex items-center gap-1 rounded-full border border-white/15 bg-white/5 p-1 backdrop-blur">
            <button
              type="button"
              onClick={() => setJahr(false)}
              aria-pressed={!jahr}
              className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-colors ${
                !jahr ? "bg-white text-[#1c1917]" : "text-white/80 hover:text-white"
              }`}
            >
              Monatlich
            </button>
            <button
              type="button"
              onClick={() => setJahr(true)}
              aria-pressed={jahr}
              className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-colors ${
                jahr ? "bg-white text-[#1c1917]" : "text-white/80 hover:text-white"
              }`}
            >
              Jährlich <span className="text-[#34d399]">−2 Monate</span>
            </button>
          </div>
        </div>
      </section>

      {/* Pakete */}
      <section className="px-6 py-20">
        <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-3">
          {PAKETE.map((p) => (
            <div
              key={p.id}
              className={`relative flex flex-col rounded-3xl border p-7 transition-transform hover:-translate-y-1 ${
                p.hervorgehoben
                  ? "border-[#ffb066] bg-white shadow-[0_30px_80px_-30px_rgba(255,120,40,0.5)]"
                  : "acc-card"
              }`}
            >
              {p.badge && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-3 py-1 text-[11px] font-bold text-white shadow">
                  {p.badge}
                </span>
              )}
              <h2 className="text-xl font-bold text-[#1c1917]">{p.name}</h2>
              <p className="mt-1 text-sm text-[#6f6557]">{p.untertitel}</p>
              <div className="mt-5 flex items-end gap-1">
                <span className="text-4xl font-extrabold text-[#1c1917]">
                  {chf(jahr ? Math.round(p.preisJahr / 12) : p.preisMonat)}
                </span>
                <span className="mb-1 text-sm text-[#6f6557]">/ Monat</span>
              </div>
              <p className="mt-1 text-xs text-[#7c7161]">
                {jahr ? `${chf(p.preisJahr)} jährlich` : "monatlich kündbar"} · exkl. MwSt.
              </p>
              <p className="mt-3 text-xs font-semibold uppercase tracking-wider text-[#c25e0e]">
                {p.zielgruppe}
              </p>

              <ul className="mt-5 space-y-2.5 text-sm text-[#4a4335]">
                {p.leistungen.map((l) => (
                  <li key={l} className="flex gap-2">
                    <svg viewBox="0 0 20 20" className="mt-0.5 h-4 w-4 shrink-0 text-[#177245]" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <path d="m4 10.5 4 4 8-9" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <span>{l}</span>
                  </li>
                ))}
              </ul>

              <button
                type="button"
                onClick={() => waehlen(p)}
                disabled={ladend === p.id}
                className={`mt-7 w-full rounded-full px-5 py-3 text-sm font-bold transition-colors disabled:opacity-70 ${
                  p.hervorgehoben
                    ? "bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] text-white shadow-[0_10px_28px_-8px_rgba(255,110,30,0.6)] hover:brightness-105"
                    : "border border-[#e0d8c6] bg-white text-[#1c1917] hover:border-[#ffb066] hover:text-[#c25e0e]"
                }`}
              >
                {ladend === p.id ? "Einen Moment …" : p.cta}
              </button>
              <Link
                href={`/produkt/${p.id}`}
                className="mt-3 block text-center text-xs font-semibold text-[#c25e0e] hover:underline"
              >
                Details ansehen →
              </Link>
            </div>
          ))}
        </div>
        <p className="mx-auto mt-6 max-w-2xl text-center text-xs text-[#7c7161]">
          Beispielpreise – anpassbar in <code>lib/preise.ts</code>. Sichere Zahlung
          (Stripe) und automatische Rechnungen werden mit Ihren Zugangsdaten angebunden.
        </p>
      </section>

      {/* Vergleich */}
      <section className="border-t border-[#e8e1d2] px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-center text-3xl font-bold tracking-tight">
            Pakete im <span className="acc-grad-text">Vergleich</span>
          </h2>
          <div className="mt-10 overflow-x-auto">
            <table className="w-full min-w-[640px] border-collapse text-sm">
              <thead>
                <tr>
                  <th className="w-1/3 p-3 text-left font-semibold text-[#6f6557]"> </th>
                  {PAKETE.map((p) => (
                    <th key={p.id} className="p-3 text-center text-base font-bold text-[#1c1917]">
                      {p.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {VERGLEICH.map((g) => (
                  <FragmentGruppe key={g.gruppe} gruppe={g.gruppe} zeilen={g.zeilen} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Vertrauen */}
      <section className="border-t border-[#e8e1d2] bg-[#faf6ee] px-6 py-16">
        <div className="mx-auto grid max-w-5xl gap-6 sm:grid-cols-3">
          {[
            ["Sofort startklar", "Nach dem Kauf öffnen Sie Ihr Dashboard mit dem Lizenzschlüssel – kein Setup nötig."],
            ["Ihre Daten, geschützt", "Wichtige Schritte nur mit Ihrer Freigabe. Enterprise auch On-Premise."],
            ["Echte Ergebnisse", "Fertige E-Mails, Angebote, Berichte und Code – mit Qualitäts-Score."],
          ].map(([t, d]) => (
            <div key={t} className="acc-card rounded-2xl p-6 text-center">
              <p className="text-base font-bold text-[#1c1917]">{t}</p>
              <p className="mt-2 text-sm text-[#6f6557]">{d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-3xl">
          <h2 className="text-center text-3xl font-bold tracking-tight">
            Häufige <span className="acc-grad-text">Fragen</span>
          </h2>
          <div className="mt-8 space-y-3">
            {FAQ.map((f, i) => {
              const auf = offen === i;
              return (
                <div key={f.frage} className="acc-card overflow-hidden rounded-2xl">
                  <button
                    type="button"
                    onClick={() => setOffen(auf ? null : i)}
                    aria-expanded={auf}
                    className="flex w-full items-center justify-between gap-3 p-5 text-left"
                  >
                    <span className="font-semibold text-[#1c1917]">{f.frage}</span>
                    <span className={`shrink-0 text-[#c25e0e] transition-transform ${auf ? "rotate-45" : ""}`}>
                      <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                        <path d="M10 4v12M4 10h12" strokeLinecap="round" />
                      </svg>
                    </span>
                  </button>
                  {auf && <p className="px-5 pb-5 text-sm leading-relaxed text-[#4a4335]">{f.antwort}</p>}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Abschluss-CTA */}
      <section className="acc-hero-dark relative overflow-hidden px-6 py-20 text-center">
        <div className="acc-hero-glow" aria-hidden="true" />
        <div className="relative mx-auto max-w-2xl">
          <h2 className="text-3xl font-extrabold text-white sm:text-4xl">
            Bereit für Ihre <span className="acc-grad-text">KI-Abteilung</span>?
          </h2>
          <p className="mt-4 text-[#b9b7d4]">
            Starten Sie heute – Ihr Team ist in Minuten einsatzbereit.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => waehlen(PAKETE[1])}
              className="rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-7 py-3 text-sm font-bold text-white shadow-[0_10px_28px_-8px_rgba(255,110,30,0.6)] hover:brightness-105"
            >
              Jetzt starten
            </button>
            <Link
              href="/onboarding"
              className="rounded-full border border-white/20 px-7 py-3 text-sm font-semibold text-white hover:bg-white/10"
            >
              System ansehen
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

/** Eine Vergleichsgruppe (Kopfzeile + Zeilen). */
function FragmentGruppe({ gruppe, zeilen }: { gruppe: string; zeilen: { label: string; werte: [string, string, string] }[] }) {
  return (
    <>
      <tr>
        <td colSpan={4} className="pt-6 pb-2 text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">
          {gruppe}
        </td>
      </tr>
      {zeilen.map((z) => (
        <tr key={z.label} className="border-t border-[#efe9dd]">
          <td className="p-3 text-[#4a4335]">{z.label}</td>
          {z.werte.map((w, i) => (
            <td key={i} className="p-3 text-center font-medium text-[#1c1917]">{w}</td>
          ))}
        </tr>
      ))}
    </>
  );
}
