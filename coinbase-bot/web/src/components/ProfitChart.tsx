import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export type Point = { t: string; v: number };

export function ProfitChart({ data, label }: { data: Point[]; label: string }) {
  if (data.length === 0) {
    return <p className="p-6 text-center text-xs text-white/40">
      Keine Datenpunkte — es wurde noch kein Trade ausgeführt. Nichts wird erfunden.
    </p>;
  }
  const up = data[data.length - 1].v >= data[0].v;
  const stroke = up ? "#39ff8a" : "#ff4d6d";
  return (
    <div className="h-48 w-full min-w-0">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id="pg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={stroke} stopOpacity={0.45} />
              <stop offset="100%" stopColor={stroke} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#16224a" vertical={false} />
          <XAxis dataKey="t" tick={{ fill: "#6f82ab", fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "#6f82ab", fontSize: 10 }} axisLine={false} tickLine={false} width={52} />
          <Tooltip contentStyle={{ background: "#0b1226", border: "1px solid #1b2a4d", borderRadius: 10, fontSize: 12 }}
                   labelStyle={{ color: "#8aa0bd" }} formatter={(v: number) => [v.toFixed(2), label]} />
          <Area type="monotone" dataKey="v" stroke={stroke} strokeWidth={2} fill="url(#pg)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
