---
description: Zweitmeinung vom KI-Team — 13 Modelle aus 13 Firmen ueber OpenRouter
---
Hole eine echte Zweitmeinung von verschiedenen Anbieter-Modellen (nicht
13x dasselbe Modell) zu: $ARGUMENTS

```bash
cd platform-backend && set -a && . ./.env && set +a
python3 ops/council.py --dry-run "$ARGUMENTS"   # erst Kosten/Auswahl zeigen
python3 ops/council.py --only OpenAI,Google,DeepSeek "$ARGUMENTS"
```

Regeln: Kosten vor dem Senden nennen. Frage konkret stellen ("max 5 Saetze").
Bei drei ausreichenden Meinungen `--only` nutzen statt aller 13. Der Wert
liegt in der **Konvergenz** — nennen unabhaengige Modelle dieselbe Loesung,
ist das ein starkes Signal; widersprechen sie sich, ist die Frage unscharf
oder das Problem echt strittig.
