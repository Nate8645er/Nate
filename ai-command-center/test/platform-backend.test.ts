import { describe, it, expect } from "vitest";
import { backendBaseUrl, fetchCompute, formatMemoryGb, primaryDevice, type ComputeResponse } from "@/lib/platform-backend";

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
