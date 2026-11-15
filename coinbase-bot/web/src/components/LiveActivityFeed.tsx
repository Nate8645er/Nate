import { AnimatePresence, motion } from "framer-motion";
import type { Statement } from "../lib/types";

const COLOR: Record<string, string> = {
  BUY: "text-emerald-400", SELL: "text-red-400", HOLD: "text-white/60",
  "NO TRADE": "text-amber-300", VETO: "text-red-400",
};

export function LiveActivityFeed({ items }: { items: Statement[] }) {
  return (
    <div className="max-h-[420px] space-y-2 overflow-y-auto pr-1">
      <AnimatePresence initial={false}>
        {items.slice().reverse().map((s, i) => (
          <motion.div key={`${s.step}-${s.agent}-${i}`}
            initial={{ opacity: 0, x: 18 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}
            className="rounded-xl border border-line bg-panel/70 p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono text-[11px] tracking-wide text-cyan">
                {s.agent} · Schritt {s.step}
              </span>
              <span className={`font-mono text-[10px] ${COLOR[s.decision] ?? "text-white/60"}`}>
                {s.decision}
              </span>
            </div>
            <p className="mt-1 text-xs text-white/60">{s.rationale}</p>
          </motion.div>
        ))}
      </AnimatePresence>
      {items.length === 0 && (
        <p className="text-xs text-white/40">Noch keine Agentenereignisse. Starte ein Team-Meeting.</p>
      )}
    </div>
  );
}
