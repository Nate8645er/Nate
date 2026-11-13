import type { CSSProperties } from "react";

export type RobotState =
  | "IDLE" | "ANALYZING" | "SCANNING" | "MEETING" | "RISK_CHECK"
  | "BUY_PREP" | "SELL_PREP" | "NO_TRADE" | "ERROR" | "SUCCESS" | "OFFLINE";

const EYE: Record<RobotState, string> = {
  IDLE: "#9fb3d9", ANALYZING: "#22e8ff", SCANNING: "#39ff8a", MEETING: "#a86bff",
  RISK_CHECK: "#39ff8a", BUY_PREP: "#39ff8a", SELL_PREP: "#ff4d6d",
  NO_TRADE: "#ffc34d", ERROR: "#ff4d6d", SUCCESS: "#39ff8a", OFFLINE: "#44506e",
};

/** A blocky pixel robot drawn from plain rects, so it stays crisp at any size. */
export function PixelRobot({ color, state, scale = 1 }: {
  color: string; state: RobotState; scale?: number;
}) {
  const off = state === "OFFLINE";
  const body = off ? "#2a3350" : color;
  const eye = EYE[state];
  const anim = state === "ANALYZING" || state === "SCANNING" ? "anim-typing"
    : state === "OFFLINE" ? "" : "anim-bob";
  const style: CSSProperties = { transformOrigin: "center", transformBox: "fill-box" };
  return (
    <g className={`pixel ${anim}`} style={style} transform={`scale(${scale})`}>
      {/* antenna */}
      <rect x="13" y="-2" width="2" height="4" fill={off ? "#2a3350" : eye} />
      <rect x="12" y="-5" width="4" height="3" fill={off ? "#2a3350" : eye} className={off ? "" : "anim-pulse"} />
      {/* head */}
      <rect x="4" y="2" width="20" height="14" fill={body} />
      <rect x="2" y="4" width="2" height="10" fill={body} />
      <rect x="24" y="4" width="2" height="10" fill={body} />
      {/* visor */}
      <rect x="6" y="6" width="16" height="7" fill="#060b1a" />
      <rect x="8" y="8" width="4" height="3" fill={eye} className={off ? "" : "anim-blink"} />
      <rect x="16" y="8" width="4" height="3" fill={eye} className={off ? "" : "anim-blink"} />
      {/* body */}
      <rect x="6" y="17" width="16" height="10" fill={body} opacity={off ? 1 : 0.92} />
      <rect x="9" y="20" width="10" height="4" fill="#060b1a" />
      <rect x="11" y="21" width="2" height="2" fill={eye} />
      {/* arms */}
      <rect x="2" y="18" width="4" height="7" fill={body} />
      <rect x="22" y="18" width="4" height="7" fill={body} />
    </g>
  );
}

export const DECISION_STATE: Record<string, RobotState> = {
  BUY: "BUY_PREP", SELL: "SELL_PREP", HOLD: "IDLE",
  "NO TRADE": "NO_TRADE", VETO: "ERROR",
};
