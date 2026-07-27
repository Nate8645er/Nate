#!/usr/bin/env python3
"""Merged einen trainierten LoRA-Adapter in das Basismodell und schreibt ein
eigenstaendiges HF-Modellverzeichnis (fp16/bf16 safetensors) -- der naechste
Schritt nach train.py, vor der GGUF-Konvertierung fuer Ollama.

Warum ueberhaupt mergen (statt den Adapter live zu laden)?
    - llama.cpp/convert_hf_to_gguf.py erwartet ein vollstaendiges Modell,
      keinen PEFT-Adapter obendrauf.
    - Ein gemergtes Modell laeuft ohne die peft-Bibliothek zur Inferenzzeit --
      wichtig fuer den spaeteren Ollama/GGUF-Pfad, der ohnehin ausserhalb von
      Python laeuft.

Nutzung:
    python merge_and_export.py \
        --base_model Qwen/Qwen2.5-7B-Instruct \
        --adapter_dir output/lora-adapter \
        --output_dir output/merged-model

Hinweis: Dieser Schritt braucht das Basismodell noch einmal in voller
Praezision (bf16/fp16) im Arbeitsspeicher -- bei Qwen2.5-7B ca. 15 GB RAM/VRAM.
Er kann auf CPU laufen (langsamer, aber ohne QLoRA-Quantisierung problemlos
moeglich), anders als das eigentliche QLoRA-Training.
"""
from __future__ import annotations

import argparse

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base_model", default="Qwen/Qwen2.5-7B-Instruct")
    p.add_argument("--adapter_dir", default="output/lora-adapter",
                   help="Ausgabeverzeichnis von train.py (LoRA-Adapter + Tokenizer).")
    p.add_argument("--output_dir", default="output/merged-model",
                   help="Zielverzeichnis fuer das gemergte, eigenstaendige Modell.")
    p.add_argument("--dtype", choices=["bfloat16", "float16", "float32"], default="bfloat16")
    return p


def main() -> None:
    args = build_arg_parser().parse_args()
    dtype = getattr(torch, args.dtype)

    print(f"[merge_and_export.py] Lade Basismodell {args.base_model} in {args.dtype} ...")
    base_model = AutoModelForCausalLM.from_pretrained(args.base_model, dtype=dtype)
    tokenizer = AutoTokenizer.from_pretrained(args.adapter_dir)

    print(f"[merge_and_export.py] Lade LoRA-Adapter aus {args.adapter_dir} ...")
    merged = PeftModel.from_pretrained(base_model, args.adapter_dir)

    print("[merge_and_export.py] Merge (peft.PeftModel.merge_and_unload) ...")
    # merge_and_unload() faltet die LoRA-Delta-Gewichte (B @ A * scaling) in
    # die Original-Gewichte ein und gibt ein reines transformers-Modell
    # zurueck -- ab hier ist es kein PeftModel mehr, sondern ein
    # eigenstaendiges Modell mit echten, veraenderten Gewichten.
    merged = merged.merge_and_unload()

    print(f"[merge_and_export.py] Speichere gemergtes Modell nach {args.output_dir} ...")
    merged.save_pretrained(args.output_dir, safe_serialization=True)
    tokenizer.save_pretrained(args.output_dir)

    print("[merge_and_export.py] Fertig. Naechster Schritt: GGUF-Konvertierung, siehe "
          "scripts/export_to_ollama.sh bzw. README.md Abschnitt "
          "'Vom Adapter zum Gateway-Modell'.")


if __name__ == "__main__":
    main()
