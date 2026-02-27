# MindWall — Dataset Downloader (Windows Version)
# Downloads public phishing/social engineering corpora for fine-tuning
# Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RawDir = Join-Path $ScriptDir "raw"

New-Item -ItemType Directory -Force -Path $RawDir | Out-Null

Write-Host "[MindWall] Downloading training datasets..."

# ── 1. CEAS 2008 Spam/Phishing Corpus ──────────────────────────────────────
$CeasDir = Join-Path $RawDir "ceas2008"

if (-Not (Test-Path $CeasDir)) {
    Write-Host "  → Downloading CEAS 2008 corpus..."
    New-Item -ItemType Directory -Force -Path $CeasDir | Out-Null

    try {
        Invoke-WebRequest `
            -Uri "https://monkey.org/~jose/phishing/phishing3.mbox" `
            -OutFile (Join-Path $CeasDir "phishing.mbox")
    }
    catch {
        Write-Host "    ⚠ CEAS 2008 download failed — add corpus manually to $CeasDir/"
    }
}
else {
    Write-Host "  → CEAS 2008 already present, skipping."
}

# ── 2. Enron Email Dataset ──────────────────────────────────────────────────
$EnronDir = Join-Path $RawDir "enron"

if (-Not (Test-Path $EnronDir)) {
    Write-Host "  → Downloading Enron phishing subset..."
    New-Item -ItemType Directory -Force -Path $EnronDir | Out-Null

    $EnronTar = Join-Path $EnronDir "enron_mail.tar.gz"

    try {
        Invoke-WebRequest `
            -Uri "https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz" `
            -OutFile $EnronTar

        if (Test-Path $EnronTar) {
            Write-Host "    → Extracting Enron corpus (this may take a while)..."
            tar -xzf $EnronTar -C $EnronDir
            Remove-Item $EnronTar -Force
        }
    }
    catch {
        Write-Host "    ⚠ Enron download failed (large file ~423MB). Download manually."
    }
}
else {
    Write-Host "  → Enron corpus already present, skipping."
}

# ── 3. Nigerian Fraud / 419 Corpus ─────────────────────────────────────────
$FraudDir = Join-Path $RawDir "nigerian_fraud"

if (-Not (Test-Path $FraudDir)) {
    Write-Host "  → Downloading Nigerian Fraud email corpus..."
    New-Item -ItemType Directory -Force -Path $FraudDir | Out-Null

    try {
        Invoke-WebRequest `
            -Uri "https://raw.githubusercontent.com/5starkarma/nigerian-prince/master/data/nigerian_prince_emails.csv" `
            -OutFile (Join-Path $FraudDir "nigerian_fraud_emails.csv")
    }
    catch {
        Write-Host "    ⚠ Nigerian fraud corpus download failed — add manually."
    }
}
else {
    Write-Host "  → Nigerian Fraud corpus already present, skipping."
}

# ── 4. Synthetic Placeholder ───────────────────────────────────────────────
$SyntheticDir = Join-Path $RawDir "synthetic"
New-Item -ItemType Directory -Force -Path $SyntheticDir | Out-Null

if (-Not (Test-Path (Join-Path $SyntheticDir ".generated"))) {
    Write-Host "  → Synthetic dataset not yet generated."
    Write-Host "    Run: python synthetic_generator.py"
}

Write-Host ""
Write-Host "[MindWall] Dataset download complete."
Write-Host "  Raw data location: $RawDir"
Write-Host ""
Write-Host "  Next steps:"
Write-Host "    1. Generate synthetic data:  python synthetic_generator.py"
Write-Host "    2. Prepare training data:    python prepare_dataset.py"
Write-Host "    3. Train:                    python train.py"