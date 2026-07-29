"use client";

/**
 * AgentWorld – das animierte KI-Büro aus der Vogelperspektive (dunkel).
 *
 * Draufsicht auf ein dunkles Grossraumbüro, abgestimmt aufs schwarze
 * Dashboard: acht Abteilungs-Arbeitsplätze mit leuchtenden Monitoren und
 * tippenden Mitarbeitern (arbeitende Plätze leuchten stärker, gesperrte
 * sind gedimmt), Figuren laufen durch den Gang, ein Drucker gibt laufend
 * Ergebnisse aus, dazu Meeting-Ecke und Live-Monitore.
 *
 * Reine CSS-Animationen (transform/opacity), deterministisch (kein
 * Math.random → kein Hydration-Mismatch), prefers-reduced-motion beachtet.
 */

import { memo } from "react";

export type WorldStatus = "idle" | "working" | "done" | "error";

export interface WorldAgent {
  id: string;
  name: string;
  status: WorldStatus;
  locked?: boolean;
}

/** Abteilungsfarbe je Rolle (Akzent des Arbeitsplatzes). */
const ROLLE_FARBE: Record<string, string> = {
  commander: "#ff8c2a",
  builder: "#3b82f6",
  analyst: "#06b6d4",
  research: "#8b5cf6",
  quality: "#eab308",
  coding: "#22c55e",
  marketing: "#ec4899",
  business: "#14b8a6",
};
const MONITOR_ART: Record<string, "code" | "mail" | "doc"> = {
  commander: "doc", builder: "code", analyst: "code", research: "doc",
  quality: "doc", coding: "code", marketing: "mail", business: "mail",
};
// Laufende Figuren (ohne Blau – der Blaue sitzt jetzt am Platz und arbeitet).
const WALK_FARBEN = ["#ff8c2a", "#22c55e", "#a78bfa", "#ec4899", "#14b8a6", "#eab308"];

export default memo(function AgentWorld({
  agents,
  firma,
}: {
  agents: WorldAgent[];
  /** Name der verbundenen Firma – erscheint im Häuser-Bezirk, sobald gesetzt. */
  firma?: string;
}) {
  const liste = agents.slice(0, 8);

  return (
    <div
      className="aw"
      role="img"
      aria-label={`Ihr KI-Büro aus der Vogelperspektive: acht Abteilungen mit Mitarbeitern am Rechner; arbeitende Plätze leuchten. Figuren laufen auf verschiedenen Wegen umher, ein Drucker gibt Ergebnisse aus. Daneben kleine Häuser für ${firma ? `die verbundene Firma ${firma}` : "Ihre Firma"}.`}
    >
      <div className="aw-floor">
        {/* Gang-Linien */}
        <div className="aw-aisle h" style={{ top: "30.5%" }} />
        <div className="aw-aisle h" style={{ top: "60%" }} />

        {/* Arbeitsplätze (2 Reihen à 4) */}
        {liste.map((a, i) => {
          const col = (i % 4) * 20 + 3;
          const row = i < 4 ? 5 : 33;
          const c = ROLLE_FARBE[a.id] ?? "#a78bfa";
          const art = MONITOR_ART[a.id] ?? "doc";
          const zustand = a.locked ? "is-locked" : a.status === "working" ? "is-working" : a.status === "done" ? "is-done" : a.status === "error" ? "is-error" : "";
          return (
            <div
              key={a.id}
              className={`aw-ws ${zustand}`}
              style={{ left: `${col}%`, top: `${row}%`, ["--c" as string]: c } as React.CSSProperties}
            >
              <span className="aw-tag">{a.locked ? `🔒 ${a.name}` : a.name}</span>
              <div className="aw-desk">
                <div className={`aw-mon aw-mon--${art}`}>
                  <div className="aw-scroll">{Array.from({ length: 12 }, (_, k) => <span key={k} />)}</div>
                </div>
                <div className="aw-kbd" />
              </div>
              <div className="aw-worker">
                <span className="aw-arm l" />
                <span className="aw-arm r" />
                <span className="aw-head" />
              </div>
            </div>
          );
        })}

        {/* Laufende Figuren im Gang */}
        {WALK_FARBEN.map((c, i) => (
          <div key={i} className={`aw-walk g${i + 1}`} style={{ ["--c" as string]: c } as React.CSSProperties}>
            <span className="aw-wh" /><span className="aw-wb" />
          </div>
        ))}

        {/* Meeting-Ecke unten links */}
        <div className="aw-meet">
          <span className="aw-mlabel">MEETING</span>
          <div className="aw-table" />
          <div className="aw-mfig" style={{ ["--c" as string]: "#3b82f6", left: "50%", top: "-4px" } as React.CSSProperties} />
          <div className="aw-mfig" style={{ ["--c" as string]: "#ec4899", left: "-4px", top: "50%" } as React.CSSProperties} />
          <div className="aw-mfig" style={{ ["--c" as string]: "#14b8a6", right: "-4px", top: "50%" } as React.CSSProperties} />
          <div className="aw-mfig" style={{ ["--c" as string]: "#eab308", left: "50%", bottom: "-4px" } as React.CSSProperties} />
        </div>

        {/* Drucker unten rechts: gibt laufend Ergebnisse aus */}
        <div className="aw-printer">
          <span className="aw-plabel">DRUCKER</span>
          <div className="aw-pbody"><span className="aw-led" /><div className="aw-slot" /><div className="aw-sheet"><i /><i /><i /></div></div>
          <div className="aw-tray"><span className="aw-stack s1" /><span className="aw-stack s2" /><span className="aw-stack s3" /></div>
        </div>

        {/* Verbundene-Firma-Bezirk: kleine Häuser + Firmenname (erscheint bei Verbindung) */}
        <div className="aw-district">
          <span className="aw-dlabel">VERBUNDENE FIRMA</span>
          <div className="aw-houses">
            <div className="aw-house" style={{ ["--c" as string]: "#3b82f6" } as React.CSSProperties} />
            <div className="aw-house" style={{ ["--c" as string]: "#22c55e" } as React.CSSProperties} />
            <div className="aw-house" style={{ ["--c" as string]: "#ec4899" } as React.CSSProperties} />
          </div>
          <div className={`aw-firma ${firma ? "" : "is-leer"}`}>
            <span className="k">{firma ? "Verbunden" : "Noch nicht verbunden"}</span>
            <span className="n">{firma || "Ihre Firma"}</span>
          </div>
        </div>
      </div>

      {/* Live-Monitore: woran gerade gearbeitet wird */}
      <div className="aw-live browser"><div className="aw-lbar"><b style={{ background: "#f87171" }} /><b style={{ background: "#fbbf24" }} /><b style={{ background: "#34d399" }} /><span>ihre-firma.ch</span></div><div className="aw-lview"><div className="aw-lscroll">{Array.from({ length: 14 }, (_, i) => <span key={i} />)}</div></div></div>
      <div className="aw-live code"><div className="aw-lbar"><b style={{ background: "#22c55e" }} /><span>mission.ts</span></div><div className="aw-lview"><div className="aw-lscroll">{Array.from({ length: 14 }, (_, i) => <span key={i} />)}</div></div></div>
      <div className="aw-live mail"><div className="aw-lbar"><b style={{ background: "#a78bfa" }} /><span>E-Mail</span></div><div className="aw-lview"><div className="aw-lscroll">{Array.from({ length: 14 }, (_, i) => <span key={i} />)}</div></div></div>
    </div>
  );
});
