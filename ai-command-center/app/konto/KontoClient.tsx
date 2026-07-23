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

  // Login-Status (Supabase). Client kennt die öffentlichen NEXT_PUBLIC_*-Werte.
  const loginAktiv =
    Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL) &&
    Boolean(process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
  const [modus, setModus] = useState<"anmelden" | "registrieren">("anmelden");
  const [email, setEmail] = useState("");
  const [passwort, setPasswort] = useState("");
  const [angemeldet, setAngemeldet] = useState<string | null>(null);
  const [authFehler, setAuthFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  const [aboStatus, setAboStatus] = useState<string | null>(null);
  const [portalLaeuft, setPortalLaeuft] = useState(false);

  // Echten Plan aus dem Kunden-Store laden (nur wenn angemeldet; sonst 401 → ignorieren).
  async function aboLaden() {
    try {
      const res = await fetch("/api/mein-abo");
      if (!res.ok) return;
      const data = (await res.json()) as { planId?: string; status?: string };
      if (data.planId) {
        setPlan(data.planId);
        setAboStatus(data.status ?? null);
        try {
          localStorage.setItem("acc-plan", data.planId);
        } catch {
          /* localStorage nicht verfügbar */
        }
      }
    } catch {
      /* nicht angemeldet / Netzwerk – stiller Fallback auf lokalen Zustand */
    }
  }

  // Öffnet das Stripe-Kundenportal (customerId kommt serverseitig aus der Sitzung).
  async function portalOeffnen() {
    setPortalLaeuft(true);
    try {
      const res = await fetch("/api/portal", { method: "POST" });
      const data = (await res.json()) as { url?: string };
      if (res.ok && data.url) {
        window.location.assign(data.url);
        return;
      }
    } catch {
      /* Netzwerkfehler */
    } finally {
      setPortalLaeuft(false);
    }
  }

  async function authSenden(e: React.FormEvent) {
    e.preventDefault();
    setAuthFehler(null);
    setLaeuft(true);
    try {
      const pfad = modus === "anmelden" ? "/api/auth/login" : "/api/auth/register";
      const res = await fetch(pfad, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, passwort }),
      });
      const data = (await res.json()) as { user?: { email: string | null }; error?: string; meldung?: string };
      if (res.ok && data.user) {
        setAngemeldet(data.user.email ?? email);
        void aboLaden();
      } else if (res.status === 501) {
        setAuthFehler("Login ist für diesen Shop noch nicht aktiviert.");
      } else {
        setAuthFehler(data.meldung ?? "Anmeldung fehlgeschlagen. Bitte Daten prüfen.");
      }
    } catch {
      setAuthFehler("Netzwerkfehler. Bitte erneut versuchen.");
    } finally {
      setLaeuft(false);
    }
  }

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
    // Falls bereits eine Sitzung besteht: echten Plan laden (401 wird ignoriert).
    void aboLaden();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
            <h2 className="mt-1 text-2xl font-bold">
              {paket.name}
              {aboStatus && aboStatus !== "active" && (
                <span className="ml-2 rounded-full bg-[#fff0e6] px-2 py-0.5 align-middle text-xs font-bold text-[#c25e0e]">
                  {aboStatus === "canceled" ? "gekündigt" : aboStatus}
                </span>
              )}
            </h2>
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
        <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Kundenkonto</p>
        {angemeldet ? (
          <p className="mt-2 text-sm text-[#4a4335]">
            Angemeldet als <strong>{angemeldet}</strong>. Ihr Zugang ist mit Ihrem Konto verknüpft.
          </p>
        ) : loginAktiv ? (
          <>
            <div className="mt-3 flex gap-2 text-sm font-semibold">
              <button
                type="button"
                onClick={() => setModus("anmelden")}
                className={`rounded-full px-4 py-1.5 ${modus === "anmelden" ? "bg-[#1c1917] text-white" : "border border-[#e0d8c6] text-[#4a4335]"}`}
              >
                Anmelden
              </button>
              <button
                type="button"
                onClick={() => setModus("registrieren")}
                className={`rounded-full px-4 py-1.5 ${modus === "registrieren" ? "bg-[#1c1917] text-white" : "border border-[#e0d8c6] text-[#4a4335]"}`}
              >
                Konto erstellen
              </button>
            </div>
            <form onSubmit={authSenden} className="mt-4 grid gap-3 sm:max-w-sm">
              <input
                type="email"
                required
                placeholder="E-Mail"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-xl border border-[#e0d8c6] bg-white px-4 py-2.5 text-sm"
              />
              <input
                type="password"
                required
                minLength={6}
                placeholder="Passwort"
                value={passwort}
                onChange={(e) => setPasswort(e.target.value)}
                className="rounded-xl border border-[#e0d8c6] bg-white px-4 py-2.5 text-sm"
              />
              {authFehler && <p className="text-sm font-medium text-[#b91c1c]">{authFehler}</p>}
              <button
                type="submit"
                disabled={laeuft}
                className="rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-5 py-2.5 text-sm font-bold text-white hover:brightness-105 disabled:opacity-60"
              >
                {laeuft ? "Bitte warten…" : modus === "anmelden" ? "Anmelden" : "Konto erstellen"}
              </button>
            </form>
          </>
        ) : (
          <p className="mt-2 text-sm text-[#4a4335]">
            Der Login wird aktiv, sobald das Kundenkonto (Supabase) für Ihren Shop
            konfiguriert ist. Bis dahin läuft der Zugang über den Lizenzschlüssel per E-Mail.
          </p>
        )}
      </section>

      <section className="acc-card mt-6 rounded-2xl p-6">
        <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Zahlung & Rechnungen</p>
        <p className="mt-2 text-sm text-[#4a4335]">
          Die Verwaltung von Zahlung, Rechnungen und Kündigung läuft über das sichere
          Stripe-Kundenportal.
        </p>
        <button
          type="button"
          onClick={portalOeffnen}
          disabled={portalLaeuft}
          className="mt-4 rounded-full border border-[#e0d8c6] bg-white px-5 py-2.5 text-sm font-semibold text-[#1c1917] hover:border-[#ffb066] hover:text-[#c25e0e] disabled:opacity-60"
        >
          {portalLaeuft ? "Öffne Portal…" : "Rechnungen & Kündigung verwalten"}
        </button>
        <p className="mt-2 text-xs text-[#8a8072]">
          Öffnet sich, sobald Sie angemeldet sind und ein Abo hinterlegt ist.
        </p>
      </section>
    </div>
  );
}
