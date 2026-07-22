"use client";

/**
 * Benutzerverwaltung – Team-Mitglieder mit Rollen.
 *
 * Verwaltet das Team des Arbeitsbereichs lokal (acc-benutzer): Name,
 * E-Mail, Rolle (Admin / Manager / Mitarbeiter) mit klar beschriebenen
 * Rechten. Ehrlich ausgewiesen: zentrales Login mit SSO/2FA über alle
 * Geräte hinweg ist Teil der Enterprise-Einrichtung pro Kunde.
 */

import { useCallback, useEffect, useState } from "react";
import WorkNav from "@/app/components/WorkNav";
import WorkFooter from "@/app/components/WorkFooter";

const BENUTZER_KEY = "acc-benutzer";

type Rolle = "Admin" | "Manager" | "Mitarbeiter";

interface Benutzer {
  id: string;
  name: string;
  email: string;
  rolle: Rolle;
}

const ROLLEN: { rolle: Rolle; rechte: string }[] = [
  { rolle: "Admin", rechte: "Alles: Lizenz, Benutzer, Einstellungen, alle Bereiche" },
  { rolle: "Manager", rechte: "Befehle, Autopilot, Berichte und Analysen" },
  { rolle: "Mitarbeiter", rechte: "Befehle ausführen und eigene Berichte sehen" },
];

export default function BenutzerPage() {
  const [benutzer, setBenutzer] = useState<Benutzer[]>([]);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [rolle, setRolle] = useState<Rolle>("Mitarbeiter");

  useEffect(() => {
    try {
      const raw = localStorage.getItem(BENUTZER_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Benutzer[];
        if (Array.isArray(parsed)) setBenutzer(parsed);
      }
    } catch {
      /* Storage nicht lesbar */
    }
  }, []);

  const persist = useCallback((next: Benutzer[]) => {
    setBenutzer(next);
    try {
      localStorage.setItem(BENUTZER_KEY, JSON.stringify(next));
    } catch {
      /* voll */
    }
  }, []);

  const hinzufuegen = () => {
    const n = name.trim().slice(0, 60);
    const e = email.trim().slice(0, 120);
    if (!n) return;
    persist([...benutzer, { id: `u${Date.now().toString(36)}`, name: n, email: e, rolle }]);
    setName("");
    setEmail("");
    setRolle("Mitarbeiter");
  };

  return (
    <div className="acc-page min-h-dvh text-[#1c1917]">
      <div className="mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#e8e1d2] py-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <WorkNav aktiv="benutzer" variante="hell" />
        </header>

        <div className="pt-10">
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Benutzerverwaltung</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">Ihr Team und seine Rollen</h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#8d8172]">
            Legen Sie fest, wer in Ihrem Unternehmen mit der KI-Belegschaft
            arbeitet und mit welcher Rolle. Der Lizenzschlüssel gilt für Ihr
            ganzes Team (je nach Abo-Stufe).
          </p>
          <p className="mt-3 max-w-2xl rounded-xl border border-[#f0ceA0] bg-[#fff4e6] px-4 py-3 text-xs leading-relaxed text-[#8a4a12]">
            Transparenz: Diese Verwaltung gilt für diesen Arbeitsbereich.
            Zentrales Firmen-Login mit SSO, 2FA und geräteübergreifenden
            Rollen richten wir als Enterprise-Projekt pro Kunde ein.
          </p>
        </div>

        {/* Rollen-Erklärung */}
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {ROLLEN.map((r) => (
            <div key={r.rolle} className="rounded-2xl acc-card p-5">
              <p className="font-bold text-[#c25e0e]">{r.rolle}</p>
              <p className="mt-1.5 text-sm leading-relaxed text-[#6f6557]">{r.rechte}</p>
            </div>
          ))}
        </div>

        {/* Hinzufügen */}
        <form
          className="mt-8 grid gap-3 rounded-2xl acc-card p-5 sm:grid-cols-[1fr_1fr_160px_auto]"
          onSubmit={(e) => {
            e.preventDefault();
            hinzufuegen();
          }}
        >
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Name"
            className="rounded-xl border border-[#e0d8c6] bg-[#faf8f3] px-4 py-2.5 text-sm focus:border-[#ffb066] focus:outline-none"
            aria-label="Name"
          />
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            placeholder="E-Mail (optional)"
            className="rounded-xl border border-[#e0d8c6] bg-[#faf8f3] px-4 py-2.5 text-sm focus:border-[#ffb066] focus:outline-none"
            aria-label="E-Mail"
          />
          <select
            value={rolle}
            onChange={(e) => setRolle(e.target.value as Rolle)}
            className="rounded-xl border border-[#e0d8c6] bg-[#faf8f3] px-3 py-2.5 text-sm focus:border-[#ffb066] focus:outline-none"
            aria-label="Rolle"
          >
            {ROLLEN.map((r) => (
              <option key={r.rolle}>{r.rolle}</option>
            ))}
          </select>
          <button
            type="submit"
            disabled={!name.trim()}
            className="shop-btn rounded-xl bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-5 py-2.5 text-sm font-bold text-white disabled:opacity-40"
          >
            Hinzufügen
          </button>
        </form>

        {/* Liste */}
        <div className="mt-6 overflow-hidden rounded-2xl acc-card">
          {benutzer.length === 0 && (
            <p className="px-5 py-8 text-center text-sm text-[#8d8172]">
              Noch keine Team-Mitglieder erfasst.
            </p>
          )}
          {benutzer.map((b, i) => (
            <div
              key={b.id}
              className={`flex flex-wrap items-center gap-3 px-5 py-3.5 ${i > 0 ? "border-t border-[#f0ebe0]" : ""}`}
            >
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f] text-sm font-bold text-white">
                {b.name.slice(0, 1).toUpperCase()}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold">{b.name}</p>
                {b.email && <p className="truncate text-xs text-[#a2988a]">{b.email}</p>}
              </div>
              <select
                value={b.rolle}
                onChange={(e) =>
                  persist(benutzer.map((x) => (x.id === b.id ? { ...x, rolle: e.target.value as Rolle } : x)))
                }
                className="rounded-lg border border-[#e0d8c6] bg-[#faf8f3] px-2.5 py-1.5 text-xs focus:outline-none"
                aria-label={`Rolle von ${b.name}`}
              >
                {ROLLEN.map((r) => (
                  <option key={r.rolle}>{r.rolle}</option>
                ))}
              </select>
              <button
                onClick={() => persist(benutzer.filter((x) => x.id !== b.id))}
                className="rounded-lg border border-[#e0d8c6] px-2.5 py-1.5 text-xs text-[#a2988a] hover:border-red-300 hover:text-red-600"
                aria-label={`${b.name} entfernen`}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
        <WorkFooter variante="hell" />
      </div>
    </div>
  );
}
