"use client";

/**
 * Live-ROI-Rechner (einstimmige Team-Empfehlung): Branche + Teamgröße + Abo →
 * geschätzte Ersparnis pro Monat. Reiner Client, nutzt die getestete Logik aus
 * lib/roi.ts. Zahlen zählen sanft hoch (Micro-Interaction). Werte sind klar als
 * Schätzung gekennzeichnet – kein Versprechen.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { roiSchaetzung, BRANCHEN, TEAMGROESSEN, type BranchenId } from "@/lib/roi";

const PLAENE = ["PERSONAL", "STARTER", "PROFESSIONAL", "BUSINESS", "ENTERPRISE"] as const;

/** Sanft hochzählender Wert (200–600ms), respektiert prefers-reduced-motion. */
function useCountUp(ziel: number, dauer = 600): number {
  const [wert, setWert] = useState(ziel);
  const vonRef = useRef(ziel);
  const rafRef = useRef<number | null>(null);
  const startRef = useRef(0);
  useEffect(() => {
    const reduce = typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) { setWert(ziel); vonRef.current = ziel; return; }
    const von = vonRef.current;
    startRef.current = 0;
    const tick = (ts: number) => {
      if (!startRef.current) startRef.current = ts;
      const p = Math.min(1, (ts - startRef.current) / dauer);
      const eased = 1 - Math.pow(1 - p, 3);
      setWert(Math.round(von + (ziel - von) * eased));
      if (p < 1) rafRef.current = requestAnimationFrame(tick);
      else vonRef.current = ziel;
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [ziel, dauer]);
  return wert;
}

const nf = new Intl.NumberFormat("de-CH");

export default function RoiRechner({ variant = "hell" }: { variant?: "hell" | "shop" }) {
  const [branche, setBranche] = useState<BranchenId>("marketing");
  const [teamgroesse, setTeamgroesse] = useState("klein");
  const [plan, setPlan] = useState<string>("PROFESSIONAL");

  const ergebnis = useMemo(() => roiSchaetzung({ branche, teamgroesse, plan }), [branche, teamgroesse, plan]);
  const chf = useCountUp(ergebnis.chfProMonat);
  const stunden = useCountUp(ergebnis.stundenProMonat);
  const aufgaben = useCountUp(ergebnis.aufgabenProMonat);

  const feld =
    "w-full rounded-xl border border-[#e0d8c6] bg-white px-3 py-2.5 text-sm text-[#1c1917] outline-none transition focus:border-[#ffb066] focus:ring-2 focus:ring-[#ffb066]/30";
  const label = "text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]";

  return (
    <div className="acc-card rounded-2xl p-5 sm:p-6">
      <div className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Live-Rechner</div>
      <h3 className="mt-1 text-xl font-semibold text-[#1c1917] sm:text-2xl">
        Was spart Ihnen Ihre <span className="acc-grad-text">KI-Abteilung</span>?
      </h3>
      <p className="mt-1 text-sm text-[#6f6557]">In 5 Sekunden – ehrliche, konservative Schätzung.</p>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div>
          <label className={label} htmlFor="roi-branche">Branche</label>
          <select id="roi-branche" className={`mt-1 ${feld}`} value={branche} onChange={(e) => setBranche(e.target.value as BranchenId)}>
            {BRANCHEN.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        </div>
        <div>
          <label className={label} htmlFor="roi-team">Teamgröße</label>
          <select id="roi-team" className={`mt-1 ${feld}`} value={teamgroesse} onChange={(e) => setTeamgroesse(e.target.value)}>
            {TEAMGROESSEN.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
        </div>
        <div>
          <label className={label} htmlFor="roi-plan">Abo</label>
          <select id="roi-plan" className={`mt-1 ${feld}`} value={plan} onChange={(e) => setPlan(e.target.value)}>
            {PLAENE.map((p) => <option key={p} value={p}>{p.charAt(0) + p.slice(1).toLowerCase()}</option>)}
          </select>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-3 text-center">
        <div className="rounded-2xl border border-[#bfe6cf] bg-[#f0faf4] p-4">
          <p className="text-2xl font-bold text-[#177245] sm:text-3xl">CHF {nf.format(chf)}</p>
          <p className="mt-1 text-[11px] font-semibold text-[#6f6557]">Ersparnis / Monat</p>
        </div>
        <div className="rounded-2xl border border-[#ffe0b8] bg-[#fff7ed] p-4">
          <p className="text-2xl font-bold text-[#c25e0e] sm:text-3xl">{nf.format(stunden)} h</p>
          <p className="mt-1 text-[11px] font-semibold text-[#6f6557]">Zeit / Monat</p>
        </div>
        <div className="rounded-2xl border border-[#d7d4f5] bg-[#eef0ff] p-4">
          <p className="text-2xl font-bold text-[#5b52d6] sm:text-3xl">{nf.format(aufgaben)}</p>
          <p className="mt-1 text-[11px] font-semibold text-[#6f6557]">Aufgaben / Monat</p>
        </div>
      </div>

      <p className="mt-3 text-[11px] leading-relaxed text-[#8a8172]">{ergebnis.annahmen}</p>
    </div>
  );
}
