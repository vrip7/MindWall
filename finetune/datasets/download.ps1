# MindWall — Dataset Downloader (Windows Version)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RawDir = Join-Path $ScriptDir "raw"

New-Item -ItemType Directory -Force -Path $RawDir | Out-Null

Write-Host "[MindWall] Downloading training datasets..."

# ── 1. CEAS 2008 ─────────────────────────────────────────────
$CeasDir = Join-Path $RawDir "ceas2008"

if (-Not (Test-Path $CeasDir)) {
    Write-Host "  -> Downloading CEAS 2008 corpus..."
    New-Item -ItemType Directory -Force -Path $CeasDir | Out-Null

    try {
        Invoke-WebRequest -Uri "https://monkey.org/~jose/phishing/phishing3.mbox" `
                          -OutFile (Join-Path $CeasDir "phishing.mbox")
    }
    catch {
        Write-Host "  WARNING: CEAS 2008 download failed — add manually."
    }
}
else {
    Write-Host "  -> CEAS 2008 already present, skipping."
}

# ── 2. Enron Dataset ─────────────────────────────────────────
$EnronDir = Join-Path $RawDir "enron"

if (-Not (Test-Path $EnronDir)) {
    Write-Host "  -> Downloading Enron dataset..."
    New-Item -ItemType Directory -Force -Path $EnronDir | Out-Null

    $EnronTar = Join-Path $EnronDir "enron_mail.tar.gz"

    try {
        Invoke-WebRequest -Uri "https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz" `
                          -OutFile $EnronTar

        if (Test-Path $EnronTar) {
            Write-Host "  -> Extracting Enron dataset..."
            tar -xzf $EnronTar -C $EnronDir
            Remove-Item $EnronTar -Force
        }
    }
    catch {
        Write-Host "  WARNING: Enron download failed (large file)."
    }
}
else {
    Write-Host "  -> Enron already present, skipping."
}

# ── 3. Nigerian Fraud ───────────────────────────────────────
$FraudDir = Join-Path $RawDir "nigerian_fraud"

if (-Not (Test-Path $FraudDir)) {
    Write-Host "  -> Downloading Nigerian Fraud corpus..."
    New-Item -ItemType Directory -Force -Path $FraudDir | Out-Null

    try {
        Invoke-WebRequest -Uri "https://raw.githubusercontent.com/5starkarma/nigerian-prince/master/data/nigerian_prince_emails.csv" `
                          -OutFile (Join-Path $FraudDir "nigerian_fraud_emails.csv")
    }
    catch {
        Write-Host "  WARNING: Nigerian fraud corpus download failed."
    }
}
else {
    Write-Host "  -> Nigerian Fraud already present, skipping."
}

# ── 4. Synthetic Placeholder ─────────────────────────────────
$SyntheticDir = Join-Path $RawDir "synthetic"
New-Item -ItemType Directory -Force -Path $SyntheticDir | Out-Null

if (-Not (Test-Path (Join-Path $SyntheticDir ".generated"))) {
    Write-Host "  -> Synthetic dataset not yet generated."
    Write-Host "     Run: python synthetic_generator.py"
}

Write-Host ""
Write-Host "[MindWall] Dataset download complete."
Write-Host "  Raw data location: $RawDir"
Write-Host ""
Write-Host "  Next steps:"
Write-Host "    1. Generate synthetic data: python synthetic_generator.py"
Write-Host "    2. Prepare training data:   python prepare_dataset.py"
Write-Host "    3. Train:                   python train.py"