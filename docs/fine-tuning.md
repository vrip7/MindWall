# Fine-Tuning

> Train a specialised MindWall manipulation detection model using QLoRA.

---

## Overview

MindWall includes a complete fine-tuning pipeline for training a specialised Qwen3-4B model on manipulation detection. The pipeline uses **QLoRA** (Quantized Low-Rank Adaptation) via [Unsloth](https://github.com/unslothai/unsloth) to achieve training on a single 8GB VRAM GPU.

**Base model:** `unsloth/Qwen3-4B-Instruct-2507-bnb-4bit`  
**Output:** GGUF quantized model importable into Ollama

---

## Pipeline Stages

```
1. Generate synthetic data     → datasets/raw/synthetic/
2. Download public corpora     → datasets/raw/
3. Prepare dataset             → datasets/processed/mindwall_train/
4. Train with QLoRA            → output/mindwall-lora/
5. Evaluate on test set        → metrics report
6. Export to GGUF              → output/mindwall-gguf/
7. Import into Ollama          → mindwall-qwen3-4b
```

---

## Step 1: Generate Synthetic Data

**Script:** `finetune/datasets/synthetic_generator.py`

Generates labelled training examples for all 12 manipulation dimensions.

```powershell
cd finetune
python datasets/synthetic_generator.py
```

- **Output:** 20,000 synthetic emails in `datasets/raw/synthetic/`
- **Format:** JSONL with email body, dimension labels, and manipulation scores
- **Templates:** 8+ templates per dimension with placeholder variables for:
  - `{amount}` — dollar amounts
  - `{minutes}` — time pressure values
  - `{ceo_name}` — authority figure names
  - `{project}` — project names
  - `{name1}`, `{name2}`, `{name3}` — colleague names
  - `{award}` — awards/honours
- **Batch size:** 500 emails per batch

The generator creates realistic email bodies spanning all 12 dimensions with ground-truth labels, ensuring balanced representation across manipulation types.

---

## Step 2: Download Public Corpora

**Scripts:** `finetune/datasets/download.sh` (Linux/macOS), `finetune/datasets/download.ps1` (Windows)

```powershell
cd finetune/datasets
.\download.ps1
```

Downloads public email datasets to `datasets/raw/`:
- **CEAS 2008** — Spam/phishing corpus (mbox format)
- **CSV corpora** — Additional labelled email datasets

These provide real-world email examples for training alongside the synthetic data.

---

## Step 3: Prepare Dataset

**Script:** `finetune/prepare_dataset.py`

```powershell
cd finetune
python prepare_dataset.py
```

Processes all raw data into the **Qwen3 ChatML format** used by the model:

```
<|im_start|>system
You are MindWall, a clinical-grade cybersecurity inference engine...
<|im_end|>
<|im_start|>user
Analyze the following email for psychological manipulation...
<|im_end|>
<|im_start|>assistant
{"dimension_scores": {...}, "explanation": "...", "recommended_action": "..."}
<|im_end|>
```

### Processing Steps

1. **Parse mbox corpora** — Extract emails from CEAS mbox files, label as "phishing"
2. **Parse CSV corpora** — Extract body and labels, truncate to 4,000 characters
3. **Parse synthetic data** — Already formatted, loaded directly
4. **Format as ChatML** — Wrap in `<|im_start|>` / `<|im_end|>` role tags
5. **Train/eval split** — 90% training, 10% evaluation (configurable via `train_split_ratio`)

### Output

- `datasets/processed/mindwall_train/` — Training set
- `datasets/processed/mindwall_eval/` — Evaluation set

---

## Step 4: Train

**Script:** `finetune/train.py`

```powershell
cd finetune
python train.py
```

### Configuration

All hyperparameters are in `finetune/configs/qlora_config.yaml`:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model_name` | `unsloth/Qwen3-4B-Instruct-2507-bnb-4bit` | 4-bit pre-quantized model |
| `max_seq_length` | 1024 | Maximum token sequence length |
| `load_in_4bit` | true | 4-bit quantization (NF4) |
| `lora_r` | 8 | LoRA rank (low-rank dimension) |
| `lora_alpha` | 16 | LoRA scaling factor (`alpha / r = 2.0`) |
| `lora_dropout` | 0 | No dropout (Unsloth recommendation) |
| `target_modules` | `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` | All attention + MLP layers |
| `gradient_checkpointing` | `"unsloth"` | 30% VRAM reduction |
| `per_device_train_batch_size` | 1 | Single sample per step |
| `gradient_accumulation_steps` | 16 | Effective batch size = 16 |
| `num_train_epochs` | 3 | Training epochs |
| `learning_rate` | 2e-4 | AdamW 8-bit learning rate |
| `lr_scheduler_type` | `cosine` | Cosine annealing schedule |
| `warmup_steps` | 100 | Linear warmup steps |
| `bf16` | true | BFloat16 precision (Ampere+ GPUs) |
| `optim` | `adamw_8bit` | 8-bit AdamW optimizer |

### Training Process

1. **Load model** — `FastLanguageModel.from_pretrained()` loads the 4-bit quantized model
2. **Apply LoRA** — `FastLanguageModel.get_peft_model()` attaches low-rank adapters to all target modules
3. **Monkey-patch CE loss** — Replaces Unsloth's fused CE loss with standard PyTorch CE loss (fixes 8GB GPU memory and label shape issues)
4. **Load dataset** — Reads processed ChatML data from `datasets/processed/`
5. **Train** — `SFTTrainer` with the configured hyperparameters
6. **Save** — LoRA adapter weights saved to `output/mindwall-lora/`

### VRAM Requirements

| Component | VRAM |
|-----------|------|
| Model (4-bit) | ~3 GB |
| LoRA adapters | ~0.2 GB |
| Activation checkpoints | ~1.5 GB |
| Optimizer states (8-bit) | ~1.5 GB |
| Batch + overhead | ~1.5 GB |
| **Total** | **~8 GB** |

---

## Step 5: Evaluate

**Script:** `finetune/evaluate.py`

```powershell
cd finetune
python evaluate.py
```

Evaluates the fine-tuned model against the held-out test set using:

| Metric | Description |
|--------|-------------|
| **MAE** | Mean Absolute Error per dimension (average score deviation) |
| **MSE** | Mean Squared Error per dimension |
| **Accuracy** | Classification accuracy (severity level matching) |
| **Classification Report** | Per-severity precision, recall, F1-score |
| **Confusion Matrix** | Severity prediction confusion matrix |

The evaluator runs inference on each test sample, parses the JSON response, and compares predicted dimension scores and severity against ground truth.

---

## Step 6: Export to GGUF

**Script:** `finetune/export.py`

```powershell
cd finetune
python export.py
```

### Process

1. **Merge LoRA** — Merge adapter weights back into the base model
2. **Convert to GGUF** — Using llama.cpp with configured quantization
3. **Create Ollama Modelfile** — Generates the import configuration

### Quantization

Default: `q4_k_m` (4-bit with medium quality k-quant)

Other options: `q4_0`, `q4_1`, `q5_0`, `q5_1`, `q5_k_m`, `q8_0`, `f16`

### Output

- `output/mindwall-gguf/` — GGUF model file
- `output/mindwall-gguf/Modelfile` — Ollama import file

### Ollama Modelfile

The generated Modelfile includes:

```
FROM ./mindwall-qwen3-4b.gguf
TEMPLATE """<|im_start|>system
{{ .System }}<|im_end|>
<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
"""
SYSTEM "You are MindWall, a cybersecurity analysis engine..."
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_predict 1024
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"
```

---

## Step 7: Import into Ollama

```powershell
# Copy the GGUF model and Modelfile to the Ollama container
docker compose exec ollama ollama create mindwall-qwen3-4b -f /root/.ollama/Modelfile
```

Or use the Makefile:
```bash
make load-model
```

Then update the MindWall API to use the fine-tuned model:
- Set `OLLAMA_MODEL=mindwall-qwen3-4b` in your `.env` or `docker-compose.yml`
- Restart the API: `docker compose restart api`

---

## Directory Structure

```
finetune/
├── train.py                    # QLoRA training script
├── prepare_dataset.py          # Dataset preparation + formatting
├── evaluate.py                 # Model evaluation + metrics
├── export.py                   # LoRA merge + GGUF export
├── requirements.txt            # Python dependencies
├── configs/
│   └── qlora_config.yaml       # All training hyperparameters
├── datasets/
│   ├── synthetic_generator.py  # Synthetic data generation
│   ├── download.sh             # Linux/macOS corpus download
│   ├── download.ps1            # Windows corpus download
│   ├── raw/                    # Raw downloaded/generated data
│   │   └── synthetic/          # Generated synthetic emails
│   └── processed/              # Formatted ChatML datasets
│       ├── mindwall_train/     # Training set
│       └── mindwall_eval/      # Evaluation set
├── output/
│   ├── mindwall-lora/          # LoRA adapter checkpoints
│   ├── mindwall-merged/        # Merged model (intermediate)
│   └── mindwall-gguf/          # Final GGUF model + Modelfile
└── unsloth_compiled_cache/     # Unsloth compiled trainer stubs
```
