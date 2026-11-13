import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import { PixelRobot, type RobotState } from "./PixelRobot";
import type { Prices, Station } from "../lib/types";

const COLS = [110, 290, 470, 650, 830];
const ROWS = [180, 320, 460];
const TABLE = { x: 470, y: 636, rx: 150, ry: 46 };

/** Six seats around the meeting table, used when agents are called in. */
const SEATS = [
  { x: 350, y: 620 }, { x: 470, y: 598 }, { x: 590, y: 620 },
  { x: 350, y: 664 }, { x: 470, y: 682 }, { x: 590, y: 664 },
];

export type OfficeProps = {
  stations: Station[];
  states: Record<string, RobotState>;
  prices: Prices;
  stale: boolean;
  meetingActive: boolean;
  meetingSymbol: string | null;
  meetingLine: string;
  onPick: (id: string) => void;
};

export function PixelOffice(props: OfficeProps) {
  const { stations, states, prices, stale, meetingActive, meetingSymbol, meetingLine, onPick } = props;
  const pathRefs = useRef<Record<string, SVGPathElement | null>>({});
  const nodeRefs = useRef<Record<string, SVGGElement | null>>({});
  const progress = useRef<Record<string, { L: number }>>({});
  const [seated, setSeated] = useState(false);

  const desks = useMemo(() => stations.map((s, i) => {
    const x = COLS[i % 5];
    const y = ROWS[Math.floor(i / 5)] ?? ROWS[2];
    return { ...s, x, y, ry: y + 4 };
  }), [stations]);

  /** Agents that take a seat: the six that actually drive a meeting. */
  const seatOrder = ["market", "strategy", "risk", "ceo", "exec", "portfolio"];

  const walk = useCallback((toSeats: boolean) => {
    seatOrder.forEach((id) => {
      const path = pathRefs.current[id];
      const node = nodeRefs.current[id];
      if (!path || !node) return;
      const total = path.getTotalLength();
      if (!progress.current[id]) progress.current[id] = { L: 0 };
      const prog = progress.current[id];
      const update = () => {
        const L = Math.min(Math.max(prog.L, 0), total);
        const p = path.getPointAtLength(L);
        const q = path.getPointAtLength(Math.min(L + 2, total));
        const ang = (Math.atan2(q.y - p.y, q.x - p.x) * 180) / Math.PI;
        gsap.set(node, { x: p.x, y: p.y, rotation: toSeats ? ang * 0.12 : 0 });
      };
      gsap.to(prog, { L: toSeats ? total : 0, duration: 1.25, ease: "power3.inOut", onUpdate: update });
    });
    setSeated(toSeats);
  }, []);

  useEffect(() => {
    if (meetingActive && !seated) walk(true);
    if (!meetingActive && seated) walk(false);
  }, [meetingActive, seated, walk]);

  // park every robot at its desk on first paint
  useEffect(() => {
    desks.forEach((d) => {
      const node = nodeRefs.current[d.id];
      if (node) gsap.set(node, { x: d.x, y: d.ry, rotation: 0 });
    });
  }, [desks]);

  const ticker = ["BTC-USD", "ETH-USD", "SOL-USD"];

  return (
    <div className="office-wrap relative rounded-2xl border border-line overflow-hidden scanlines">
      <svg viewBox="0 0 960 720" className="block w-full h-auto" role="img"
           aria-label="Pixel-Art-Trading-Buero mit 15 Arbeitsplaetzen">
        <defs>
          <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#0a1130" /><stop offset="1" stopColor="#060a18" />
          </linearGradient>
          <linearGradient id="desk" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#16214a" /><stop offset="1" stopColor="#0c1330" />
          </linearGradient>
          <radialGradient id="roomGlow">
            <stop offset="0" stopColor="rgba(57,255,138,.16)" /><stop offset="1" stopColor="transparent" />
          </radialGradient>
        </defs>

        <rect width="960" height="720" fill="url(#wall)" />
        <g stroke="#101a3a" strokeWidth="1" className="pixel">
          <path d="M0 140H960M0 280H960M0 420H960M0 560H960M160 0V720M320 0V720M480 0V720M640 0V720M800 0V720" />
        </g>
        <ellipse cx={TABLE.x} cy={TABLE.y} rx="260" ry="120" fill="url(#roomGlow)" />

        {/* big central trading monitor */}
        <g className="pixel">
          <rect x="250" y="14" width="460" height="104" rx="4" fill="#060b1a" stroke="#22e8ff66" />
          <rect x="258" y="22" width="444" height="88" fill="#040814" />
          {ticker.map((sym, i) => {
            const p = prices[sym];
            const up = (p?.change_pct ?? 0) >= 0;
            return (
              <g key={sym} transform={`translate(${268 + i * 148}, 36)`}>
                <text x="0" y="0" fill="#8aa0bd" fontFamily="Space Grotesk, monospace" fontSize="10">{sym}</text>
                <text x="0" y="20" fill={stale ? "#8aa0bd" : up ? "#39ff8a" : "#ff4d6d"}
                      fontFamily="Space Grotesk, monospace" fontSize="16">
                  {p ? p.price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "—"}
                </text>
                <text x="0" y="36" fill={up ? "#39ff8a" : "#ff4d6d"}
                      fontFamily="Space Grotesk, monospace" fontSize="10">
                  {p ? `${up ? "+" : ""}${p.change_pct.toFixed(2)}%` : ""}
                </text>
              </g>
            );
          })}
          {/* candles drawn from the real 24h change, never random */}
          {ticker.map((sym, i) => {
            const p = prices[sym];
            const h = Math.min(30, Math.abs(p?.change_pct ?? 0) * 6 + 6);
            const up = (p?.change_pct ?? 0) >= 0;
            return (
              <rect key={sym + "c"} x={268 + i * 148 + 96} y={96 - h} width="8" height={h}
                    fill={up ? "#39ff8a" : "#ff4d6d"} opacity=".85" />
            );
          })}
          <text x="480" y="112" textAnchor="middle" fill={stale ? "#ffc34d" : "#39ff8a"}
                fontFamily="Space Grotesk, monospace" fontSize="9">
            {stale ? "DATA STALE" : "LIVE · COINBASE"}
          </text>
        </g>

        {/* side screens */}
        <g className="pixel" opacity=".9">
          <rect x="24" y="24" width="190" height="84" rx="3" fill="#060b1a" stroke="#a86bff55" />
          <text x="34" y="44" fill="#a86bff" fontFamily="Space Grotesk, monospace" fontSize="9">SOLANA · SCAN</text>
          <text x="34" y="62" fill="#8aa0bd" fontFamily="Space Grotesk, monospace" fontSize="8">GeckoTerminal</text>
          <text x="34" y="76" fill="#8aa0bd" fontFamily="Space Grotesk, monospace" fontSize="8">DexScreener</text>
          <text x="34" y="90" fill="#8aa0bd" fontFamily="Space Grotesk, monospace" fontSize="8">Solana RPC · Jupiter</text>
          <rect x="746" y="24" width="190" height="84" rx="3" fill="#060b1a" stroke="#39ff8a55" />
          <text x="756" y="44" fill="#39ff8a" fontFamily="Space Grotesk, monospace" fontSize="9">RISK · DECISION</text>
          <text x="756" y="62" fill="#8aa0bd" fontFamily="Space Grotesk, monospace" fontSize="8">RiskManager Veto aktiv</text>
          <text x="756" y="76" fill="#8aa0bd" fontFamily="Space Grotesk, monospace" fontSize="8">Live autonom: LOCKED</text>
          <text x="756" y="90" fill="#8aa0bd" fontFamily="Space Grotesk, monospace" fontSize="8">Modus: PAPER</text>
        </g>

        {/* walk paths (desk -> seat), invisible but measurable */}
        <g fill="none" stroke="#16224a" strokeDasharray="3 6" opacity=".45">
          {desks.map((d) => {
            const idx = seatOrder.indexOf(d.id);
            if (idx < 0) return null;
            const s = SEATS[idx];
            const mx = (d.x + s.x) / 2;
            const my = (d.ry + s.y) / 2 - 40;
            return (
              <path key={d.id} ref={(el) => { pathRefs.current[d.id] = el; }}
                    d={`M ${d.x} ${d.ry} Q ${mx} ${my} ${s.x} ${s.y}`} />
            );
          })}
        </g>

        {/* meeting table */}
        <g className="pixel">
          <ellipse cx={TABLE.x} cy={TABLE.y} rx={TABLE.rx} ry={TABLE.ry}
                   fill="url(#desk)" stroke={meetingActive ? "#a86bff" : "#243463"} strokeWidth="2" />
          <rect x={TABLE.x - 120} y={TABLE.y - 96} width="240" height="46" rx="4"
                fill="#060b1a" stroke={meetingActive ? "#a86bff" : "#243463"} />
          <text x={TABLE.x} y={TABLE.y - 76} textAnchor="middle" fill="#22e8ff"
                fontFamily="Space Grotesk, monospace" fontSize="13">
            {meetingSymbol ?? "MEETING ROOM"}
          </text>
          <text x={TABLE.x} y={TABLE.y - 60} textAnchor="middle" fill="#8aa0bd"
                fontFamily="Space Grotesk, monospace" fontSize="9">
            {meetingLine || (meetingActive ? "Meeting laeuft" : "bereit")}
          </text>
        </g>

        {/* 15 workstations */}
        {desks.map((d) => {
          const st = states[d.id] ?? (d.connected ? "IDLE" : "OFFLINE");
          const off = !d.connected;
          const mcol = off ? "#2a3350"
            : st === "ERROR" || st === "SELL_PREP" ? "#ff4d6d"
            : st === "SUCCESS" || st === "BUY_PREP" ? "#39ff8a"
            : st === "NO_TRADE" ? "#ffc34d" : "#22e8ff";
          return (
            <g key={d.id} className="cursor-pointer" onClick={() => onPick(d.id)}
               role="button" tabIndex={0}
               onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onPick(d.id); }}>
              <title>{`${d.num}. ${d.name} — ${d.status}`}</title>
              {/* solid hit area so clicks and taps land on the whole station */}
              <rect x={d.x - 58} y={d.y - 56} width="116" height="120" fill="transparent"
                    pointerEvents="all" />
              {/* desk + monitor */}
              <rect x={d.x - 54} y={d.y + 20} width="108" height="24" rx="3" fill="url(#desk)" stroke="#243463" className="pixel" />
              <rect x={d.x - 34} y={d.y - 54} width="68" height="40" rx="3" fill="#060b1a" stroke={mcol} className="pixel" />
              <rect x={d.x - 29} y={d.y - 49} width="58" height="30" fill="#040814" className="pixel" />
              {[0, 1, 2, 3].map((r) => (
                <rect key={r} x={d.x - 25} y={d.y - 45 + r * 7} width={off ? 14 : 20 + (r % 3) * 8}
                      height="3" fill={mcol} opacity={off ? ".25" : ".6"} className="pixel" />
              ))}
              {off && (
                <text x={d.x} y={d.y - 26} textAnchor="middle" fill="#ff4d6d"
                      fontFamily="Space Grotesk, monospace" fontSize="7">NOT CONNECTED</text>
              )}
              {/* number badge */}
              <rect x={d.x - 54} y={d.y - 54} width="16" height="12" fill={d.color} className="pixel" />
              <text x={d.x - 46} y={d.y - 45} textAnchor="middle" fill="#04060f"
                    fontFamily="Space Grotesk, monospace" fontSize="8" fontWeight="700">
                {String(d.num).padStart(2, "0")}
              </text>
              {/* name plate */}
              <rect x={d.x - 56} y={d.y + 47} width="112" height="15" rx="2" fill="#070d20" stroke="#1d2a4d" className="pixel" />
              <text x={d.x} y={d.y + 58} textAnchor="middle" fill="#9fb3d9"
                    fontFamily="Space Grotesk, monospace" fontSize="8">{d.short} · {d.name.slice(0, 18)}</text>
              {/* robot */}
              <g ref={(el) => { nodeRefs.current[d.id] = el; }}>
                <g transform="translate(-14,-14)">
                  <PixelRobot color={d.color} state={st} />
                </g>
              </g>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
