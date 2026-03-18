# Getting Started

> First-time installation and verification of a MindWall deployment.

---

## Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Docker Desktop** | v24+ with Compose v2 | Latest stable |
| **NVIDIA GPU** | 8 GB VRAM | 24 GB VRAM |
| **NVIDIA Drivers** | 535+ with CUDA 12.x | Latest |
| **NVIDIA Container Toolkit** | Latest | Latest |
| **Operating System** | Linux (Ubuntu 22.04+), Windows 10/11 with WSL2, macOS (CPU-only) | Ubuntu 22.04+ or Windows 11 |
| **RAM** | 16 GB | 32 GB |
| **Disk** | 20 GB free | 40 GB free |

### Verifying GPU Access

```bash
# Check NVIDIA drivers
nvidia-smi

# Verify Docker GPU passthrough
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

If `nvidia-smi` fails inside Docker, install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).

---

## One-Command Setup

### Linux / macOS

```bash
git clone https://github.com/vrip7/mindwall.git
cd mindwall
chmod +x setup.sh
./setup.sh
```

### Windows (PowerShell)

```powershell
git clone https://github.com/vrip7/mindwall.git
cd mindwall
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
```

The setup script will:

1. **Check dependencies** — Docker, Docker Compose, NVIDIA GPU drivers.
2. **Create `.env`** from `.env.example` and generate a random `API_SECRET_KEY`.
3. **Create data directories** — `data/db/` (SQLite database) and `data/models/` (Ollama model cache).
4. **Build and start** all four Docker services.
5. **Wait for Ollama** to become healthy.
6. **Pull the Qwen3-8B model** into the Ollama container.
7. **Verify** each service responds to health checks.

---

## Manual Setup

If you prefer to run each step yourself:

```bash
# 1. Clone the repository
git clone https://github.com/vrip7/mindwall.git
cd mindwall

# 2. Create environment file
cp .env.example .env

# 3. Generate a strong API secret
#    Linux/macOS:
openssl rand -hex 32
#    Windows PowerShell:
[System.Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))

# 4. Edit .env — paste the secret into API_SECRET_KEY
#    Also set DASHBOARD_USERNAME and DASHBOARD_PASSWORD

# 5. Create data directories
mkdir -p data/db data/models          # Linux/macOS
New-Item -ItemType Directory -Path data\db, data\models -Force  # Windows

# 6. Build and start all services
docker compose up -d --build

# 7. Pull the LLM model (may take several minutes)
docker compose exec ollama ollama pull qwen3:8b
```

---

## Verify Installation

### API Health

```bash
curl http://localhost:5297/health
# Expected: {"status":"healthy","service":"mindwall-api","version":"1.0.0"}
```

### Dashboard

Open `http://localhost:4297` in a browser. You should see the MindWall login screen.

Default credentials (change in `.env`):

| Field | Default |
|-------|---------|
| Username | `admin` |
| Password | `MindWall@2026` |

### Ollama Model

```bash
curl http://localhost:11434/api/tags
# Should list qwen3:8b in the models array
```

### Container Health

```bash
docker compose ps
# All containers should show "Up" / "healthy"
```

---

## First-Time Workflow

Once all services are running:

1. **Log in** to the dashboard at `http://localhost:4297`.
2. **Add an employee** on the Employees page:
   - Enter the employee's email address, display name, and department.
   - Expand **Email Account Configuration** and fill in the upstream IMAP/SMTP server details (e.g. `imap.gmail.com:993`, `smtp.gmail.com:587`), the login username (usually the email), and an **app password** (not the regular account password — for Gmail, generate one at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)).
3. **Note the proxy connection info** shown after adding the employee — it tells you the IMAP/SMTP proxy host, port, and username to put in the email client.
4. **Configure the email client** (Thunderbird, Outlook, Apple Mail) to use `localhost:1143` for IMAP and `localhost:1025` for SMTP with **no encryption** and the employee's real credentials. See [Email Client Setup](email-client-setup.md) for step-by-step guides.
5. **Open an email** in the email client — MindWall's IMAP proxy intercepts the FETCH response, analyses the body, and injects a risk badge into the subject line if the score is ≥ 35.
6. **Monitor alerts** in real-time on the dashboard's Alerts page via the WebSocket live feed.
7. **Review risk profiles** on the Employees page to see per-employee 30-day rolling risk scores, top threat senders, and dimension breakdowns.

---

## Stopping and Restarting

```bash
# Stop all services (keep data)
docker compose down

# Restart
docker compose up -d

# Full clean (removes database, model cache, images)
docker compose down -v --rmi all --remove-orphans
rm -f data/db/mindwall.db
```

---

## Upgrading

```bash
git pull origin main
docker compose up -d --build
```

The database schema auto-migrates on API startup via `run_migrations()` in `api/db/database.py`.
