"use client";

/**
 * Premium-Politur (Team-Idee): zählt eine Kennzahl beim Sichtbarwerden sanft
 * hoch. Reine Zusatz-Animation – der Endwert entspricht exakt der Vorgabe, es
 * wird nichts erfunden. Respektiert prefers-reduced-motion (dann sofort fertig).
 *
 * `text` darf einen führenden Ganzzahl-Anteil haben (z. B. "1000", "24/7",
 * "100"); nur dieser Zahlteil wird animiert, der Rest bleibt unverändert.
 */

import { useEffect, useRef, useState } from "react";

const nf = new Intl.NumberFormat("de-CH");

function zerlege(text: string): { ziel: number; suffix: string } | null {
  const m = /^(\d[\d'.,]*)(.*)$/.exec(text.trim());
  if (!m) return null;
  const ziel = parseInt(m[1].replace(/[^\d]/g, ""), 10);
  if (!Number.isFinite(ziel)) return null;
  return { ziel, suffix: m[2] };
}

export default function StatZahl({ text, dauer = 1100 }: { text: string; dauer?: number }) {
  const teile = zerlege(text);
  const [wert, setWert] = useState(teile ? 0 : NaN);
  const ref = useRef<HTMLSpanElement | null>(null);
  const gestartet = useRef(false);

  useEffect(() => {
    if (!teile) return;
    const el = ref.current;
    if (!el) return;
    const reduce = typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) { setWert(teile.ziel); return; }

    const starte = () => {
      if (gestartet.current) return;
      gestartet.current = true;
      const t0 = performance.now();
      const tick = (t: number) => {
        const p = Math.min(1, (t - t0) / dauer);
        const eased = 1 - Math.pow(1 - p, 3);
        setWert(Math.round(teile.ziel * eased));
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    };

    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => { if (e.isIntersecting) { starte(); io.disconnect(); } }),
      { threshold: 0.4 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [teile, dauer]);

  if (!teile) return <span ref={ref}>{text}</span>;
  return <span ref={ref}>{nf.format(Number.isNaN(wert) ? teile.ziel : wert)}{teile.suffix}</span>;
}
