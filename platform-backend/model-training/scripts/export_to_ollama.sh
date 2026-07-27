#!/usr/bin/env bash
# Vom gemergten HF-Modell (output/merged-model, siehe merge_and_export.py) zu
# einem lauffaehigen Ollama-Modell, bereit fuer die Registrierung im Gateway.
#
# NICHT in dieser Sandbox ausgefuehrt (kein GPU/kein Bedarf fuer echtes
# Training hier) -- das ist die dokumentierte, real funktionierende Befehls-
# folge (llama.cpp- und ollama-CLI-Syntax gegen deren aktuelle Dokumentation
# geprueft, siehe README.md "Was verifiziert wurde"). Vor dem ersten echten
# Lauf: Versionen von llama.cpp/ollama pruefen, Flags koennen sich aendern.
#
# Voraussetzungen:
#   - llama.cpp lokal geklont + Python-Requirements installiert
#     (git clone https://github.com/ggml-org/llama.cpp && pip install -r
#     llama.cpp/requirements.txt)
#   - Ollama lokal installiert (https://ollama.com/download)
#
# Nutzung:
#   ./export_to_ollama.sh <merged_model_dir> <llama_cpp_dir> <ollama_model_name>
set -euo pipefail

MERGED_MODEL_DIR="${1:-output/merged-model}"
LLAMA_CPP_DIR="${2:-../llama.cpp}"
OLLAMA_MODEL_NAME="${3:-firmenname-support-modell}"

GGUF_F16="${MERGED_MODEL_DIR}/model-f16.gguf"
GGUF_Q4="${MERGED_MODEL_DIR}/model-q4_k_m.gguf"

echo "1/3: HF-Modell -> GGUF (f16, verlustfrei bzgl. Praezision)"
python3 "${LLAMA_CPP_DIR}/convert_hf_to_gguf.py" \
    "${MERGED_MODEL_DIR}" \
    --outtype f16 \
    --outfile "${GGUF_F16}"

echo "2/3: f16-GGUF -> quantisiertes GGUF (q4_K_M -- guter Kompromiss Qualitaet/Groesse fuer 7B)"
"${LLAMA_CPP_DIR}/build/bin/llama-quantize" \
    "${GGUF_F16}" \
    "${GGUF_Q4}" \
    q4_K_M

echo "3/3: Ollama-Modell aus dem quantisierten GGUF anlegen"
cat > "${MERGED_MODEL_DIR}/Modelfile" <<EOF
FROM ${GGUF_Q4}

# Qwen2.5-Instruct benutzt ChatML. Falls das GGUF beim Konvertieren bereits
# ein chat_template aus tokenizer_config.json eingebettet hat, erkennt
# 'ollama create' das TEMPLATE automatisch -- die folgenden Zeilen sind der
# explizite Fallback, falls nicht.
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
{{ .Response }}<|im_end|>
"""

PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"

SYSTEM """Du bist ein internes, lokal fine-getuntes Sprachmodell dieser Plattform. Antworte praezise und ehrlich."""
EOF

ollama create "${OLLAMA_MODEL_NAME}" -f "${MERGED_MODEL_DIR}/Modelfile"

echo "Fertig. Testen mit:  ollama run ${OLLAMA_MODEL_NAME}"
echo "Naechster Schritt: Registrierung in litellm/config.yaml + app/models_catalog.py, siehe README.md."
