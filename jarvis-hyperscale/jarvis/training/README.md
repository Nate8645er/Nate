# JARVIS Trainings-Pipeline

Echte, lauffähige Pipeline, um aus JARVIS' **tatsächlichen** Interaktionsdaten
einen Fine-Tuning-Datensatz zu bauen, ihn zu analysieren und zu evaluieren.
Reine Standardbibliothek — keine schweren Abhängigkeiten nötig.

## Ablauf

```bash
# 1) Datensatz aus Gedächtnis + Autopilot-Ideen bauen (mit PII-Bereinigung)
python -m jarvis.training.build_dataset --data <JARVIS_DATA> --out dataset.jsonl

# 2) Token-/Längen-Statistik (für Hyperparameter)
python -m jarvis.training.tokenize_stats --in dataset.jsonl

# 3) Evaluation im Code: split() + evaluate_live() (siehe evaluate.py)
```

Der Datensatz ist im **Chat-JSONL-Format** (eine Zeile pro Beispiel mit
`messages`) — direkt nutzbar für:
- **API-Fine-Tuning** (OpenAI/kompatible Anbieter erwarten genau dieses Format),
- **lokales Fine-Tuning** (HuggingFace `transformers`/`trl`).

## Bausteine
| Datei | Aufgabe |
|------|--------|
| `scrub.py` | PII-Bereinigung (E-Mail, Key, Karte, IP, Telefon) |
| `build_dataset.py` | Gedächtnis + Ideen → Chat-JSONL, filtert Offline/Fehler |
| `tokenize_stats.py` | echte Token-Statistik (tiktoken) oder Wort-Schätzung |
| `evaluate.py` | deterministischer Holdout-Split + Wort-F1-Eval |

## Ehrliche Grenzen (wichtig)
- **Volles lokales Gewicht-Training** (Modell wirklich neu/weitertrainieren)
  braucht **GPU + torch/transformers** und ist hier NICHT enthalten — das wäre
  ein separater, schwergewichtiger Schritt. Diese Pipeline bereitet alles dafür
  vor (Daten, Format, Statistik), behauptet aber nicht, das Training selbst
  auszuführen.
- Die **PII-Bereinigung** ist konservativ, aber **keine Garantie** — prüfe den
  Datensatz vor jeder Weitergabe.
- Die **Eval-Metrik** ist eine einfache Wortüberlappung (F1), kein semantisches
  Maß. Sie zeigt Tendenzen, ersetzt keine gründliche Bewertung.
- Ohne echten API-Key entstehen **keine** Trainingsdaten (JARVIS muss erst mit
  Modell laufen). Der Builder meldet das ehrlich, statt leere Zahlen zu liefern.
