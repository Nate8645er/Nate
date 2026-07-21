"use client";

/**
 * AgentWorld – die animierte KI-Welt Ihrer Belegschaft.
 *
 * Statt statischer Karten: eine bunte kleine Stadt. Jeder Agent hat ein
 * eigenes, farbiges Gebäude mit Neon-Schild (CODING, MARKETING, ANALYSE …).
 * Wer arbeitet, dessen Fenster leuchten und blinken. Dazwischen laufen
 * bunte Roboter-Figuren durch die Welt – hin und her, in vielen Farben.
 *
 * Reine CSS-Animationen (transform/opacity, s. globals.css) – kein Canvas,
 * respektiert prefers-reduced-motion. Deterministisch (kein Math.random),
 * damit Server- und Client-Render identisch sind.
 */

import { memo } from "react";

export type WorldStatus = "idle" | "working" | "done" | "error";

export interface WorldAgent {
  id: string;
  name: string;
  status: WorldStatus;
  locked?: boolean;
}

/** Gebäude-Beschriftung + Farbe je Rolle. */
const GEBAEUDE: Record<string, { label: string; color: string; h: number }> = {
  commander: { label: "HAUPTQUARTIER", color: "#ff8c2a", h: 210 },
  builder: { label: "WERKSTATT", color: "#3b82f6", h: 165 },
  analyst: { label: "ANALYSE", color: "#06b6d4", h: 190 },
  quality: { label: "QUALITÄT", color: "#eab308", h: 150 },
  marketing: { label: "MARKETING", color: "#ec4899", h: 185 },
  research: { label: "RESEARCH", color: "#8b5cf6", h: 200 },
  coding: { label: "CODING", color: "#22c55e", h: 170 },
  business: { label: "FINANZEN", color: "#14b8a6", h: 160 },
};
const FALLBACK = { label: "TEAM", color: "#a78bfa", h: 175 };

/** Bunte Figuren-Farben (laufen durch die Welt). */
const BOT_FARBEN = [
  "#ff8c2a", "#3b82f6", "#22c55e", "#ec4899", "#8b5cf6",
  "#06b6d4", "#eab308", "#14b8a6", "#f43f5e", "#a3e635",
  "#fb923c", "#38bdf8",
];

/** Fenster-Gitter für ein Gebäude (Zeilen × Spalten je nach Höhe). */
function fenster(h: number): number {
  const rows = Math.max(3, Math.round((h - 30) / 18));
  return rows * 3; // 3 Spalten
}

export default memo(function AgentWorld({ agents }: { agents: WorldAgent[] }) {
  const liste = agents.slice(0, 8);
  const n = liste.length;

  // 14 Figuren laufen durch die Welt – deterministisch verteilt.
  const bots = Array.from({ length: 14 }, (_, i) => {
    const nachRechts = i % 2 === 0;
    const lane = 4 + ((i * 37) % 60); // Höhe auf der Strasse (px vom Boden)
    const dauer = 8 + ((i * 5) % 9); // 8–16 s
    const delay = -((i * 13) % 16); // gestaffelter Start
    const scale = 0.7 + ((i * 17) % 45) / 100; // 0.7–1.15 (Tiefe)
    const farbe = BOT_FARBEN[i % BOT_FARBEN.length];
    return { i, nachRechts, lane, dauer, delay, scale, farbe };
  });

  return (
    <div className="world" role="img" aria-label="Ihre KI-Belegschaft als animierte Stadt – Figuren laufen zwischen den Abteilungsgebäuden">
      {/* Gebäude */}
      <div className="world-city">
        {liste.map((a, i) => {
          const g = GEBAEUDE[a.id] ?? FALLBACK;
          const left = n > 0 ? 3 + (i * 94) / n : 0;
          const width = n > 0 ? Math.min(11, 82 / n) : 10;
          const cls = a.locked
            ? "is-locked"
            : a.status === "working"
              ? "is-working"
              : a.status === "done"
                ? "is-done"
                : "";
          const winCount = fenster(g.h);
          return (
            <div
              key={a.id}
              className={`world-building ${cls}`}
              style={
                {
                  left: `${left}%`,
                  width: `${width}%`,
                  height: `${g.h}px`,
                  "--c": g.color,
                } as React.CSSProperties
              }
            >
              <span className="sign">{g.label}</span>
              <div className="win" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
                {Array.from({ length: winCount }, (_, w) => (
                  <i key={w} />
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Laufende Figuren */}
      {bots.map((b) => (
        <div
          key={b.i}
          className={`world-bot ${b.nachRechts ? "dir-r" : "dir-l"}`}
          style={
            {
              bottom: `${b.lane}px`,
              transform: `scale(${b.scale})${b.nachRechts ? "" : " scaleX(-1)"}`,
              animation: `${b.nachRechts ? "world-walk-r" : "world-walk-l"} ${b.dauer}s linear ${b.delay}s infinite`,
              "--c": b.farbe,
            } as React.CSSProperties
          }
        >
          <div className="wb-inner">
            <div className="wb-head" />
            <div className="wb-body" />
            <div className="wb-legs"><i /><i /></div>
          </div>
        </div>
      ))}
    </div>
  );
});
