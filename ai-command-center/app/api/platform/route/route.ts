/**
 * POST /api/platform/route  (Cutover-UI-Proxy)
 *
 * Dünner Server-Proxy: nimmt { goal, dataClass? } vom Browser und fragt die
 * Routing-Entscheidung des platform-backend ab (das intern erreichbar ist, der
 * Browser aber nicht). Gibt die Entscheidung zurück oder `{ connected:false }`,
 * wenn kein Backend konfiguriert/erreichbar ist — ehrlich, nie werfen.
 */

import { routeModel, type DataClass } from "@/lib/platform-backend";

export const runtime = "nodejs";

export async function POST(request: Request): Promise<Response> {
  let goal = "";
  let dataClass: DataClass = "internal";
  try {
    const body = (await request.json()) as { goal?: unknown; dataClass?: unknown };
    goal = typeof body.goal === "string" ? body.goal.slice(0, 2000) : "";
    if (body.dataClass === "local_only" || body.dataClass === "public" || body.dataClass === "internal") {
      dataClass = body.dataClass;
    }
  } catch {
    return Response.json({ connected: false, error: "ungueltiger-body" }, { status: 400 });
  }

  const decision = await routeModel({
    prompt_tokens_est: Math.max(1, Math.ceil(goal.length / 4)),
    data_class: dataClass,
  });
  if (!decision) return Response.json({ connected: false });
  return Response.json({ connected: true, decision });
}
