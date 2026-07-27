# Model-Training — eine echte Fine-Tuning-Pipeline fuer ein eigenes Modell

Dieser Ordner ist **getrennt** von `app/`, `static/`, `tests/` (kein
Ueberschneidungsrisiko mit anderen laufenden Aenderungen) und liefert eine
lauffaehige, aber in dieser Sandbox **nicht ausgefuehrte** LoRA/QLoRA-
Fine-Tuning-Pipeline: aus einem offenen Basismodell + eigenen Trainingsdaten
entstehen echte, neue Modellgewichte, die am Ende als lokales Modell im
LiteLLM-Gateway dieser Plattform registriert werden koennen.

## 0. Ehrlich zuerst: was das hier ist — und was nicht

**Ist:**
- Echtes Fine-Tuning (LoRA bzw. QLoRA) eines offen lizenzierten Basismodells
  mit eigenen Daten. Das Ergebnis sind **neue, tatsaechlich veraenderte
  Gewichte** (ein LoRA-Adapter, optional ins Basismodell gemergt) — kein
  Reverse-Proxy und kein neuer Anzeigename fuer ein fremdes Modell.
- Ein realer Weg vom Adapter zu einem in Ollama lauffaehigen, im Gateway
  registrierten, **lokalen** Modell.

**Ist NICHT:**
- Kein Pretraining von Grund auf. Das Basismodell (Qwen2.5-7B-Instruct)
  wurde von Alibaba/Qwen auf Billionen Token trainiert — diese Pipeline
  passt es an, sie erschafft kein neues Sprachverstaendnis von null.
- Keine Konkurrenzfaehigkeit zu Frontier-Modellen (GPT/Claude/Gemini) zu
  erwarten. Ein 7B-LoRA-Fine-Tune ist gut fuer eng umrissene Aufgaben
  (hier: Support-Antworten ueber diese eine Plattform), nicht fuer
  allgemeines Reasoning auf Frontier-Niveau.
- Kein hier tatsaechlich durchgefuehrter Trainingslauf des Zielmodells
  Qwen2.5-7B-Instruct: **diese Sandbox hat keine GPU** (`nvidia-smi` liefert
  "command not found", `torch.cuda.is_available()` liefert `False`). Es
  wurde bewusst **nicht** vorgetaeuscht, dass hier ein 7B-Modell trainiert
  wurde. Was tatsaechlich verifiziert wurde, steht in Abschnitt 6.

## 1. Basismodell-Wahl: Qwen2.5-7B-Instruct

| Kriterium | Befund |
|---|---|
| Lizenz | **Apache License 2.0** — vollstaendiger Standardtext in `LICENSE` des HF-Repos (`Qwen/Qwen2.5-7B-Instruct`), Copyright Alibaba Cloud. Keine Nutzungsschwellen, keine Sonderklausel fuer kommerzielle Nutzung, keine Namensauflage. Verifiziert per direktem Abruf der LICENSE-Datei (siehe Quellen unten). |
| Groesse | 7.61B Parameter gesamt (6.53B ohne Embeddings), 28 Layer — passt mit QLoRA (4-bit) auf eine einzelne 24-GB-Consumer-/Cloud-GPU (z.B. RTX 4090, RTX 3090, A10G). |
| Kontext | 131072 Token Input, bis 8192 Token Output. |
| Sprache | Explizit mehrsprachig (u.a. Deutsch, Englisch, Franzoesisch) — passt zur Zielgruppe dieser Plattform (CHF-Preise, deutschsprachige UI/Rechtstexte). |
| Qualitaet | Aktuelles, breit genutztes Instruct-Modell seiner Groessenklasse mit ausgereiftem Chat-Template (ChatML) und guter Tooling-Unterstuetzung in `transformers`/`peft`/`trl`. |

**Verworfene Kandidaten** (recherchiert, nicht geraten):

- **Llama-3.1-8B-Instruct** — Meta **Llama 3.1 Community License**, kein
  Apache/MIT: enthaelt eine 700-Millionen-MAU-Schwelle (ab der eine separate
  Lizenz von Meta noetig wird), eine Acceptable-Use-Policy und die Auflage,
  Produkte mit "Llama" zu kennzeichnen. Fuer diese Plattform aktuell
  praktisch folgenlos (weit unter 700M MAU), aber **nicht so bedingungslos
  permissiv** wie Apache 2.0 — deshalb nicht die erste Wahl, wenn ein
  gleichwertiger Apache-2.0-Kandidat verfuegbar ist.
- **Mistral-7B-Instruct-v0.3** — ebenfalls **Apache 2.0**, also lizenzrechtlich
  gleichwertig zu Qwen2.5-7B-Instruct. Nicht gewaehlt, weil Qwen2.5 explizit
  bessere/breitere mehrsprachige Abdeckung (inkl. Deutsch) in der eigenen
  Modellkarte ausweist und in `trl` bereits ein spezifisches, getestetes
  Trainings-Chat-Template mitbringt (siehe Abschnitt 3) — beide waeren aber
  eine legitime Wahl gewesen.

**Quellen** (per WebFetch/WebSearch am 2026-07-27 direkt gegen Hugging Face
gegengeprueft, nicht aus dem Gedaechtnis behauptet):
- https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/main/LICENSE (Apache-2.0-Volltext)
- https://huggingface.co/Qwen/Qwen2.5-7B-Instruct (Modellkarte: Parameter, Kontext, Sprachen)
- https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3 (Apache-2.0)
- https://www.llama.com/llama3_1/license/ (Llama 3.1 Community License, MAU-Klausel)

## 2. Dataset-Format

TRL/`SFTTrainer` unterstuetzt mehrere Formate nativ; hier verwendet: das
**conversational** Format (eine Zeile JSONL = ein Trainingsbeispiel):

```json
{"messages": [
  {"role": "system", "content": "..."},
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": "..."}
]}
```

`SFTTrainer` erkennt dieses Format automatisch, wendet das Chat-Template des
Tokenizers an und tokenisiert. Mit `assistant_only_loss=True` (Default in
`train.py`) wird der Trainings-Loss **nur** auf den Assistant-Antworten
berechnet, nicht auf System-/User-Text — das Modell lernt zu antworten,
nicht Fragen zu "vervollstaendigen". Das braucht ein Chat-Template mit
`{% generation %}`/`{% endgeneration %}`-Markern; `trl` 1.9.1 bringt dafuer
ein gepatchtes Trainings-Template exakt fuer Qwen2.5-Instructs
Standard-ChatML-Template mit (`trl/chat_templates/qwen2_5_training.jinja`,
per String-Vergleich gegen `tokenizer.chat_template` automatisch aktiviert
— im installierten Paket nachgelesen, siehe Abschnitt 6).

## 3. Beispieldatensatz

`data/example_dataset.jsonl` — **24 Zeilen**, echte Frage-Antwort-Paare
**aus dieser Plattform selbst**, nicht erfunden:

- Herkunft: `platform-backend/README.md` (Architektur, RLS/`app_rw`,
  Endpunkte, Rate-Limiting, Streaming, `web_fetch`-Tool, Stripe-Webhooks),
  `store/sections/faq.liquid` (Kuendigung, Tarifwechsel, kein eigener
  API-Key noetig, Free-Tarif), `migrations/002_seed_plans.sql` und
  `migrations/008_openrouter_plans.sql` (Tarif-Inhalte: Preise in CHF,
  Token-Limits, freigeschaltete Modelle).
- Jede Antwort ist mit einer echten Stelle im Repo belegbar — keine
  erfundenen Firmendaten, keine erfundenen Zahlen.
- 24 Beispiele sind fuer ein produktionsreifes Fine-Tuning **zu wenig**
  (siehe Abschnitt 5, "Grenzen") — das ist bewusst ein **Startpunkt**, kein
  fertiger Trainingsdatensatz. Realistisch braucht ein spuerbarer,
  stabiler Effekt eher 200-2000+ qualitativ saubere Beispiele, je nach
  gewuenschter Verhaltensaenderung.

Eigene Erweiterung: gleiche JSONL-Struktur fortsetzen, pro Zeile ein
`messages`-Array. Bei sehr grossen Datensaetzen ist `datasets.load_dataset`
mit `streaming=True` moeglich (in `train.py` nicht aktiviert, da fuer die
Groessenordnung hier nicht noetig).

## 4. Training ausfuehren (`train.py`)

```bash
pip install -r requirements.txt
# + torch fuer die eigene CUDA-Version, siehe requirements.txt-Kommentar

python train.py \
    --base_model Qwen/Qwen2.5-7B-Instruct \
    --dataset_path data/example_dataset.jsonl \
    --output_dir output/lora-adapter \
    --num_train_epochs 3
```

Kernstueck (QLoRA: 4-bit-Basis + LoRA-Adapter in hoeherer Praezision):

```python
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
peft_config = LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05,
    bias="none", task_type="CAUSAL_LM",
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
)
trainer = SFTTrainer(
    model="Qwen/Qwen2.5-7B-Instruct",
    args=SFTConfig(learning_rate=2e-4, assistant_only_loss=True, ...),
    train_dataset=dataset,
    peft_config=peft_config,
    quantization_config=quantization_config,
    processing_class=tokenizer,
)
trainer.train()
```

Wichtige Stellschrauben in `train.py` (alle als CLI-Flags):
- `--lora_r`/`--lora_alpha`: LoRA-Rang/Skalierung. 16/32 ist ein solider
  Default; hoeherer Rang = mehr trainierbare Parameter, mehr VRAM, potenziell
  bessere Anpassung.
- `--no_quantization`: deaktiviert QLoRA (4-bit). Nur sinnvoll auf einer GPU
  mit sehr viel VRAM (ungequantisiertes 7B-LoRA braucht deutlich mehr
  Speicher) oder fuer CPU-Smoke-Tests (siehe Abschnitt 6) — bitsandbytes-
  4-bit-Kernels brauchen eine CUDA-GPU.
- `--assistant_only_loss` (Default an): Loss nur auf Assistant-Turns.

## 5. Vom Adapter zum Gateway-Modell

Schritt fuer Schritt, nach `train.py`:

1. **Merge**: `merge_and_export.py` laedt Basismodell + Adapter und ruft
   `peft`s `PeftModel.merge_and_unload()` auf — das faltet die LoRA-Delta-
   Gewichte in die Original-Gewichte ein und liefert ein eigenstaendiges
   `transformers`-Modell (kein `peft` mehr zur Laufzeit noetig):

   ```bash
   python merge_and_export.py \
       --base_model Qwen/Qwen2.5-7B-Instruct \
       --adapter_dir output/lora-adapter \
       --output_dir output/merged-model
   ```

2. **GGUF-Konvertierung + Quantisierung** (fuer Ollama/`llama.cpp`), siehe
   `scripts/export_to_ollama.sh`:

   ```bash
   python3 llama.cpp/convert_hf_to_gguf.py output/merged-model \
       --outtype f16 --outfile output/merged-model/model-f16.gguf
   llama.cpp/build/bin/llama-quantize \
       output/merged-model/model-f16.gguf \
       output/merged-model/model-q4_k_m.gguf q4_K_M
   ```

3. **Ollama-Modell anlegen**, siehe `Modelfile.example`:

   ```bash
   ollama create firmenname-support-modell -f Modelfile
   ollama run firmenname-support-modell
   ```

   `scripts/export_to_ollama.sh` fuehrt Schritte 2+3 automatisiert aus (nicht
   in dieser Sandbox ausgefuehrt — braucht `llama.cpp`-Build + `ollama`-CLI).

4. **Registrierung im LiteLLM-Gateway** (`litellm/config.yaml`), analog zum
   bestehenden `ollama/llama3.2`-Eintrag:

   ```yaml
     - model_name: ollama/firmenname-support-modell
       litellm_params:
         model: ollama/firmenname-support-modell
         api_base: os.environ/OLLAMA_BASE_URL
   ```

5. **Registrierung im Backend-Katalog** (`app/models_catalog.py`), analog
   zum bestehenden lokalen Eintrag:

   ```python
   {"id": "ollama/firmenname-support-modell", "label": "Firmenname Support-Modell (lokal, fine-tuned)",
    "provider": "ollama", "local": True},
   ```

   **Wichtig zum Label**: `"firmenname-support-modell"` ist ein Platzhalter.
   Hier gehoert der echte, eigene Firmen-/Produktname hin (aus den
   Theme-Einstellungen von `store/config/settings_schema.json`, sobald dort
   echte Firmendaten eingetragen sind) — **kein** Fantasiename, der wie ein
   Konkurrenzprodukt klingt (kein "GPT"/"Claude"/"Gemini" im Namen, siehe
   die bestehende Regel in `app/models_catalog.py`). Dieser Ordner erfindet
   bewusst **keinen** Firmennamen, weil `store/README.md` explizit sagt,
   dass hier noch keine echten Firmendaten hinterlegt sind
   ("[Platzhalter]", bis das im Theme-Editor ausgefuellt wird).

6. Danach ist `ollama/firmenname-support-modell` fuer Tarife freischaltbar
   wie jedes andere Modell (`allowed_models` in `migrations/002_seed_plans.sql`
   / `008_openrouter_plans.sql`).

## 6. Was verifiziert wurde — und was nicht

**Verifiziert** (echte Installation + echte Imports in einer frischen
virtuellen Umgebung, Netzwerkzugriff auf PyPI und Hugging Face war in dieser
Sandbox vorhanden):

- `pip install torch transformers==5.14.1 peft==0.19.1 trl==1.9.1
  bitsandbytes==0.50.0 accelerate==1.14.0 datasets==5.0.0` — erfolgreich.
- Alle in `train.py`/`merge_and_export.py` verwendeten Klassen/Funktionen
  existieren tatsaechlich mit den verwendeten Parametern: `trl.SFTTrainer`,
  `trl.SFTConfig` (inkl. `dataset_text_field`, `max_length`, `packing`,
  `assistant_only_loss`, `model_init_kwargs`), `peft.LoraConfig` (`r`,
  `lora_alpha`, `lora_dropout`, `bias`, `task_type`, `target_modules`),
  `transformers.BitsAndBytesConfig` (`load_in_4bit`, `bnb_4bit_quant_type`,
  `bnb_4bit_compute_dtype`, `bnb_4bit_use_double_quant`), `peft.PeftModel`
  (inkl. `merge_and_unload()`, per Attribut-Delegation an `BaseTuner` — im
  installierten Quellcode `peft/tuners/tuners_utils.py` nachgelesen).
- **Echter CPU-Smoke-Test des tatsaechlichen `train.py`-Skripts** (nicht nur
  Import-Check): `python train.py --base_model Qwen/Qwen2.5-0.5B-Instruct
  --no_quantization --max_steps 2 ...` gegen `data/example_dataset.jsonl` —
  ein **viel kleineres** Modell derselben Familie (0.5B statt 7B, ohne
  4-bit-Quantisierung, da bitsandbytes-4-bit-Kernels eine CUDA-GPU brauchen),
  nur um den Code-Pfad (Datenladen, Tokenisierung/Chat-Template,
  `SFTTrainer`-Aufbau, `trainer.train()`, `trainer.save_model()`) real
  auszufuehren. Tatsaechliches Ergebnis dieses Laufs (2 Optimierungsschritte,
  24 Beispiele, `--no_quantization`, CPU): Loss fiel von `4.307` (Schritt 1)
  auf `3.061` (Schritt 2), `train_runtime` 8.16s, Adapter wurde als
  `adapter_model.safetensors` (~35 MB, plausibel fuer einen LoRA-Adapter auf
  einem 0.5B-Modell) + `adapter_config.json` gespeichert. Diese zwei Schritte
  sind **kein aussagekraeftiges Trainingsergebnis** (viel zu wenige Schritte,
  falsches/zu kleines Modell) — sie beweisen ausschliesslich, dass der
  Code-Pfad fehlerfrei durchlaeuft, nicht dass das Fine-Tuning-Ergebnis gut
  ist.
- Anschliessend **`merge_and_export.py` gegen genau diesen Adapter real
  ausgefuehrt**: `PeftModel.from_pretrained(...)` + `merge_and_unload()` +
  `save_pretrained()` liefen fehlerfrei durch und erzeugten ein
  eigenstaendiges HF-Modellverzeichnis (`model.safetensors`, ca. 1.98 GB in
  float32 fuer das 0.5B-Modell) — der komplette Codepfad Training -> Merge
  ist damit einmal end-to-end real durchlaufen, nur eben mit einem viel
  kleineren Stellvertreter-Modell statt Qwen2.5-7B-Instruct.
- `Qwen/Qwen2.5-7B-Instruct/LICENSE` real abgerufen: Apache-2.0-Volltext.
- Llama-3.1-Lizenztext uebers offizielle `llama.com`-Dokument abgerufen
  (MAU-Klausel, Acceptable-Use-Policy).
- `llama.cpp`s Konvertierungs-Skriptname (`convert_hf_to_gguf.py`,
  `--outtype`) und Ollamas `Modelfile`-Syntax (`FROM`, `ADAPTER`, `ollama
  create --quantize`) gegen die aktuelle offizielle Dokumentation geprueft.

**Nicht verifiziert / nicht moeglich in dieser Sandbox**:

- **Kein echter QLoRA-Trainingslauf von Qwen2.5-7B-Instruct** — keine GPU
  vorhanden (`torch.cuda.is_available()` == `False`, `nvidia-smi` nicht
  installiert). Der 0.5B-CPU-Smoke-Test oben beweist, dass der Code-Pfad
  funktioniert, **nicht**, dass das 7B-Fine-Tuning inhaltlich gute Ergebnisse
  liefert — das kann nur ein echter Lauf auf echter Hardware zeigen.
- Keine `llama.cpp`-Konvertierung, keine `ollama create`-Ausfuehrung
  durchgefuehrt (kein `llama.cpp`-Checkout, kein Ollama in dieser Sandbox
  installiert) — die Befehle in `scripts/export_to_ollama.sh` sind gegen die
  offizielle Dokumentation geprueft, aber nicht End-to-End hier gelaufen.
- Keine Trainingsmetriken, Loss-Kurven oder Qualitaetsvergleiche — es gibt
  keinen echten Trainingslauf des Zielmodells, also auch keine echten Zahlen
  dazu. Jede hier behauptete Metrik waere erfunden; deshalb steht keine da.

## 7. Hardware- und Kostenrealitaet (Schaetzung, keine Werbezahlen)

- **Minimum fuer QLoRA auf Qwen2.5-7B-Instruct**: eine einzelne GPU mit
  **mindestens ~16 GB VRAM** (knapp, mit kleiner Batchgroesse/Gradient-
  Accumulation), **komfortabel ab 24 GB VRAM** (RTX 3090/4090, A10G, L4).
  Vollstaendiges (nicht-quantisiertes) LoRA oder gar volles Fine-Tuning
  braucht deutlich mehr (~40-80 GB VRAM je nach Setup).
- **Dauer/Kosten (grobe Schaetzung, KEINE gemessene Zahl)**: fuer einen
  Datensatz in der Groessenordnung von ein paar Tausend Beispielen und 2-3
  Epochen auf einer gemieteten 24-GB-GPU (z.B. RTX 4090 bei einem
  Cloud-GPU-Anbieter, Richtwert ca. 0.40-0.70 USD/Stunde je nach Anbieter/
  Zeitpunkt): typischerweise **im Bereich von 30-90 Minuten Trainingszeit**,
  also **grob 0.50-3 USD reine Rechenkosten** fuer einen Lauf dieser
  Groessenordnung. Bei deutlich groesseren Datensaetzen (zehntausende
  Beispiele, mehr Epochen) skaliert das entsprechend auf mehrere Stunden.
  **Diese Zahl ist eine Schaetzung zur Groessenordnung, keine Zusage** — der
  tatsaechliche Wert haengt an Datensatzgroesse, Sequenzlaenge, Anbieter-
  Preisen und Konfiguration und wurde in dieser Sandbox nicht gemessen (es
  gab keinen echten Lauf).

## 8. Dateien in diesem Ordner

```
model-training/
  README.md                    Diese Datei
  requirements.txt             Pipeline-Abhaengigkeiten (getrennt vom Backend)
  train.py                     LoRA/QLoRA-SFT-Training (trl.SFTTrainer)
  merge_and_export.py          LoRA-Adapter -> eigenstaendiges HF-Modell (merge_and_unload)
  Modelfile.example            Ollama-Modelfile-Vorlage (ChatML-Template)
  scripts/
    export_to_ollama.sh        GGUF-Konvertierung + Quantisierung + ollama create
  data/
    example_dataset.jsonl      24 echte Q&A-Paare aus README/FAQ/Tarifen dieser Plattform
```
