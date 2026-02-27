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

# ── 3. Nigerian Fraud / 419 Advance-Fee Corpus ────────────────────────────
FRAUD_DIR="${RAW_DIR}/nigerian_fraud"
if [ ! -d "${FRAUD_DIR}" ]; then
    echo "  → Downloading Nigerian Fraud email corpus..."
    mkdir -p "${FRAUD_DIR}"
    curl -fSL \
        "https://raw.githubusercontent.com/5starkarma/nigerian-prince/master/data/nigerian_prince_emails.csv" \
        -o "${FRAUD_DIR}/nigerian_fraud_emails.csv" 2>/dev/null || \
        echo "    ⚠ Nigerian fraud corpus download failed — add manually."
else
    echo "  → Nigerian Fraud corpus already present, skipping."
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
