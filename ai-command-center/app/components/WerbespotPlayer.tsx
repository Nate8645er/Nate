"use client";

/**
 * Werbespot-Player: spielt mehrere cinematische Szenen (Higgsfield-Clips)
 * nahtlos hintereinander ab und loopt danach. Ein einzelnes <video>-Element
 * wechselt bei `ended` zur nächsten Quelle – so wirkt es wie ein
 * durchgehender Spot, ohne die mp4s serverseitig zusammenschneiden zu müssen.
 *
 * Zugänglich: Szenen-Anzeige als Punkte (anklickbar), aktive Szene beschriftet,
 * Autoplay stummgeschaltet (Browser-Richtlinie), `prefers-reduced-motion`
 * respektiert (dann kein Autoplay, nur Steuerung).
 */

import { useEffect, useMemo, useRef, useState } from "react";

export interface WerbespotSzene {
  src: string;
  label: string;
}

export default function WerbespotPlayer({ szenen }: { szenen: WerbespotSzene[] }) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [aktiv, setAktiv] = useState(0);
  const reduziert = useMemo(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches ?? false;
  }, []);

  // Bei Szenenwechsel: Quelle laden und (falls Motion erlaubt) abspielen.
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    v.load();
    if (!reduziert) {
      // Autoplay kann abgelehnt werden – dann bleibt der Play-Button aktiv.
      void v.play().catch(() => {});
    }
  }, [aktiv, reduziert]);

  function naechste() {
    setAktiv((i) => (i + 1) % szenen.length);
  }

  const szene = szenen[aktiv];

  return (
    <div>
      <div className="relative overflow-hidden rounded-2xl border border-[#1c1917]/10 bg-[#0b0b0f] shadow-[0_30px_90px_-30px_rgba(28,25,23,0.6)]">
        <video
          ref={videoRef}
          controls
          autoPlay={!reduziert}
          muted
          playsInline
          preload="metadata"
          onEnded={naechste}
          className="w-full"
        >
          <source src={szene.src} type="video/mp4" />
          Ihr Browser kann dieses Video nicht abspielen.
        </video>
        {/* Szenen-Beschriftung */}
        <div className="pointer-events-none absolute left-4 top-4 rounded-full bg-black/45 px-3 py-1 text-xs font-semibold text-white backdrop-blur-sm">
          {aktiv + 1}/{szenen.length} · {szene.label}
        </div>
      </div>

      {/* Szenen-Punkte zum Springen */}
      <div className="mt-4 flex items-center justify-center gap-2" role="tablist" aria-label="Werbespot-Szenen">
        {szenen.map((s, i) => {
          const an = i === aktiv;
          return (
            <button
              key={s.src}
              type="button"
              role="tab"
              aria-selected={an}
              aria-label={`Szene ${i + 1}: ${s.label}`}
              onClick={() => setAktiv(i)}
              className={
                an
                  ? "h-2.5 w-8 rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] transition-all"
                  : "h-2.5 w-2.5 rounded-full bg-[#d9cfbd] transition-all hover:bg-[#ffb066]"
              }
            />
          );
        })}
      </div>
    </div>
  );
}
