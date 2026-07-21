"use client";

/**
 * Einstellungen – der Einstellungsbereich für die KI.
 *
 * Bündelt alle lokalen Einstellungen des Arbeitsbereichs:
 * - Unternehmensprofil (Branche, Grösse) -> steuert jede Mission
 * - E-Mail-Signatur -> fliesst in die E-Mail-Zentrale
 * - Lizenz-Status mit Link zur Aktivierung im Dashboard
 * - Daten: Export aller Ergebnisse als JSON, gezieltes Löschen
 */

import Link from "next/link";
import { useEffect, useState } from "react";
import WorkNav from "@/app/components/WorkNav";

const BRANCHE_KEY = "acc-branche";
const GROESSE_KEY = "acc-groesse";
const SIGNATUR_KEY = "acc-email-signatur";
const PLAN_KEY = "acc-plan";

const BRANCHEN = [
  "Marketing/Agentur",
  "Handel/E-Commerce",
  "Handwerk/Bau",
  "Treuhand/Finanzen",
  "Gesundheit",
  "Software/IT",
  "Gastronomie",
  "Andere",
];
const GROESSEN = ["Solo", "2-10", "11-50", "50+"];

const DATEN_KEYS = [
  "acc-mission-history",
  "acc-kommandos",
  "acc-workflows",
  "acc-chat-conversations",
  "acc-benutzer",
  "acc-kunden",
];

export default function EinstellungenPage() {
  const [branche, setBranche] = useState("");
  const [groesse, setGroesse] = useState("");
  const [signatur, setSignatur] = useState("");
  const [plan, setPlan] = useState("FREE");
  const [meldung, setMeldung] = useState<string | null>(null);

  useEffect(() => {
    try {
      setBranche(localStorage.getItem(BRANCHE_KEY) ?? "");
      setGroesse(localStorage.getItem(GROESSE_KEY) ?? "");
      setSignatur(localStorage.getItem(SIGNATUR_KEY) ?? "");
      setPlan(localStorage.getItem(PLAN_KEY) ?? "FREE");
    } catch {
      /* Storage nicht lesbar */
    }
  }, []);

  const speichern = (key: string, wert: string) => {
    try {
      if (wert) localStorage.setItem(key, wert);
      else localStorage.removeItem(key);
      setMeldung("Gespeichert ✓");
      setTimeout(() => setMeldung(null), 1800);
    } catch {
      setMeldung("Speichern fehlgeschlagen (Speicher voll?)");
    }
  };

  const exportieren = () => {
    const daten: Record<string, unknown> = {};
    for (const k of DATEN_KEYS) {
      try {
        const raw = localStorage.getItem(k);
        if (raw) daten[k] = JSON.parse(raw);
      } catch {
        /* Eintrag überspringen */
      }
    }
    const blob = new Blob([JSON.stringify(daten, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ai-command-center-export.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const loeschen = (key: string, label: string) => {
    if (!window.confirm(`${label} wirklich unwiderruflich löschen?`)) return;
    try {
      localStorage.removeItem(key);
      setMeldung(`${label} gelöscht.`);
      setTimeout(() => setMeldung(null), 2500);
    } catch {
      /* nichts */
    }
  };

  return (
    <div className="min-h-dvh bg-[#faf8f3] text-[#241f17]">
      <div className="mx-auto max-w-3xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#e8e1d2] py-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <WorkNav aktiv="einstellungen" variante="hell" />
        </header>

        <div className="pt-10">
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Einstellungsbereich</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">So arbeitet Ihre KI für Sie</h1>
          {meldung && (
            <p className="mt-3 inline-block rounded-lg bg-[#e7f6ee] px-3 py-1.5 text-sm font-medium text-[#177245]">
              {meldung}
            </p>
          )}
        </div>

        {/* Unternehmensprofil */}
        <section className="mt-8 rounded-2xl border border-[#eee7d8] bg-white p-6 shadow-[0_1px_3px_rgba(40,30,10,0.05)]">
          <h2 className="text-lg font-semibold">Unternehmensprofil</h2>
          <p className="mt-1 text-sm text-[#8d8172]">
            Branche und Grösse fliessen in jeden Auftrag ein – Ihre Belegschaft
            liefert dadurch passende statt allgemeine Ergebnisse.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <select
              value={branche}
              onChange={(e) => {
                setBranche(e.target.value);
                speichern(BRANCHE_KEY, e.target.value);
              }}
              className="rounded-xl border border-[#e0d8c6] bg-[#faf8f3] px-4 py-2.5 text-sm focus:border-[#ffb066] focus:outline-none"
              aria-label="Branche"
            >
              <option value="">Branche wählen …</option>
              {BRANCHEN.map((b) => (
                <option key={b}>{b}</option>
              ))}
            </select>
            <select
              value={groesse}
              onChange={(e) => {
                setGroesse(e.target.value);
                speichern(GROESSE_KEY, e.target.value);
              }}
              className="rounded-xl border border-[#e0d8c6] bg-[#faf8f3] px-4 py-2.5 text-sm focus:border-[#ffb066] focus:outline-none"
              aria-label="Unternehmensgrösse"
            >
              <option value="">Grösse wählen …</option>
              {GROESSEN.map((g) => (
                <option key={g}>{g}</option>
              ))}
            </select>
          </div>
        </section>

        {/* Signatur */}
        <section className="mt-6 rounded-2xl border border-[#eee7d8] bg-white p-6 shadow-[0_1px_3px_rgba(40,30,10,0.05)]">
          <h2 className="text-lg font-semibold">E-Mail-Signatur</h2>
          <p className="mt-1 text-sm text-[#8d8172]">
            Wird in der{" "}
            <Link href="/email" className="font-medium text-[#c25e0e] hover:underline">E-Mail-Zentrale</Link>{" "}
            automatisch unter jede E-Mail gesetzt.
          </p>
          <textarea
            value={signatur}
            onChange={(e) => setSignatur(e.target.value)}
            onBlur={() => speichern(SIGNATUR_KEY, signatur.trim())}
            rows={3}
            placeholder={"Freundliche Grüsse\nVorname Name\nFirma"}
            className="mt-3 w-full resize-none rounded-xl border border-[#e0d8c6] bg-[#faf8f3] px-4 py-3 text-sm focus:border-[#ffb066] focus:outline-none"
            aria-label="E-Mail-Signatur"
          />
        </section>

        {/* Lizenz */}
        <section className="mt-6 rounded-2xl border border-[#eee7d8] bg-white p-6 shadow-[0_1px_3px_rgba(40,30,10,0.05)]">
          <h2 className="text-lg font-semibold">Abo und Lizenz</h2>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <span className="rounded-full bg-gradient-to-r from-[#ffb066] to-[#ff5f1f] px-4 py-1.5 text-sm font-bold text-white">
              Plan: {plan}
            </span>
            <Link
              href="/dashboard"
              className="rounded-xl border border-[#e0d8c6] px-4 py-2 text-sm font-medium text-[#6f6557] hover:border-[#ffb066] hover:text-[#c25e0e]"
            >
              Lizenzschlüssel im Dashboard aktivieren
            </Link>
          </div>
        </section>

        {/* Daten */}
        <section className="mt-6 rounded-2xl border border-[#eee7d8] bg-white p-6 shadow-[0_1px_3px_rgba(40,30,10,0.05)]">
          <h2 className="text-lg font-semibold">Ihre Daten</h2>
          <p className="mt-1 text-sm text-[#8d8172]">
            Alle Arbeitsdaten liegen in diesem Browser – nichts wird ohne Ihren
            Auftrag gespeichert oder weitergegeben. Datenschutzfreundlich ab Werk.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              onClick={exportieren}
              className="shop-btn rounded-xl bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-4 py-2.5 text-sm font-bold text-white"
            >
              Alles exportieren (JSON)
            </button>
            <button
              onClick={() => loeschen("acc-mission-history", "Missions-Verlauf")}
              className="rounded-xl border border-[#e0d8c6] px-4 py-2.5 text-sm text-[#6f6557] hover:border-red-300 hover:text-red-600"
            >
              Missions-Verlauf löschen
            </button>
            <button
              onClick={() => loeschen("acc-kommandos", "Befehls-Verlauf")}
              className="rounded-xl border border-[#e0d8c6] px-4 py-2.5 text-sm text-[#6f6557] hover:border-red-300 hover:text-red-600"
            >
              Befehls-Verlauf löschen
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
