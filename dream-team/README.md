# 🤝 AI Dream Team — Claude Code (Fable 5) × ChatGPT (GPT Sol 5.6)

> **The new AI dream team.** Zwei KI-Modelle verbinden sich zu einem Team:
> Claude Fable 5 (Anthropic) baut, GPT Sol 5.6 (OpenAI) reviewt — gemeinsam
> liefern sie ein besseres Ergebnis als jedes Modell allein.

## Installation

```bash
cd dream-team
pip install -r requirements.txt
```

## API-Keys setzen

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

(Vorlage: `.env.example`)

## Benutzung

### Frage vom Team beantworten lassen

Beide Modelle diskutieren die Frage, dann liefert Claude das konsolidierte
Team-Ergebnis:

```bash
python dream_team.py ask "Wie strukturiere ich eine skalierbare REST-API?"
python dream_team.py -r 2 ask "..."   # 2 Diskussionsrunden
```

### Code im Team entwickeln

Claude schreibt den Code, GPT macht das Code-Review, Claude verbessert:

```bash
python dream_team.py code "Ein CLI-Tool, das CSV-Dateien zusammenfuehrt"
python dream_team.py -r 3 code "..."  # 3 Review-Runden
```

### Interaktiver Team-Chat

Du schreibst, beide Modelle antworten dir nacheinander (GPT sieht Claudes
Antwort und ergaenzt/korrigiert):

```bash
python dream_team.py chat
```

### Demo ohne API-Keys

```bash
python dream_team.py --mock ask "Testfrage"
```

## Konfiguration

| Variable | Default | Beschreibung |
|---|---|---|
| `DREAMTEAM_CLAUDE_MODEL` | `claude-fable-5` | Anthropic-Modell |
| `DREAMTEAM_CLAUDE_FALLBACK` | `claude-opus-4-8` | Fallback bei Safety-Refusal |
| `DREAMTEAM_OPENAI_MODEL` | `gpt-5.6` | OpenAI-Modell — anpassen, falls dein Modell z.B. `gpt-sol-5.6` heisst |
| `DREAMTEAM_MAX_TOKENS` | `16000` | Max. Output-Tokens pro Claude-Antwort |
| `DREAMTEAM_MOCK` | — | `1` = Demo-Modus ohne Keys |

## Wie es funktioniert

Beide Modelle teilen sich ein gemeinsames Team-Transcript. Jedes Modell sieht
die Beitraege des Partners als markierte Nachrichten (`[Claude (Fable 5)]: …`,
`[GPT Sol 5.6]: …`) und baut darauf auf, statt zu wiederholen.

- **Claude Fable 5** laeuft mit immer aktivem Adaptive Thinking und einem
  serverseitigen Refusal-Fallback auf Opus 4.8, damit der Team-Loop bei einem
  Safety-Decline nicht abbricht.
- **GPT Sol 5.6** wird ueber die OpenAI Chat Completions API angebunden.

## Rollen

| Modell | Rolle |
|---|---|
| 🟧 Claude (Fable 5) | Builder & Architekt — entwirft, implementiert, konsolidiert |
| ⬜ GPT Sol 5.6 | Reviewer & Sparringspartner — prueft, findet Luecken, verbessert |
