"use client";

/**
 * AgentOffice – das animierte Büro Ihrer KI-Belegschaft.
 *
 * Statt statischer Status-Karten: eine kleine Firma. Jeder Agent hat
 * einen Schreibtisch mit Monitor. Wer arbeitet, sitzt am Platz und
 * tippt (Monitor flackert); wer bereit ist, läuft durchs Büro; wer
 * fertig ist, zeigt eine grüne Sprechblase. Gesperrte Plätze (höhere
 * Abo-Stufe) sind abgedunkelt.
 *
 * Reine CSS-Animationen (transform/opacity, s. globals.css) – kein
 * Canvas, kein Timer, respektiert prefers-reduced-motion.
 */

import { memo } from "react";

export type OfficeStatus = "idle" | "working" | "done" | "error";

export interface OfficeAgent {
  id: string;
  name: string;
  status: OfficeStatus;
  locked?: boolean;
}

/** Schreibtisch-Plätze (Prozent-Koordinaten) für bis zu 8 Agenten. */
const PLAETZE: { x: number; y: number }[] = [
  { x: 14, y: 38 },
  { x: 38, y: 34 },
  { x: 62, y: 34 },
  { x: 86, y: 38 },
  { x: 14, y: 82 },
  { x: 38, y: 86 },
  { x: 62, y: 86 },
  { x: 86, y: 82 },
];

/** Figuren-Farben je Platz: grüne KI-Roboter (Meta-Grün-Familie) mit
 *  leichter Ton-Variation, dazu ein Mint-Leuchtakzent für die Antenne. */
const FARBEN: [string, string, string][] = [
  ["#22c55e", "#15a34a", "#86efac"],
  ["#34d399", "#059669", "#a7f3d0"],
  ["#4ade80", "#16a34a", "#bbf7d0"],
  ["#2dd4bf", "#0d9488", "#99f6e4"],
  ["#10b981", "#047857", "#6ee7b7"],
  ["#84cc16", "#4d7c0f", "#d9f99d"],
  ["#14b8a6", "#0f766e", "#5eead4"],
  ["#22c55e", "#166534", "#86efac"],
];

const ROUTEN = ["route-a", "route-b", "route-c", "route-d"] as const;

export default memo(function AgentOffice({ agents }: { agents: OfficeAgent[] }) {
  return (
    <div className="office" role="img" aria-label="Ihre KI-Belegschaft bei der Arbeit im virtuellen Büro">
      {agents.slice(0, 8).map((a, i) => {
        const platz = PLAETZE[i];
        const [c1, c2, mint] = FARBEN[i % FARBEN.length];
        const deskCls =
          a.locked ? "is-locked" : a.status === "working" ? "is-working" : a.status === "done" ? "is-done" : a.status === "error" ? "is-error" : "";
        // Bereit => durchs Büro laufen; sonst am Platz sitzen und tippen.
        const laeuft = !a.locked && a.status === "idle";
        const botCls = a.locked
          ? "is-sitzend"
          : laeuft
            ? `is-laufen ${ROUTEN[i % ROUTEN.length]}`
            : "is-sitzend";
        return (
          <div key={a.id}>
            <div className={`office-desk ${deskCls}`} style={{ left: `${platz.x}%`, top: `${platz.y}%` }}>
              <div className="desk-screen"><span className="desk-glow" /><span className="desk-scan" /></div>
              <div className="desk-kbd" />
              <div className="desk-top" />
              <div className="desk-name">{a.locked ? `🔒 ${a.name}` : a.name}</div>
            </div>
            {!a.locked && (
              <div
                className={`office-bot ${botCls}`}
                style={
                  {
                    left: `${platz.x}%`,
                    top: `${platz.y + (laeuft ? 14 : 6)}%`,
                    "--bot-farbe": c1,
                    "--bot-farbe-2": c2,
                    "--bot-mint": mint,
                    animationDelay: laeuft ? `${(i % 4) * -3.5}s` : undefined,
                  } as React.CSSProperties
                }
              >
                {a.status === "done" && <span className="bot-bubble">✓</span>}
                {a.status === "error" && <span className="bot-bubble is-fehler">!</span>}
                <div className="bot-inner">
                  <span className="bot-arm bot-arm--l" />
                  <span className="bot-arm bot-arm--r" />
                  <div className="bot-head"><i className="bot-eye" /></div>
                  <div className="bot-body" />
                  <div className="bot-legs"><span /><span /></div>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
});
