$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RawDir = Join-Path $ScriptDir "raw"

New-Item -ItemType Directory -Force -Path $RawDir | Out-Null

Write-Host "[MindWall] Downloading datasets..."

# ================= CEAS =================
$CeasDir = Join-Path $RawDir "ceas2008"

if (-not (Test-Path $CeasDir)) {

    Write-Host "Downloading CEAS 2008..."

    New-Item -ItemType Directory -Force -Path $CeasDir | Out-Null

    try {
        Invoke-WebRequest `
            -Uri "https://monkey.org/~jose/phishing/phishing3.mbox" `
            -OutFile (Join-Path $CeasDir "phishing.mbox")
    }
    catch {
        Write-Host "CEAS download failed."
    }

}
else {
    Write-Host "CEAS already exists."
}

# ================= ENRON =================
$EnronDir = Join-Path $RawDir "enron"

if (-not (Test-Path $EnronDir)) {

    Write-Host "Downloading Enron..."

    New-Item -ItemType Directory -Force -Path $EnronDir | Out-Null

    $TarFile = Join-Path $EnronDir "enron_mail.tar.gz"

    try {
        Invoke-WebRequest `
            -Uri "https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz" `
            -OutFile $TarFile

        if (Test-Path $TarFile) {
            Write-Host "Extracting Enron..."
            tar -xzf $TarFile -C $EnronDir
            Remove-Item $TarFile -Force
        }
    }
    catch {
        Write-Host "Enron download failed."
    }

}
else {
    Write-Host "Enron already exists."
}

# ================= FRAUD =================
# Uses HuggingFace ealvaradob/phishing-dataset via the datasets library
# (Replaces the previously unavailable nigerian-prince GitHub dataset)
$FraudDir = Join-Path $RawDir "nigerian_fraud"

if (-not (Test-Path $FraudDir)) {

    Write-Host "Downloading Phishing/Social Engineering corpus from HuggingFace..."

    New-Item -ItemType Directory -Force -Path $FraudDir | Out-Null

    try {
        python -c @"
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
print(f'Downloaded and processed {count} phishing email samples')
"@ $FraudDir
    }
    catch {
        Write-Host "Phishing corpus download failed. Ensure datasets is installed: pip install datasets"
    }

}
else {
    Write-Host "Phishing corpus already exists."
}

Write-Host ""
Write-Host "[MindWall] Download complete."
Write-Host "Location: $RawDir"