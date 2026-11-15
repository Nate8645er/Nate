import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight, DollarSign } from "lucide-react";
import type { LucideIcon } from "lucide-react";

type StatsCardProps = {
  title: string;
  value: string;
  change?: number;
  icon?: LucideIcon;
  hint?: string;
};

export function StatsCard({ title, value, change, icon: Icon = DollarSign, hint }: StatsCardProps) {
  const positive = (change ?? 0) >= 0;
  return (
    <motion.div
      whileHover={{ y: -5 }}
      transition={{ duration: 0.2 }}
      className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl min-w-0"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-wider text-white/60">{title}</p>
          <h2 className="text-2xl font-bold text-white break-words tabular-nums">{value}</h2>
          {change !== undefined && (
            <div className={`flex items-center gap-1 text-sm ${positive ? "text-emerald-400" : "text-red-400"}`}>
              {positive ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
              {change.toFixed(2)}%
            </div>
          )}
          {hint && <p className="mt-1 text-[11px] text-white/40">{hint}</p>}
        </div>
        <Icon className="text-violet shrink-0" size={20} />
      </div>
    </motion.div>
  );
}
