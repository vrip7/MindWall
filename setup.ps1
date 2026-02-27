# MindWall — One-Command Setup (Windows PowerShell)
# Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
#
# Usage: .\setup.ps1
# Requires: Docker Desktop (with WSL2/Hyper-V), NVIDIA GPU drivers, NVIDIA Container Toolkit

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step { param([string]$Message) Write-Host "[MindWall] $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message) Write-Host "  ✅ $Message" -ForegroundColor Green }
function Write-Warn { param([string]$Message) Write-Host "  ⚠  $Message" -ForegroundColor Yellow }

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "  ║        MindWall — Cognitive Firewall Setup               ║" -ForegroundColor Blue
Write-Host "  ║        Developed by Pradyumn Tandon @ VRIP7              ║" -ForegroundColor Blue
Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# ── 1. Dependency Checks ──────────────────────────────────────────────────────

Write-Step "Checking dependencies..."

# Docker
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "  ❌ Docker is not installed or not in PATH." -ForegroundColor Red
    Write-Host "     Install Docker Desktop: https://docs.docker.com/desktop/install/windows-install/" -ForegroundColor Red
    exit 1
}
Write-Success "Docker found: $(docker --version)"

# Docker Compose (v2 built into Docker Desktop)
$composeCheck = docker compose version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Docker Compose (v2) not available." -ForegroundColor Red
    Write-Host "     Ensure Docker Desktop is updated to latest version." -ForegroundColor Red
    exit 1
}
Write-Success "Docker Compose found: $composeCheck"

# NVIDIA GPU
$nvidiaCheck = nvidia-smi 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warn "NVIDIA GPU drivers not detected. Ollama requires GPU acceleration."
    Write-Warn "Install: https://developer.nvidia.com/cuda-downloads"
    $continue = Read-Host "Continue without GPU check? (y/N)"
    if ($continue -ne "y") { exit 1 }
} else {
    $gpuName = (nvidia-smi --query-gpu=name --format=csv,noheader 2>$null) | Select-Object -First 1
    $gpuMem  = (nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>$null) | Select-Object -First 1
    Write-Success "NVIDIA GPU: $($gpuName.Trim()) ($($gpuMem.Trim()))"
}

# OpenSSL (for secret generation)
$hasOpenSSL = Get-Command "openssl" -ErrorAction SilentlyContinue

# ── 2. Environment Configuration ─────────────────────────────────────────────

Write-Step "Configuring environment..."

$envFile = Join-Path $PSScriptRoot ".env"
$envExample = Join-Path $PSScriptRoot ".env.example"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Success "Created .env from .env.example"
    } else {
        Write-Host "  ❌ .env.example not found." -ForegroundColor Red
        exit 1
    }
}

# Generate secret key
if ($hasOpenSSL) {
    $secret = openssl rand -hex 32 2>$null
} else {
    # Fallback: .NET random bytes
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $secret = ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""
}

# Update API_SECRET_KEY in .env
$envContent = Get-Content $envFile -Raw
$envContent = $envContent -replace "API_SECRET_KEY=.*", "API_SECRET_KEY=$secret"
Set-Content $envFile $envContent -NoNewline
Write-Success "API secret key generated and written to .env"

# ── 3. Data Directories ──────────────────────────────────────────────────────

Write-Step "Creating data directories..."

$dirs = @("data\db", "data\models")
foreach ($dir in $dirs) {
    $fullPath = Join-Path $PSScriptRoot $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    }
}
Write-Success "data\db and data\models ready"

# ── 4. Build & Start Services ────────────────────────────────────────────────

Write-Step "Building and starting Docker services..."
Write-Host "  This may take several minutes on first run..." -ForegroundColor DarkGray

docker compose up -d --build
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Docker Compose build failed." -ForegroundColor Red
    Write-Host "     Check Docker Desktop is running and GPU passthrough is configured." -ForegroundColor Red
    exit 1
}
Write-Success "All containers started"

# ── 5. Wait for Ollama Health ────────────────────────────────────────────────

Write-Step "Waiting for Ollama LLM server to become healthy..."

$maxAttempts = 30
$attempt = 0
$ollamaReady = $false

while ($attempt -lt $maxAttempts) {
    $attempt++
    try {
        $result = docker compose exec ollama curl -sf http://localhost:11434/api/tags 2>$null
        if ($LASTEXITCODE -eq 0) {
            $ollamaReady = $true
            break
        }
    } catch { }
    Write-Host "  Attempt $attempt/$maxAttempts — waiting 10s..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 10
}

if (-not $ollamaReady) {
    Write-Warn "Ollama did not become healthy within timeout."
    Write-Warn "Check: docker compose logs ollama"
} else {
    Write-Success "Ollama is healthy"
}

# ── 6. Pull LLM Model ───────────────────────────────────────────────────────

Write-Step "Pulling Llama 3.1 8B model (this may take several minutes)..."

docker compose exec ollama ollama pull llama3.1:8b
if ($LASTEXITCODE -eq 0) {
    Write-Success "Model pulled successfully"
} else {
    Write-Warn "Model pull may have failed. Retry: docker compose exec ollama ollama pull llama3.1:8b"
}

# ── 7. Verify Services ──────────────────────────────────────────────────────

Write-Step "Verifying service health..."

Start-Sleep -Seconds 5

$services = @(
    @{ Name = "API";       URL = "http://localhost:8000/health";       Container = "mindwall-api" },
    @{ Name = "Dashboard"; URL = "http://localhost:3000";              Container = "mindwall-ui" },
    @{ Name = "Ollama";    URL = "http://localhost:11434/api/tags";    Container = "mindwall-ollama" }
)

foreach ($svc in $services) {
    try {
        $response = Invoke-WebRequest -Uri $svc.URL -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "$($svc.Name) — healthy"
        }
    } catch {
        Write-Warn "$($svc.Name) — not yet responding (container: $($svc.Container))"
    }
}

# ── Done ─────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║          ✅ MindWall is running                        ║" -ForegroundColor Green
Write-Host "  ║                                                        ║" -ForegroundColor Green
Write-Host "  ║  Dashboard:    http://localhost:3000                   ║" -ForegroundColor Green
Write-Host "  ║  API:          http://localhost:8000                   ║" -ForegroundColor Green
Write-Host "  ║  API Health:   http://localhost:8000/health            ║" -ForegroundColor Green
Write-Host "  ║  IMAP Proxy:   localhost:1143                         ║" -ForegroundColor Green
Write-Host "  ║  SMTP Proxy:   localhost:1025                         ║" -ForegroundColor Green
Write-Host "  ║                                                        ║" -ForegroundColor Green
Write-Host "  ║  Point your email client IMAP to: localhost:1143      ║" -ForegroundColor Green
Write-Host "  ║                                                        ║" -ForegroundColor Green
Write-Host "  ║  Developed by Pradyumn Tandon @ VRIP7                 ║" -ForegroundColor Green
Write-Host "  ║  https://pradyumntandon.com | https://vrip7.com       ║" -ForegroundColor Green
Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
