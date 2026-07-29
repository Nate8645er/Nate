"use client";

/**
 * Plan-Gating für Arbeitsbereiche. `usePlanGate(bereich, titel)` liefert
 * `null`, wenn das aktuelle Abo (localStorage `acc-plan`) den Bereich nutzen
 * darf – sonst eine fertige, gesperrte Ansicht (mit Navigation + Upgrade-
 * Hinweis), die die Seite per früher Rückgabe anzeigt:
 *
 *   const gate = usePlanGate("analysen", "Analysen");
 *   if (gate) return gate;
 *
 * Bewusst clientseitig, weil der Plan – wie im ganzen Arbeitsbereich – in
 * localStorage liegt. Basis-Bereiche (ohne Mindest-Plan) sind immer offen.
 */

import { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import WorkNav, { type BereichId } from "@/app/components/WorkNav";
import type { PlanId } from "@/lib/agents/types";
import { hatZugriff, minPlanFuer, PLAN_LABEL } from "@/lib/features";

const PLAN_KEY = "acc-plan";
const GUELTIG: readonly PlanId[] = ["FREE", "PERSONAL", "STARTER", "PROFESSIONAL", "BUSINESS", "ENTERPRISE"];

export function usePlanGate(bereich: BereichId, titel: string): ReactNode | null {
  const [plan, setPlan] = useState<PlanId | null>(null);

  useEffect(() => {
    const lese = () => {
      const roh = (localStorage.getItem(PLAN_KEY) || "FREE").toUpperCase();
      setPlan((GUELTIG.includes(roh as PlanId) ? roh : "FREE") as PlanId);
    };
    lese();
    const onStorage = (e: StorageEvent) => {
      if (e.key === PLAN_KEY) lese();
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const min = minPlanFuer(bereich);
  if (!min) return null; // Basis-Bereich – immer offen
  if (plan === null) return null; // vor dem Mounten: Seite normal starten lassen
  if (hatZugriff(plan, bereich)) return null;

  return <GesperrteAnsicht bereich={bereich} titel={titel} plan={plan} min={min} />;
}

/**
 * PlanGate – Wrapper-Variante für SERVER-Komponenten (die keine Hooks nutzen
 * dürfen). Rendert die (serverseitig erzeugten) `children`, wenn das Abo den
 * Bereich freigibt, sonst die gesperrte Ansicht.
 */
export default function PlanGate({
  bereich,
  titel,
  children,
}: {
  bereich: BereichId;
  titel: string;
  children: ReactNode;
}) {
  const gate = usePlanGate(bereich, titel);
  return <>{gate ?? children}</>;
}

function GesperrteAnsicht({
  bereich,
  titel,
  plan,
  min,
}: {
  bereich: BereichId;
  titel: string;
  plan: PlanId;
  min: PlanId;
}) {
  return (
    <div className="acc-page min-h-dvh text-[#1c1917]">
      <div className="mx-auto max-w-6xl px-5 py-6">
        <div className="mb-10 flex justify-end">
          <WorkNav aktiv={bereich} variante="dunkel" />
        </div>
        <div className="mx-auto max-w-2xl">
          <div className="acc-card rounded-3xl p-8 text-center sm:p-12">
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-[#ff8c2a] to-[#ff5f1f] text-3xl shadow-[0_10px_30px_-8px_rgba(255,110,30,0.6)]">
              🔒
            </div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[#9aa0bd]">
              Ab {PLAN_LABEL[min]} verfügbar
            </p>
            <h1 className="mt-3 text-2xl font-bold text-[#eef0f8] sm:text-3xl">
              {titel} ist in Ihrem Abo noch nicht freigeschaltet
            </h1>
            <p className="mx-auto mt-4 max-w-lg text-[#9aa0bd]">
              Ihr aktuelles Abo ist{" "}
              <strong className="text-[#eef0f8]">{PLAN_LABEL[plan]}</strong>. Diese
              Funktion gehört zum {PLAN_LABEL[min]}-Paket und höher. Je höher Ihr
              Abo, desto mehr Bereiche des KI-Systems stehen Ihnen offen.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Link
                href="/preise"
                className="rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-6 py-3 font-semibold text-white shadow-[0_8px_24px_-8px_rgba(255,110,30,0.6)] transition hover:brightness-105"
              >
                Auf {PLAN_LABEL[min]} upgraden
              </Link>
              <Link
                href="/dashboard"
                className="rounded-full border border-white/15 px-6 py-3 font-semibold text-[#eef0f8] transition hover:border-[#ff8c2a] hover:text-[#ffb066]"
              >
                Zurück zum Dashboard
              </Link>
            </div>
            <p className="mt-6 text-xs text-[#7b809b]">
              Zum Testen können Sie das Abo im Dashboard oben umschalten.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
