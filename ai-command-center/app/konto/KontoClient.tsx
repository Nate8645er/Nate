"use client";

/**
 * Kundenportal (leichtgewichtig, ohne Login-Zwang): zeigt das aktuelle Abo aus
 * dem Browser-Zustand, eine Kauf-Bestätigung nach dem Checkout und die nächsten
 * Schritte. Die vollständige Abo-Verwaltung (Rechnungen, Kündigung) wird über
 * das Stripe-Kundenportal angebunden, sobald die Zahlung konfiguriert ist.
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { PAKETE } from "@/lib/preise";

export default function KontoClient() {
  const [plan, setPlan] = useState<string | null>(null);
  const [wunsch, setWunsch] = useState<string | null>(null);
  const [kaufErfolg, setKaufErfolg] = useState<string | null>(null);
  const [geladen, setGeladen] = useState(false);

  useEffect(() => {
    try {
      setPlan(localStorage.getItem("acc-plan"));
      setWunsch(localStorage.getItem("acc-plan-wunsch"));
      const q = new URLSearchParams(window.location.search);
      if (q.get("kauf") === "erfolg") setKaufErfolg(q.get("paket"));
    } catch {
      /* localStorage/URL nicht verfügbar */
    }
    setGeladen(true);
  }, []);

  const aktiv = plan ?? wunsch;
  const paket = PAKETE.find((p) => p.planId === aktiv);

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-bold tracking-tight">Mein Konto</h1>

      {kaufErfolg && (
        <div className="mt-6 rounded-2xl border border-[#bfe6cf] bg-[#f0faf4] p-5">
          <p className="font-semibold text-[#177245]">Vielen Dank für Ihren Kauf! 🎉</p>
          <p className="mt-1 text-sm text-[#4a4335]">
            Ihr Zugang wird eingerichtet. Den Lizenzschlüssel erhalten Sie per E-Mail –
            damit öffnen Sie sofort Ihr Dashboard.
          </p>
        </div>
      )}

      <section className="acc-card mt-6 rounded-2xl p-6">
        <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Ihr Abo</p>
        {geladen && paket ? (
          <>
            <h2 className="mt-1 text-2xl font-bold">{paket.name}</h2>
            <p className="mt-1 text-sm text-[#6f6557]">{paket.untertitel}</p>
          </>
        ) : (
          <>
            <h2 className="mt-1 text-2xl font-bold">Noch kein Abo aktiv</h2>
            <p className="mt-1 text-sm text-[#6f6557]">
              Wählen Sie ein Paket, um Ihre KI-Abteilung freizuschalten.
            </p>
          </>
        )}
        <div className="mt-5 flex flex-wrap gap-3">
          <Link
            href="/dashboard"
            className="rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-5 py-2.5 text-sm font-bold text-white hover:brightness-105"
          >
            Zum Dashboard
          </Link>
          <Link
            href="/onboarding"
            className="rounded-full border border-[#e0d8c6] bg-white px-5 py-2.5 text-sm font-semibold text-[#1c1917] hover:border-[#ffb066] hover:text-[#c25e0e]"
          >
            Einrichtung & Videos
          </Link>
          <Link
            href="/preise"
            className="rounded-full border border-[#e0d8c6] bg-white px-5 py-2.5 text-sm font-semibold text-[#1c1917] hover:border-[#ffb066] hover:text-[#c25e0e]"
          >
            Abo wechseln
          </Link>
        </div>
      </section>

      <section className="acc-card mt-6 rounded-2xl p-6">
        <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Zahlung & Rechnungen</p>
        <p className="mt-2 text-sm text-[#4a4335]">
          Die Verwaltung von Zahlung, Rechnungen und Kündigung läuft über das sichere
          Stripe-Kundenportal. Es wird aktiv, sobald die Zahlung für Ihren Shop
          konfiguriert ist.
        </p>
      </section>
    </div>
  );
}
