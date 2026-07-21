"use client";

/**
 * AgentWorld – die animierte KI-Stadt aus der Vogelperspektive.
 *
 * Draufsicht auf eine kleine Stadt bei Nacht im Weltraum (funkelnde
 * Sterne). Jede Abteilung ist ein Gebäude mit Dach-Schild (CODING,
 * MARKETING, ANALYSE …); arbeitende Gebäude haben leuchtende Oberlichter.
 * Bunte Figuren laufen über die Strassen. Wer nichts zu tun hat, fragt
 * mit "?" nach einer Aufgabe – oder sitzt im Café (trinkt) bzw. im
 * Restaurant (isst). Drei Live-Monitore zeigen, woran gerade gearbeitet
 * wird: eine Website, Code und die E-Mail-App scrollen durch.
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

/** Gebäude in Draufsicht: Beschriftung, Farbe, Position/Grösse (%).
 *  Obere zwei Reihen = Abteilungen; unten bleibt Platz für Café & Bistro,
 *  rechts der Streifen für die Live-Monitore (x < 84). */
const GEBAEUDE: Record<string, { label: string; color: string; x: number; y: number; w: number; h: number }> = {
  commander: { label: "HAUPTQUARTIER", color: "#ff8c2a", x: 3, y: 7, w: 20, h: 24 },
  builder: { label: "WERKSTATT", color: "#3b82f6", x: 27, y: 7, w: 16, h: 20 },
  analyst: { label: "ANALYSE", color: "#06b6d4", x: 47, y: 7, w: 16, h: 20 },
  research: { label: "RESEARCH", color: "#8b5cf6", x: 66, y: 7, w: 16, h: 22 },
  quality: { label: "QUALITÄT", color: "#eab308", x: 3, y: 36, w: 15, h: 16 },
  coding: { label: "CODING", color: "#22c55e", x: 22, y: 34, w: 17, h: 18 },
  marketing: { label: "MARKETING", color: "#ec4899", x: 45, y: 34, w: 17, h: 18 },
  business: { label: "FINANZEN", color: "#14b8a6", x: 66, y: 36, w: 16, h: 16 },
};
const FALLBACK = { label: "TEAM", color: "#a78bfa", x: 45, y: 12, w: 14, h: 16 };

const BOT_FARBEN = [
  "#ff8c2a", "#3b82f6", "#22c55e", "#ec4899", "#8b5cf6",
  "#06b6d4", "#eab308", "#14b8a6", "#f43f5e", "#a3e635",
  "#fb923c", "#38bdf8",
];
const ROUTEN = ["r1", "r2", "r3", "r4"];

function Fig({ color, extra, style, children }: { color: string; extra?: string; style?: React.CSSProperties; children?: React.ReactNode }) {
  return (
    <div className={`world-fig ${extra ?? ""}`} style={{ ["--c" as string]: color, ...style } as React.CSSProperties}>
      {children}
      <div className="f-body" />
    </div>
  );
}

export default memo(function AgentWorld({ agents }: { agents: WorldAgent[] }) {
  const liste = agents.slice(0, 8);

  // Laufende Figuren (deterministisch verteilt).
  const laeufer = Array.from({ length: 9 }, (_, i) => ({
    i,
    route: ROUTEN[i % ROUTEN.length],
    delay: -((i * 17) % 20),
    farbe: BOT_FARBEN[i % BOT_FARBEN.length],
  }));

  // Café-/Restaurant-Gäste (Position in % INNERHALB des jeweiligen Spots).
  const cafeGaeste = [
    { x: 6, y: 24, c: "#fb923c" }, { x: 30, y: 20, c: "#38bdf8" },
    { x: 6, y: 66, c: "#a3e635" }, { x: 30, y: 70, c: "#f43f5e" },
  ];
  const restGaeste = [
    { x: 8, y: 26, c: "#8b5cf6" }, { x: 34, y: 22, c: "#22c55e" },
    { x: 8, y: 68, c: "#eab308" }, { x: 34, y: 72, c: "#ec4899" },
    { x: 60, y: 46, c: "#38bdf8" },
  ];

  return (
    <div className="world" role="img" aria-label="Ihre KI-Stadt aus der Vogelperspektive: Gebäude je Abteilung, Figuren laufen umher, sitzen im Café und Restaurant oder fragen nach Aufgaben; Live-Monitore zeigen die Arbeit">
      <div className="world-ground">
        {/* Strassen (Draufsicht) */}
        <div className="world-road h" style={{ top: "30%" }} />
        <div className="world-road h" style={{ top: "58%" }} />
        <div className="world-road v" style={{ left: "42%" }} />
        <div className="world-road v" style={{ left: "84%" }} />

        {/* Gebäude */}
        {liste.map((a) => {
          const g = GEBAEUDE[a.id] ?? FALLBACK;
          const cls = a.locked ? "is-locked" : a.status === "working" ? "is-working" : a.status === "done" ? "is-done" : "";
          const winCount = Math.max(6, Math.round((g.w * g.h) / 40));
          return (
            <div
              key={a.id}
              className={`world-bld ${cls}`}
              style={{ left: `${g.x}%`, top: `${g.y}%`, width: `${g.w}%`, height: `${g.h}%`, ["--c" as string]: g.color } as React.CSSProperties}
            >
              <span className="tag">{a.locked ? `🔒 ${g.label}` : g.label}</span>
              <div className="roof">
                {Array.from({ length: winCount }, (_, w) => <i key={w} />)}
              </div>
            </div>
          );
        })}

        {/* Café (Gäste trinken) – unten links */}
        <div className="world-spot cafe" style={{ left: "3%", top: "64%", width: "34%", height: "33%" }}>
          <span className="tag">☕ CAFÉ</span>
          <div className="world-table" style={{ left: "16%", top: "28%" }}><span className="cup" /></div>
          <div className="world-table" style={{ left: "16%", top: "64%" }}><span className="cup" /></div>
          {cafeGaeste.map((s, i) => (
            <Fig key={i} color={s.c} style={{ left: `${s.x}%`, top: `${s.y}%`, position: "absolute" }} />
          ))}
        </div>

        {/* Restaurant (Gäste essen) – unten mitte */}
        <div className="world-spot rest" style={{ left: "42%", top: "64%", width: "38%", height: "33%" }}>
          <span className="tag">🍽 BISTRO</span>
          <div className="world-table" style={{ left: "16%", top: "26%" }}><span className="cup" /></div>
          <div className="world-table" style={{ left: "16%", top: "66%" }}><span className="cup" /></div>
          <div className="world-table" style={{ left: "52%", top: "44%" }}><span className="cup" /></div>
          {restGaeste.map((s, i) => (
            <Fig key={i} color={s.c} style={{ left: `${s.x}%`, top: `${s.y}%`, position: "absolute" }} />
          ))}
        </div>

        {/* Fragende Figuren (warten auf Aufgabe) vor dem Hauptquartier */}
        <Fig color="#ff8c2a" extra="ask" style={{ left: "26%", top: "18%" }}>
          <span className="ask-bubble">?</span>
        </Fig>
        <Fig color="#38bdf8" extra="ask" style={{ left: "24%", top: "24%" }}>
          <span className="ask-bubble">?</span>
        </Fig>

        {/* Laufende Figuren */}
        {laeufer.map((b) => (
          <Fig
            key={b.i}
            color={b.farbe}
            extra={`walk ${b.route}`}
            style={{ animationDelay: `${b.delay}s` }}
          />
        ))}
      </div>

      {/* Live-Monitore: woran gerade gearbeitet wird */}
      <div className="world-mon browser" style={{ right: "6%", top: "12%" }}>
        <div className="m-bar"><b style={{ background: "#f87171" }} /><b style={{ background: "#fbbf24" }} /><b style={{ background: "#34d399" }} /><span className="t">katzenufos.com</span></div>
        <div className="m-view"><div className="m-scroll">{Array.from({ length: 16 }, (_, i) => <span key={i} />)}</div></div>
      </div>
      <div className="world-mon code" style={{ right: "6%", top: "44%" }}>
        <div className="m-bar"><b style={{ background: "#22c55e" }} /><span className="t">mission.ts</span></div>
        <div className="m-view"><div className="m-scroll">{Array.from({ length: 16 }, (_, i) => <span key={i} />)}</div></div>
      </div>
      <div className="world-mon mail" style={{ right: "6%", top: "76%" }}>
        <div className="m-bar"><b style={{ background: "#a78bfa" }} /><span className="t">E-Mail</span></div>
        <div className="m-view"><div className="m-scroll">{Array.from({ length: 16 }, (_, i) => <span key={i} />)}</div></div>
      </div>
    </div>
  );
});
