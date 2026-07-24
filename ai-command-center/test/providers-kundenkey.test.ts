import { describe, it, expect, vi, afterEach } from "vitest";
import { callLLM, customerKeyStore } from "@/lib/agents/providers";
import type { ChatMessage } from "@/lib/agents/types";

const MSG: ChatMessage[] = [{ role: "user", content: "hallo" }];

function stubFetch(): { seen: () => string } {
  let seenKey = "";
  vi.stubGlobal("fetch", (async (_u: string, init: RequestInit) => {
    seenKey = (init.headers as Record<string, string>)["x-api-key"] ?? "";
    return { ok: true, status: 200, json: async () => ({ content: [{ text: "hi" }] }) };
  }) as unknown as typeof fetch);
  return { seen: () => seenKey };
}

describe("callLLM: Bring-your-own-key-Override (Sicherheit)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    delete process.env.ANTHROPIC_API_KEY;
  });

  it("nutzt den Kundenschlüssel (x-api-key) — Vorrang vor dem Betreiber-Env-Key", async () => {
    process.env.ANTHROPIC_API_KEY = "sk-betreiber-1234567890";
    const f = stubFetch();
    await customerKeyStore.run({ anthropic: "sk-kunde-ABCDEFGHIJ" }, () =>
      callLLM("anthropic", "claude-x", "sys", MSG),
    );
    expect(f.seen()).toBe("sk-kunde-ABCDEFGHIJ");
  });

  it("ohne Kundenschlüssel: fällt auf den Betreiber-Env-Key zurück", async () => {
    process.env.ANTHROPIC_API_KEY = "sk-betreiber-1234567890";
    const f = stubFetch();
    await callLLM("anthropic", "claude-x", "sys", MSG);
    expect(f.seen()).toBe("sk-betreiber-1234567890");
  });

  it("Kundenschlüssel gilt nur im run()-Kontext, danach wieder Env", async () => {
    process.env.ANTHROPIC_API_KEY = "sk-betreiber-1234567890";
    const f = stubFetch();
    await customerKeyStore.run({ anthropic: "sk-kunde-ABCDEFGHIJ" }, () => callLLM("anthropic", "m", "s", MSG));
    expect(f.seen()).toBe("sk-kunde-ABCDEFGHIJ");
    await callLLM("anthropic", "m", "s", MSG); // ausserhalb -> Env
    expect(f.seen()).toBe("sk-betreiber-1234567890");
  });
});
