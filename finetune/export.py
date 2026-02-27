"""
MindWall — Model Export Script
Merges LoRA weights and exports to GGUF format for Ollama deployment.
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
"""

import json
import subprocess
import sys
import shutil
from pathlib import Path
from datetime import datetime

import yaml

# ── Configuration ────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "configs" / "qlora_config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def create_modelfile(gguf_path: str, model_name: str, output_dir: Path) -> Path:
    """Create an Ollama Modelfile for importing the GGUF model."""
    modelfile_content = f"""# MindWall — Ollama Modelfile
# Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

FROM {gguf_path}

TEMPLATE \"\"\"<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{{{{ .System }}}}<|eot_id|><|start_header_id|>user<|end_header_id|>

{{{{ .Prompt }}}}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

\"\"\"

SYSTEM \"\"\"You are MindWall, a cybersecurity analysis engine specialized in detecting psychological manipulation tactics in business communications. You analyze emails and messages with clinical precision, identifying social engineering patterns used by attackers to manipulate recipients into unsafe actions. You always respond with a valid JSON object and nothing else.\"\"\"

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_predict 1024
PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"
"""

    modelfile_path = output_dir / "Modelfile"
    with open(modelfile_path, "w") as f:
        f.write(modelfile_content)

    return modelfile_path


def main():
    config = load_config()

    print("=" * 60)
    print("  MindWall — Model Export (GGUF for Ollama)")
    print("=" * 60)

    merged_dir = Path(config["merged_output_dir"])
    gguf_dir = Path(config["gguf_output_dir"])
    quantization = config.get("export_quantization", "q4_k_m")
    model_name = config.get("ollama_model_name", "mindwall-llama3.1-8b")

    if not merged_dir.exists():
        print(f"  ❌ Merged model not found at {merged_dir}")
        print("  Run train.py first.")
        sys.exit(1)

    gguf_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Convert to GGUF using llama.cpp ───────────────────────────────
    print(f"\n[1/3] Converting merged model to GGUF ({quantization})...")

    # Check for llama.cpp convert script
    convert_script = None
    for candidate in [
        "python -m llama_cpp.convert",
        "convert_hf_to_gguf.py",
        "convert-hf-to-gguf.py",
    ]:
        try:
            subprocess.run(
                ["python", "-c", "import llama_cpp"],
                capture_output=True, check=True,
            )
            convert_script = "llama_cpp"
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    # Try using unsloth's built-in GGUF export
    gguf_path = gguf_dir / f"mindwall-{quantization}.gguf"

    try:
        from unsloth import FastLanguageModel

        print("  Using Unsloth GGUF export...")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=str(merged_dir),
            max_seq_length=config["max_seq_length"],
            dtype=None,
            load_in_4bit=False,  # Load full precision for export
        )

        # Unsloth supports direct GGUF save
        model.save_pretrained_gguf(
            str(gguf_dir),
            tokenizer,
            quantization_method=quantization,
        )

        # Find the exported GGUF file
        gguf_files = list(gguf_dir.glob("*.gguf"))
        if gguf_files:
            gguf_path = gguf_files[0]
            print(f"  ✅ GGUF exported: {gguf_path}")
        else:
            print("  ❌ GGUF export failed — no .gguf file found")
            sys.exit(1)

    except ImportError:
        print("  ⚠ Unsloth not available for GGUF export.")
        print("  Falling back to llama-cpp-python conversion...")

        try:
            # Use llama-cpp-python's convert utility
            cmd = [
                sys.executable, "-m", "llama_cpp.llama_convert",
                "--outfile", str(gguf_path),
                "--outtype", quantization,
                str(merged_dir),
            ]
            subprocess.run(cmd, check=True)
            print(f"  ✅ GGUF exported: {gguf_path}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"  ❌ GGUF conversion failed: {e}")
            print("  Manual conversion steps:")
            print(f"    1. Clone llama.cpp: git clone https://github.com/ggerganov/llama.cpp")
            print(f"    2. Run: python llama.cpp/convert_hf_to_gguf.py {merged_dir} --outfile {gguf_path} --outtype {quantization}")
            sys.exit(1)

    # ── 2. Create Ollama Modelfile ───────────────────────────────────────
    print(f"\n[2/3] Creating Ollama Modelfile...")
    modelfile_path = create_modelfile(str(gguf_path), model_name, gguf_dir)
    print(f"  ✅ Modelfile: {modelfile_path}")

    # ── 3. Import into Ollama ────────────────────────────────────────────
    print(f"\n[3/3] Importing into Ollama as '{model_name}'...")

    try:
        result = subprocess.run(
            ["ollama", "create", model_name, "-f", str(modelfile_path)],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0:
            print(f"  ✅ Model '{model_name}' registered in Ollama!")
            print(f"  Test: ollama run {model_name}")
        else:
            print(f"  ⚠ Ollama import returned code {result.returncode}")
            print(f"  stderr: {result.stderr}")
            print(f"\n  Manual import:")
            print(f"    ollama create {model_name} -f {modelfile_path}")
    except FileNotFoundError:
        print("  ⚠ Ollama CLI not found. Import manually:")
        print(f"    ollama create {model_name} -f {modelfile_path}")
    except subprocess.TimeoutExpired:
        print("  ⚠ Ollama import timed out. Run manually:")
        print(f"    ollama create {model_name} -f {modelfile_path}")

    # ── Save export metadata ─────────────────────────────────────────────
    export_info = {
        "source_model": str(merged_dir),
        "gguf_path": str(gguf_path),
        "quantization": quantization,
        "ollama_model_name": model_name,
        "modelfile_path": str(modelfile_path),
        "exported_at": datetime.utcnow().isoformat(),
        "developer": "Pradyumn Tandon | VRIP7",
    }
    with open(gguf_dir / "export_info.json", "w") as f:
        json.dump(export_info, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  ✅ Export complete!")
    print(f"  GGUF:      {gguf_path}")
    print(f"  Modelfile: {modelfile_path}")
    print(f"  Ollama:    {model_name}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
