"""Phase 8 live token discovery on REAL free data (GeckoTerminal/DexScreener).

Read-only, no key, no order. Scans new Solana pools, categorises by market cap,
runs the memecoin risk gate (missing data -> UNKNOWN, thin exit liquidity ->
veto). Prints only real fetched data; on network failure it prints a clear
limitation instead of inventing tokens.

    python run_discovery.py
"""

from collections import Counter

from multimarket import (
    ADAPTERS,
    DexScreenerSource,
    GeckoTerminalSource,
    TokenScanner,
    assess_memecoin_risk,
    should_veto,
    valuation,
)


def main() -> int:
    print("Adapter-Status:")
    for a in ADAPTERS:
        print(f"  {a.name:18} {a.market:26} {a.status.value}")
    print()

    sources = [GeckoTerminalSource("solana"), DexScreenerSource()]
    results = TokenScanner(sources).scan()
    if not results:
        print("Keine Daten abrufbar (Netzwerk/API) — keine erfundenen Token. Abbruch.")
        return 0

    cats = Counter(r["category"].value for r in results)
    print(f"Entdeckte Token (dedup): {len(results)}")
    for k, v in cats.items():
        print(f"  {k}: {v}")

    vetoed = 0
    print("\nStichprobe (echte Daten, Risiko-Gate):")
    for r in results[:10]:
        t = r["token"]
        v = valuation(t)
        risk = assess_memecoin_risk(t)
        if should_veto(risk):
            vetoed += 1
        mc = f"{v['value_usd']:.0f}" if v["value_usd"] else "None"
        print(
            f"  {t.name[:24]:24} {t.network} mc/fdv={mc:>10} "
            f"liq={t.liquidity_usd} risk={risk.level.value} veto={should_veto(risk)} "
            f"uncertain={v['uncertain']}"
        )
    print(
        f"\nRisk-Veto in Stichprobe: {vetoed}/{min(10, len(results))} "
        f"(fehlende/zu geringe Exit-Liquiditaet)."
    )
    print(
        "Hinweis: niedrige Market Cap allein ist KEIN Kaufsignal; alle Treffer bleiben Paper."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
