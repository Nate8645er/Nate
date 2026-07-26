---
name: ai-council
description: >-
  Das KI-Team: echte Zweitmeinungen von 13 Modellen aus 13 verschiedenen
  Firmen (OpenAI, Anthropic, Google, xAI, Moonshot, DeepSeek, Alibaba, Meta,
  Mistral, Z-AI, Microsoft, Cohere, NVIDIA) ueber einen einzigen
  OpenRouter-Key. AKTIVIEREN bei Architektur- und Technologie-Entscheidungen,
  bei denen eine zweite, andersartige Sicht mehr bringt als eine weitere Runde
  desselben Modells, oder auf Trigger: "/council", "frag das KI-Team",
  "Zweitmeinung", "was sagen die anderen Modelle", "lass abstimmen".
---

# Das KI-Team (Council)

## Wichtig zum Verstaendnis

Claude-Subagenten (`ultra-security`, `ultra-fullstack` usw.) sind **alle
dasselbe Modell** mit unterschiedlichen Rollen-Prompts. Das Council ist etwas
anderes: es fragt ueber OpenRouter **wirklich verschiedene Modelle
verschiedener Firmen**. Genau darum ist es fuer Entscheidungen wertvoll — die
Modelle haben unterschiedliche Trainingsdaten und Fehlermuster.

## Ausfuehren

```bash
cd platform-backend
set -a; . ./.env; set +a                      # OPENROUTER_API_KEY laden

python3 ops/council.py --dry-run "Frage"      # zeigt nur, wer gefragt wuerde (0 Kosten)
python3 ops/council.py --only OpenAI,Google,DeepSeek "Frage"
python3 ops/council.py "Frage"                # alle 13
python3 ops/council_check.py                  # Verfuegbarkeit aller 13 pruefen
```

## Die 13 Mitglieder

Je das staerkste real existierende Modell pro Anbieter. Alle IDs stammen aus
dem OpenRouter-Live-Katalog und wurden per `council_check.py` **real getestet
— 13/13 haben geantwortet und sich selbst identifiziert.**

`openai/gpt-5.6-sol-pro` · `anthropic/claude-opus-4.8` ·
`google/gemini-3.1-pro-preview` · `x-ai/grok-4.5` · `moonshotai/kimi-k3` ·
`deepseek/deepseek-v4-pro` · `qwen/qwen3.7-max` ·
`meta-llama/llama-4-maverick` · `mistralai/mistral-large-2512` ·
`z-ai/glm-5.2` · `microsoft/phi-4` · `cohere/command-a` ·
`nvidia/nemotron-3-ultra-550b-a55b`

## Regeln beim Einsatz

1. **Kosten nennen, bevor gefragt wird.** Jeder Lauf verbraucht echte
   OpenRouter-Credits. Ein Durchlauf aller 13 mit kurzer Frage lag real bei
   ~2.1k Token rein / ~2.9k raus. `--dry-run` kostet nichts.
2. **Konkret fragen.** „Max 5 Saetze, konkret" liefert brauchbare Antworten;
   offene Essayfragen verbrennen nur Budget.
3. **`--only` nutzen**, wenn drei Meinungen reichen. Nicht immer alle 13.
4. **Antworten pruefen, nicht uebernehmen.** Auch die anderen Modelle irren.
   Wert entsteht durch **Konvergenz**: wenn drei unabhaengige Modelle
   dieselbe Loesung nennen, ist das ein starkes Signal. Widersprechen sie
   sich, ist die Frage wahrscheinlich schlecht gestellt oder das Problem
   echt strittig — beides nuetzlich zu wissen.
5. **Reasoning-Modelle brauchen Budget.** Gemini, Kimi, DeepSeek und GLM
   verbrauchen ihr Token-Budget zuerst fuer internes Denken. Bei zu kleinem
   `--max-tokens` kommt eine LEERE Antwort zurueck — das ist kein Ausfall,
   sondern ein zu enges Limit. Default ist deshalb 2000.

## Beispiel aus der Praxis

Frage nach der pragmatischsten Loesung fuer ein TOCTOU-Problem bei der
Token-Limit-Pruefung (ohne Redis). OpenAI, Google und DeepSeek kamen
**unabhaengig auf dieselbe Loesung**: atomare Reservierung per konditionalem
`UPDATE ... WHERE used + n <= limit RETURNING` vor dem LLM-Aufruf, Abgleich
danach. Diese Konvergenz war das eigentliche Ergebnis — nicht die einzelne
Antwort.

## Ehrlichkeits-Hinweis

Es kursieren Modellnamen, die **nicht existieren** (gegen den Live-Katalog
geprueft): „GPT-5.6 Sol Ultra", „Gemini 3.1 Pro Ultra", „Grok 4.5 Heavy",
„Qwen 3.8 Max", „Mistral Large 3", „Command A+", „Nemotron Ultra". Wenn eine
Quelle solche Namen als „live" bezeichnet, wurde dort nichts geprueft. Nur
IDs verwenden, die `council_check.py` bestaetigt.
