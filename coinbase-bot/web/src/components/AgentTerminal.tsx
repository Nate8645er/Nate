import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import type { Statement, Station } from "../lib/types";

export function AgentTerminal({ station, log, onClose }: {
  station: Station | null; log: Statement[]; onClose: () => void;
}) {
  return (
    <AnimatePresence>
      {station && (
        <motion.div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/70 p-3"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
          <motion.div
            initial={{ y: 40, scale: .97 }} animate={{ y: 0, scale: 1 }} exit={{ y: 40, opacity: 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 26 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg rounded-2xl border border-line bg-panel/95 backdrop-blur-xl overflow-hidden">
            <div className="flex items-center justify-between border-b border-line px-4 py-3"
                 style={{ background: `linear-gradient(90deg, ${station.color}22, transparent)` }}>
              <div className="min-w-0">
                <p className="font-mono text-[10px] tracking-widest text-white/50">
                  WORKSTATION {String(station.num).padStart(2, "0")}
                </p>
                <h3 className="truncate text-sm font-bold" style={{ color: station.color }}>{station.name}</h3>
              </div>
              <button onClick={onClose} aria-label="Schliessen"
                      className="rounded-lg border border-line p-1.5 text-white/60 hover:text-white">
                <X size={16} />
              </button>
            </div>
            <div className="space-y-3 p-4 font-mono text-xs">
              <Row k="STATUS" v={station.status} color={station.connected ? "#39ff8a" : "#ff4d6d"} />
              <Row k="BACKEND" v={station.backend || "— keine Backend-Funktion —"} />
              <Row k="LAST ACTION" v={log.length ? `${log[log.length - 1].agent}: ${log[log.length - 1].decision}` : "—"} />
              <div>
                <p className="mb-1 text-white/40">ACTIVITY HISTORY</p>
                <div className="max-h-52 space-y-1 overflow-y-auto rounded-lg border border-line bg-black/40 p-2">
                  {log.length === 0 && <p className="text-white/35">Keine Aktivität aufgezeichnet.</p>}
                  {log.slice().reverse().map((s, i) => (
                    <p key={i} className="text-white/70">
                      <span className="text-cyan">[{s.step}]</span> {s.decision} — {s.rationale}
                    </p>
                  ))}
                </div>
              </div>
              {!station.connected && (
                <p className="rounded-lg border border-loss/40 bg-loss/10 p-2 text-loss">
                  Dieser Arbeitsplatz hat noch keine Backend-Integration. Es läuft hier kein Agent.
                </p>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function Row({ k, v, color }: { k: string; v: string; color?: string }) {
  return (
    <div className="flex gap-3">
      <span className="w-28 shrink-0 text-white/40">{k}</span>
      <span className="min-w-0 break-words" style={color ? { color } : undefined}>{v}</span>
    </div>
  );
}
