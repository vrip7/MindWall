#!/usr/bin/env bash
# MindWall — Dataset Downloader
# Downloads public phishing/social engineering corpora for fine-tuning
# Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAW_DIR="${SCRIPT_DIR}/raw"
mkdir -p "${RAW_DIR}"

echo "[MindWall] Downloading training datasets..."

# ── 1. CEAS 2008 Spam/Phishing Corpus ──────────────────────────────────────
CEAS_DIR="${RAW_DIR}/ceas2008"
if [ ! -d "${CEAS_DIR}" ]; then
    echo "  → Downloading CEAS 2008 corpus..."
    mkdir -p "${CEAS_DIR}"
    # The CEAS 2008 corpus is available from multiple academic mirrors
    # Download from the IIT Bombay mirror (commonly available)
    curl -fSL \
        "https://monkey.org/~jose/phishing/phishing3.mbox" \
        -o "${CEAS_DIR}/phishing.mbox" 2>/dev/null || \
        echo "    ⚠ CEAS 2008 download failed — add corpus manually to ${CEAS_DIR}/"
else
    echo "  → CEAS 2008 already present, skipping."
fi

# ── 2. Enron Email Dataset (CMU subset—phishing-annotated) ──────────────────
ENRON_DIR="${RAW_DIR}/enron"
if [ ! -d "${ENRON_DIR}" ]; then
    echo "  → Downloading Enron phishing subset..."
    mkdir -p "${ENRON_DIR}"
    curl -fSL \
        "https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz" \
        -o "${ENRON_DIR}/enron_mail.tar.gz" 2>/dev/null || \
        echo "    ⚠ Enron download failed (large file ~423MB). Download manually."
    if [ -f "${ENRON_DIR}/enron_mail.tar.gz" ]; then
        echo "    → Extracting Enron corpus (this may take a while)..."
        tar -xzf "${ENRON_DIR}/enron_mail.tar.gz" -C "${ENRON_DIR}/" --strip-components=1 || true
        rm -f "${ENRON_DIR}/enron_mail.tar.gz"
    fi
else
    echo "  → Enron corpus already present, skipping."
fi

# ── 3. Phishing / Social Engineering Email Corpus ─────────────────────────
# (Replaces the previously unavailable nigerian-prince GitHub dataset)
# Uses HuggingFace ealvaradob/phishing-dataset via the datasets library.
FRAUD_DIR="${RAW_DIR}/nigerian_fraud"
if [ ! -d "${FRAUD_DIR}" ]; then
    echo "  → Downloading Phishing/Social Engineering email corpus from HuggingFace..."
    mkdir -p "${FRAUD_DIR}"
    python3 -c "
import csv, sys
from pathlib import Path
from datasets import load_dataset
ds = load_dataset('ealvaradob/phishing-dataset', split='train')
out_path = Path(sys.argv[1]) / 'nigerian_fraud_emails.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['body', 'label', 'sender', 'subject'])
    writer.writeheader()
    count = 0
    for row in ds:
        text = (row.get('Email Text') or '').strip()
        etype = (row.get('Email Type') or '').lower()
        if text and len(text) > 30:
            label = 'legitimate' if 'safe' in etype else 'phishing'
            writer.writerow({'body': text[:4000], 'label': label, 'sender': '', 'subject': ''})
            count += 1
print(f'  → Downloaded and processed {count} phishing email samples')
" "${FRAUD_DIR}" 2>&1 || \
        echo "    ⚠ Phishing corpus download failed — ensure datasets is installed: pip install datasets"
else
    echo "  → Phishing corpus already present, skipping."
fi

# ── 4. Create placeholder for synthetic data ────────────────────────────────
SYNTHETIC_DIR="${RAW_DIR}/synthetic"
mkdir -p "${SYNTHETIC_DIR}"
if [ ! -f "${SYNTHETIC_DIR}/.generated" ]; then
    echo "  → Synthetic dataset not yet generated."
    echo "    Run: python synthetic_generator.py"
fi

echo ""
echo "[MindWall] Dataset download complete."
echo "  Raw data location: ${RAW_DIR}"
echo ""
echo "  Next steps:"
echo "    1. Generate synthetic data:  python synthetic_generator.py"
echo "    2. Prepare training data:    python prepare_dataset.py"
echo "    3. Train:                    python train.py"
