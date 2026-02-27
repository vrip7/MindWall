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
$FraudDir = Join-Path $RawDir "nigerian_fraud"

if (-not (Test-Path $FraudDir)) {

    Write-Host "Downloading Nigerian Fraud dataset..."

    New-Item -ItemType Directory -Force -Path $FraudDir | Out-Null

    try {
        Invoke-WebRequest `
            -Uri "https://raw.githubusercontent.com/5starkarma/nigerian-prince/master/data/nigerian_prince_emails.csv" `
            -OutFile (Join-Path $FraudDir "nigerian_fraud_emails.csv")
    }
    catch {
        Write-Host "Fraud dataset download failed."
    }

}
else {
    Write-Host "Fraud dataset already exists."
}

Write-Host ""
Write-Host "[MindWall] Download complete."
Write-Host "Location: $RawDir"