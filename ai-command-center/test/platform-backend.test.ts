import { describe, it, expect } from "vitest";
import { backendBaseUrl, describePlacement, fetchCompute, formatMemoryGb, primaryDevice, routeModel, runMissionViaBackend, type ComputeResponse } from "@/lib/platform-backend";

const SAMPLE: ComputeResponse = {
  gpu_available: false,
  device_count: 1,
  devices: [
    {
      id: "cpu:0",
      vendor: "cpu",
      name: "x86_64",
      arch: "x86_64",
      memory_total_mb: 16075,
      memory_model: "unified",
      backends: ["cpu", "llama_cpp", "onnx"],
      capabilities: ["fp32"],
    },
  ],
};

describe("platform-backend Anbindung (ehrlich, additiv)", () => {
  it("backendBaseUrl: leer = null, sonst getrimmt ohne Slash", () => {
    expect(backendBaseUrl({})).toBeNull();
    expect(backendBaseUrl({ PLATFORM_BACKEND_URL: "  " })).toBeNull();
    expect(backendBaseUrl({ PLATFORM_BACKEND_URL: "http://x:8099/" })).toBe("http://x:8099");
  });

  it("fetchCompute: nicht konfiguriert → null (kein Fetch)", async () => {
    let called = false;
    const fake = (async () => {
      called = true;
      return new Response("{}");
    }) as unknown as typeof fetch;
    const res = await fetchCompute({ baseUrl: null, fetchImpl: fake });
    expect(res).toBeNull();
    expect(called).toBe(false);
  });

  it("fetchCompute: erreichbares Backend → geparste Daten", async () => {
    const fake = (async () => new Response(JSON.stringify(SAMPLE), { status: 200 })) as unknown as typeof fetch;
    const res = await fetchCompute({ baseUrl: "http://x:8099", fetchImpl: fake });
    expect(res?.devices[0].name).toBe("x86_64");
  });

  it("fetchCompute: HTTP-Fehler → null (ehrlicher Fallback, nie werfen)", async () => {
    const fake = (async () => new Response("nope", { status: 500 })) as unknown as typeof fetch;
    const res = await fetchCompute({ baseUrl: "http://x:8099", fetchImpl: fake });
    expect(res).toBeNull();
  });

  it("fetchCompute: Netzwerkfehler/Timeout → null", async () => {
    const fake = (async () => {
      throw new Error("ECONNREFUSED");
    }) as unknown as typeof fetch;
    const res = await fetchCompute({ baseUrl: "http://x:8099", fetchImpl: fake });
    expect(res).toBeNull();
  });

  it("formatMemoryGb: MB → GB, ungültig → —", () => {
    expect(formatMemoryGb(16075)).toBe("15.7 GB");
    expect(formatMemoryGb(0)).toBe("—");
    expect(formatMemoryGb(-1)).toBe("—");
  });

  it("routeModel: nicht konfiguriert → null (kein Fetch)", async () => {
    let called = false;
    const fake = (async () => {
      called = true;
      return new Response("{}");
    }) as unknown as typeof fetch;
    const res = await routeModel({ data_class: "local_only" }, { baseUrl: null, fetchImpl: fake });
    expect(res).toBeNull();
    expect(called).toBe(false);
  });

  it("routeModel: liefert Entscheidung; POST an /api/v1/models/route", async () => {
    let seenUrl = "";
    let seenMethod = "";
    const fake = (async (url: string, init: RequestInit) => {
      seenUrl = url;
      seenMethod = init.method ?? "";
      return new Response(JSON.stringify({ placement: "local", reason: "local_only", fallback: null }), { status: 200 });
    }) as unknown as typeof fetch;
    const res = await routeModel({ data_class: "local_only" }, { baseUrl: "http://x:8000", fetchImpl: fake });
    expect(res?.placement).toBe("local");
    expect(seenUrl).toBe("http://x:8000/api/v1/models/route");
    expect(seenMethod).toBe("POST");
  });

  it("routeModel: HTTP-Fehler/Netzwerkfehler → null", async () => {
    const err = (async () => {
      throw new Error("ECONNREFUSED");
    }) as unknown as typeof fetch;
    expect(await routeModel({}, { baseUrl: "http://x:8000", fetchImpl: err })).toBeNull();
    const bad = (async () => new Response("x", { status: 500 })) as unknown as typeof fetch;
    expect(await routeModel({}, { baseUrl: "http://x:8000", fetchImpl: bad })).toBeNull();
  });

  it("runMissionViaBackend: ohne Token → null (kein Delegieren)", async () => {
    let called = false;
    const fake = (async () => {
      called = true;
      return new Response("{}");
    }) as unknown as typeof fetch;
    const res = await runMissionViaBackend("Ziel", null, { baseUrl: "http://x:8000", fetchImpl: fake });
    expect(res).toBeNull();
    expect(called).toBe(false);
  });

  it("runMissionViaBackend: mit Token → Ergebnis, Bearer-Header gesetzt", async () => {
    let auth = "";
    let seenUrl = "";
    const fake = (async (url: string, init: RequestInit) => {
      seenUrl = url;
      auth = (init.headers as Record<string, string>).authorization ?? "";
      return new Response(
        JSON.stringify({ ok: true, placement: "local", reason: "ok", text: "fertig", error: null }),
        { status: 200 },
      );
    }) as unknown as typeof fetch;
    const res = await runMissionViaBackend("Ziel", "tok123", { baseUrl: "http://x:8000", fetchImpl: fake });
    expect(res?.text).toBe("fertig");
    expect(seenUrl).toBe("http://x:8000/api/v1/missions");
    expect(auth).toBe("Bearer tok123");
  });

  it("runMissionViaBackend: 503/ok=false → null (Fallback auf lokal)", async () => {
    const notReady = (async () => new Response("x", { status: 503 })) as unknown as typeof fetch;
    expect(await runMissionViaBackend("z", "t", { baseUrl: "http://x:8000", fetchImpl: notReady })).toBeNull();
    const notOk = (async () =>
      new Response(JSON.stringify({ ok: false, text: null }), { status: 200 })) as unknown as typeof fetch;
    expect(await runMissionViaBackend("z", "t", { baseUrl: "http://x:8000", fetchImpl: notOk })).toBeNull();
  });

  it("describePlacement: null → '—', local → 'Lokal', cloud → 'Cloud'", () => {
    expect(describePlacement(null)).toEqual({ label: "—", hint: "Backend nicht verbunden" });
    expect(describePlacement({ placement: "local", reason: "R", fallback: null }).label).toBe("Lokal (im Haus)");
    expect(describePlacement({ placement: "cloud", reason: "R2", fallback: "local" })).toEqual({
      label: "Cloud",
      hint: "R2",
    });
  });

  it("primaryDevice: bevorzugt GPU, sonst CPU, null-sicher", () => {
    expect(primaryDevice(null)).toBeNull();
    expect(primaryDevice(SAMPLE)?.vendor).toBe("cpu");
    const withGpu: ComputeResponse = {
      gpu_available: true,
      device_count: 2,
      devices: [
        SAMPLE.devices[0],
        { ...SAMPLE.devices[0], id: "gpu:0", vendor: "nvidia", name: "RTX", memory_model: "dedicated" },
      ],
    };
    expect(primaryDevice(withGpu)?.vendor).toBe("nvidia");
  });
});
