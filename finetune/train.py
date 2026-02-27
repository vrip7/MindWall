"""
MindWall — QLoRA Fine-Tuning Script
Trains Llama 3.1 8B with Unsloth QLoRA on manipulation detection data.
Fits on 8GB VRAM GPU.
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
"""

import sys
import json
from pathlib import Path
from datetime import datetime

import yaml
import torch
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_from_disk

# ── Configuration ────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "configs" / "qlora_config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def main():
    config = load_config()

    print("=" * 60)
    print("  MindWall — QLoRA Fine-Tuning")
    print(f"  Model: {config['model_name']}")
    print(f"  Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB" if torch.cuda.is_available() else "")
    print("=" * 60)

    # ── 1. Load model with 4-bit quantization ────────────────────────────
    print("\n[1/5] Loading model with QLoRA 4-bit quantization...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config["model_name"],
        max_seq_length=config["max_seq_length"],
        dtype=config.get("dtype"),  # None = auto-detect
        load_in_4bit=config["load_in_4bit"],
    )

    # ── 2. Apply LoRA adapters ───────────────────────────────────────────
    print("[2/5] Applying LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=config["lora_r"],
        target_modules=config["target_modules"],
        lora_alpha=config["lora_alpha"],
        lora_dropout=config["lora_dropout"],
        bias=config["lora_bias"],
        use_gradient_checkpointing=config["use_gradient_checkpointing"],
        random_state=config["random_state"],
    )

    # Print trainable parameters
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Trainable: {trainable_params:,} / {total_params:,} ({100 * trainable_params / total_params:.2f}%)")

    # ── 3. Load dataset ──────────────────────────────────────────────────
    print("[3/5] Loading training dataset...")
    dataset_path = config["dataset_dir"]
    eval_dataset_path = config.get("eval_dataset_dir")

    train_dataset = load_from_disk(dataset_path)
    print(f"  Train samples: {len(train_dataset)}")

    eval_dataset = None
    if eval_dataset_path and Path(eval_dataset_path).exists():
        eval_dataset = load_from_disk(eval_dataset_path)
        print(f"  Eval samples: {len(eval_dataset)}")

    # ── 4. Configure and start training ──────────────────────────────────
    print("[4/5] Starting training...")
    output_dir = config["output_dir"]
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        per_device_train_batch_size=config["per_device_train_batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        warmup_steps=config["warmup_steps"],
        num_train_epochs=config["num_train_epochs"],
        learning_rate=config["learning_rate"],
        fp16=config["fp16"],
        bf16=config["bf16"],
        logging_steps=config["logging_steps"],
        optim=config["optim"],
        weight_decay=config["weight_decay"],
        lr_scheduler_type=config["lr_scheduler_type"],
        output_dir=output_dir,
        save_strategy=config["save_strategy"],
        eval_strategy=config.get("eval_strategy", "no"),
        per_device_eval_batch_size=config.get("per_device_eval_batch_size", 4),
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field=config["dataset_text_field"],
        max_seq_length=config["max_seq_length"],
        args=training_args,
    )

    # Train
    train_result = trainer.train()

    # Log metrics
    metrics = train_result.metrics
    metrics["train_samples"] = len(train_dataset)
    print(f"\n  Training complete!")
    print(f"  Loss: {metrics.get('train_loss', 'N/A')}")
    print(f"  Runtime: {metrics.get('train_runtime', 0):.0f}s")
    print(f"  Samples/sec: {metrics.get('train_samples_per_second', 0):.1f}")

    # Save training metrics
    metrics_path = Path(output_dir) / "train_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    # ── 5. Save and merge ────────────────────────────────────────────────
    print("[5/5] Saving merged model...")
    merged_dir = config["merged_output_dir"]
    Path(merged_dir).mkdir(parents=True, exist_ok=True)

    model.save_pretrained_merged(
        merged_dir,
        tokenizer,
        save_method="merged_16bit",
    )

    # Save LoRA adapter separately as well
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Save training info
    info = {
        "model_name": config["model_name"],
        "lora_r": config["lora_r"],
        "lora_alpha": config["lora_alpha"],
        "epochs": config["num_train_epochs"],
        "learning_rate": config["learning_rate"],
        "train_samples": len(train_dataset),
        "trainable_params": trainable_params,
        "total_params": total_params,
        "train_loss": metrics.get("train_loss"),
        "trained_at": datetime.utcnow().isoformat(),
        "developer": "Pradyumn Tandon | VRIP7",
    }
    with open(Path(output_dir) / "training_info.json", "w") as f:
        json.dump(info, f, indent=2)

    print(f"\n✅ Training complete!")
    print(f"  LoRA adapter: {output_dir}")
    print(f"  Merged model: {merged_dir}")
    print(f"\n  Next step: python export.py")


if __name__ == "__main__":
    main()
