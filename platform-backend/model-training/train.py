#!/usr/bin/env python3
"""LoRA/QLoRA-Fine-Tuning fuer ein wirklich eigenes, lokales Modell.

Basismodell (Default): Qwen/Qwen2.5-7B-Instruct (Apache-2.0, siehe README.md
in diesem Ordner fuer die Lizenz- und Hardware-Begruendung).

Dieses Skript erzeugt ECHTE, NEUE Gewichte (einen LoRA-Adapter) auf Basis
eines offenen Modells -- kein Pretraining von Grund auf, kein neuer
Modell-Fantasiename, keine Behauptung von Frontier-Qualitaet. Siehe
model-training/README.md fuer die ehrlichen Grenzen und den Weg vom Adapter
zum einsatzbereiten, im Gateway registrierten Modell.

Bibliotheken (Versionen, gegen die dieses Skript geschrieben und per Import-
/Signatur-Check verifiziert wurde -- siehe README.md "Was verifiziert wurde"):
    transformers==5.14.1
    peft==0.19.1
    trl==1.9.1
    bitsandbytes==0.50.0
    accelerate==1.14.0
    datasets==5.0.0

Nutzung (Beispiel, auf einer echten GPU -- siehe README.md fuer Hardware-
Anforderung, in dieser Sandbox NICHT ausfuehrbar mangels GPU):

    python train.py \
        --base_model Qwen/Qwen2.5-7B-Instruct \
        --dataset_path data/example_dataset.jsonl \
        --output_dir output/lora-adapter \
        --num_train_epochs 3

Fuer einen reinen CPU-Smoke-Test des Codepfads (kleines Modell, wenige
Schritte, KEIN echtes Fine-Tuning-Ergebnis, nur ein Beweis, dass Trainer/
Datenformat/Speichern funktionieren) siehe scripts/smoke_test.sh.
"""
from __future__ import annotations

import argparse
import sys

import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

DEFAULT_BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# Alle Projektionsmatrizen (Attention + MLP) -- bessere Adapter-Qualitaet als
# nur q_proj/v_proj, bei 7B/QLoRA immer noch klein genug fuer eine 24 GB GPU.
DEFAULT_TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base_model", default=DEFAULT_BASE_MODEL,
                   help=f"HF-Modell-ID des Basismodells (Default: {DEFAULT_BASE_MODEL}).")
    p.add_argument("--dataset_path", default="data/example_dataset.jsonl",
                   help="JSONL-Datei im TRL-Conversational-Format ({'messages': [...]}).")
    p.add_argument("--output_dir", default="output/lora-adapter",
                   help="Zielordner fuer LoRA-Adapter + Tokenizer.")

    # --- LoRA-Hyperparameter ---
    p.add_argument("--lora_r", type=int, default=16, help="LoRA-Rang.")
    p.add_argument("--lora_alpha", type=int, default=32, help="LoRA-Skalierung (Faustregel: 2x r).")
    p.add_argument("--lora_dropout", type=float, default=0.05)
    p.add_argument("--target_modules", nargs="+", default=DEFAULT_TARGET_MODULES)

    # --- Trainings-Hyperparameter ---
    p.add_argument("--learning_rate", type=float, default=2e-4,
                   help="LoRA/QLoRA braucht typischerweise ~10x die Lernrate von vollem Fine-Tuning.")
    p.add_argument("--num_train_epochs", type=float, default=3.0)
    p.add_argument("--max_steps", type=int, default=-1,
                   help="Wenn > 0, ueberschreibt num_train_epochs (nuetzlich fuer Smoke-Tests).")
    p.add_argument("--per_device_train_batch_size", type=int, default=2)
    p.add_argument("--gradient_accumulation_steps", type=int, default=8)
    p.add_argument("--max_length", type=int, default=1024,
                   help="Maximale Tokenlaenge pro Beispiel (Truncation danach).")
    p.add_argument("--logging_steps", type=int, default=5)
    p.add_argument("--seed", type=int, default=42)

    # --- Quantisierung ---
    p.add_argument("--no_quantization", action="store_true",
                   help=("Deaktiviert 4-bit-QLoRA-Quantisierung (BitsAndBytesConfig). "
                         "Nur fuer CPU-Smoke-Tests oder wenn genug VRAM fuer normales "
                         "LoRA in bf16 vorhanden ist -- bitsandbytes-4-bit braucht eine "
                         "CUDA-GPU, in dieser Sandbox generell nicht verfuegbar."))
    p.add_argument("--assistant_only_loss", action="store_true", default=True,
                   help=("Loss nur auf Assistant-Antworten, nicht auf System/User-Turns. "
                         "Braucht ein Chat-Template mit {%% generation %%}-Markern; TRL "
                         "patcht das fuer bekannte Modellfamilien (u.a. Qwen2.5) automatisch."))
    p.add_argument("--no_assistant_only_loss", dest="assistant_only_loss", action="store_false")

    return p


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    torch.manual_seed(args.seed)

    print(f"[train.py] Basismodell: {args.base_model}")
    print(f"[train.py] Dataset:     {args.dataset_path}")
    print(f"[train.py] QLoRA (4-bit): {not args.no_quantization}")

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        # Viele Base-/Instruct-Modelle definieren keinen eigenen Pad-Token.
        tokenizer.pad_token = tokenizer.eos_token

    dataset = load_dataset("json", data_files=args.dataset_path, split="train")
    print(f"[train.py] Trainingsbeispiele: {len(dataset)}")

    quantization_config = None
    if not args.no_quantization:
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=args.target_modules,
    )

    has_cuda = torch.cuda.is_available()
    training_args = SFTConfig(
        output_dir=args.output_dir,
        num_train_epochs=args.num_train_epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.per_device_train_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        max_length=args.max_length,
        logging_steps=args.logging_steps,
        save_strategy="epoch",
        bf16=has_cuda,  # auf CPU (Smoke-Test) bleibt das aus -- bf16-Matmul auf CPU ist unnoetig langsam/instabil
        gradient_checkpointing=has_cuda,
        model_init_kwargs={"dtype": torch.bfloat16 if has_cuda else torch.float32},
        assistant_only_loss=args.assistant_only_loss,
        report_to="none",
        seed=args.seed,
    )

    trainer = SFTTrainer(
        model=args.base_model,
        args=training_args,
        train_dataset=dataset,
        peft_config=peft_config,
        quantization_config=quantization_config,
        processing_class=tokenizer,
    )

    trainer.train()

    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"[train.py] LoRA-Adapter gespeichert unter: {args.output_dir}")
    print("[train.py] Naechster Schritt: merge_and_export.py (siehe README.md, Abschnitt "
          "'Vom Adapter zum Gateway-Modell').")


if __name__ == "__main__":
    sys.exit(main() or 0)
