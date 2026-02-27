<p align="center">
  <img src="extension/icons/README.md" width="0" height="0" />
  <h1 align="center">🛡️ MindWall</h1>
  <p align="center">
    <strong>Cognitive Firewall — AI-Powered Human Manipulation Detection</strong>
  </p>
  <p align="center">
    A fully self-hosted, privacy-first cybersecurity platform that intercepts, analyzes, and scores incoming communications for psychological manipulation tactics using a locally-run, fine-tuned large language model.
  </p>
  <p align="center">
    <a href="#quick-start">Quick Start</a> •
    <a href="#architecture">Architecture</a> •
    <a href="#features">Features</a> •
    <a href="#configuration">Configuration</a> •
    <a href="#api-reference">API</a> •
    <a href="#fine-tuning">Fine-Tuning</a> •
    <a href="#contributing">Contributing</a>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT" />
    <img src="https://img.shields.io/badge/python-3.11+-3776AB.svg" alt="Python 3.11+" />
    <img src="https://img.shields.io/badge/react-18-61DAFB.svg" alt="React 18" />
    <img src="https://img.shields.io/badge/docker-compose-2496ED.svg" alt="Docker Compose" />
    <img src="https://img.shields.io/badge/LLM-Llama_3.1_8B-FF6F00.svg" alt="Llama 3.1 8B" />
  </p>
</p>

---

## Overview

MindWall acts as a transparent proxy between email clients and upstream mail servers, analyzing every incoming message through a multi-stage pipeline that combines rule-based pre-filtering, behavioral baseline analysis, and LLM-powered 12-dimension manipulation scoring — all running entirely on-premises. **Zero data leaves the deployment boundary.**

### Why MindWall?

Traditional email security focuses on malware and phishing links. MindWall detects **psychological manipulation** — urgency exploitation, authority fabrication, emotional coercion, social proof manufacturing, and 8 other cognitive attack dimensions that bypass conventional filters.

---

## Features

| Feature | Description |
|---------|-------------|
| **12-Dimension Analysis** | Urgency exploitation, authority fabrication, emotional coercion, social proof, scarcity/FOMO, reciprocity traps, commitment escalation, identity manipulation, information asymmetry, trust exploitation, cognitive overload, isolation tactics |
| **IMAP/SMTP Proxy** | Transparent interception — works with Thunderbird, Apple Mail, Outlook, any IMAP client |
| **Browser Extension** | Manifest V3 extension for Gmail web intercept via MutationObserver DOM injection |
| **Real-time Dashboard** | React 18 + Tailwind CSS with WebSocket-powered live threat feed, dimension radar, risk heatmap |
| **Behavioral Baselines** | Per-sender communication pattern learning with deviation scoring |
| **Fine-tuned LLM** | Llama 3.1 8B fine-tuned with QLoRA via Unsloth, exported to GGUF for Ollama inference |
| **Privacy-First** | 100% on-premises — SQLite database, local Ollama server, no external API calls |
| **GPU Accelerated** | NVIDIA GPU passthrough via Docker with CUDA support |
| **Production-Ready** | Structured logging, health checks, request tracing, async throughout |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    ORGANIZATIONAL NETWORK BOUNDARY                    │
│                                                                      │
│   Email Clients (Thunderbird/Outlook/Apple Mail)                     │
│         │                                                            │
│         ▼                                                            │
│   ┌──────────────────────┐                                           │
│   │  IMAP/SMTP PROXY     │  localhost:1143 (IMAP) / :1025 (SMTP)    │
│   │  asyncio stream-based│                                           │
│   └─────────┬────────────┘                                           │
│             │ HTTP POST /api/analyze                                  │
│             ▼                                                        │
│   ┌──────────────────────┐     ┌──────────────────┐                  │
│   │  FASTAPI ENGINE      │────▶│  OLLAMA LLM      │                  │
│   │  • Pre-filter        │     │  Llama 3.1 8B    │                  │
│   │  • Behavioral Engine │     │  Fine-tuned LoRA  │                  │
│   │  • 12-Dim Scorer     │     │  24GB GPU         │                  │
│   │  • Alert Writer      │     └──────────────────┘                  │
│   └─────────┬────────────┘                                           │
│             │ WebSocket                                               │
│             ▼                                                        │
│   ┌──────────────────────┐     ┌──────────────────┐                  │
│   │  REACT DASHBOARD     │     │  BROWSER EXT     │                  │
│   │  :3000               │     │  Gmail Intercept │                  │
│   └──────────────────────┘     └──────────────────┘                  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

| Requirement | Minimum |
|-------------|---------|
| **Docker Desktop** | v24+ with Docker Compose v2 |
| **NVIDIA GPU** | 8GB VRAM (24GB recommended) |
| **NVIDIA Drivers** | 535+ with CUDA 12.x |
| **NVIDIA Container Toolkit** | Latest |
| **OS** | Linux (Ubuntu 22.04+), Windows 10/11 with WSL2, macOS (CPU-only) |
| **RAM** | 16GB minimum, 32GB recommended |
| **Disk** | 20GB free (model weights + database) |

---

## Quick Start

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

### Manual Setup

```bash
# 1. Copy environment config
cp .env.example .env

# 2. Generate API secret
openssl rand -hex 32   # paste into API_SECRET_KEY in .env

# 3. Create data directories
mkdir -p data/db data/models

# 4. Build and start
docker compose up -d --build

# 5. Pull the LLM model
docker compose exec ollama ollama pull llama3.1:8b
```

### Verify Installation

```bash
# API health check
curl http://localhost:8000/health

# Dashboard
open http://localhost:3000

# Ollama model status
curl http://localhost:11434/api/tags
```

---

## Services

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| **API Engine** | `mindwall-api` | `8000` | FastAPI core — analysis pipeline, REST API, WebSocket |
| **Dashboard** | `mindwall-ui` | `3000` | React 18 real-time threat monitoring UI |
| **Ollama** | `mindwall-ollama` | `11434` | Local LLM inference server (Llama 3.1 8B) |
| **IMAP Proxy** | `mindwall-proxy` | `1143` | Transparent IMAP proxy with email interception |
| **SMTP Proxy** | `mindwall-proxy` | `1025` | SMTP relay with outbound analysis |

---

## Configuration

All configuration is managed through environment variables in `.env`:

```dotenv
# API
API_SECRET_KEY=<generated-secret>
DATABASE_URL=sqlite+aiosqlite:////app/data/db/mindwall.db
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=mindwall-llama3.1-8b
OLLAMA_TIMEOUT_SECONDS=30
LOG_LEVEL=INFO
WORKERS=4

# Proxy
IMAP_LISTEN_HOST=0.0.0.0
IMAP_LISTEN_PORT=1143
SMTP_LISTEN_HOST=0.0.0.0
SMTP_LISTEN_PORT=1025

# Alert Thresholds
ALERT_MEDIUM_THRESHOLD=35
ALERT_HIGH_THRESHOLD=60
ALERT_CRITICAL_THRESHOLD=80
```

### Email Client Configuration

Point your email client's IMAP server to MindWall's proxy:

| Setting | Value |
|---------|-------|
| **IMAP Server** | `localhost` |
| **IMAP Port** | `1143` |
| **SMTP Server** | `localhost` |
| **SMTP Port** | `1025` |
| **Security** | STARTTLS (proxy handles upstream TLS) |
| **Credentials** | Your real email credentials (passed through) |

---

## API Reference

### Analysis Endpoint

```http
POST /api/analyze
Content-Type: application/json
X-API-Key: <API_SECRET_KEY>

{
  "sender": "sender@example.com",
  "recipient": "employee@company.com",
  "subject": "Urgent: Action Required Immediately",
  "body": "...",
  "source": "imap_proxy"
}
```

**Response:**

```json
{
  "analysis_id": "uuid",
  "overall_score": 72,
  "verdict": "block",
  "dimensions": {
    "urgency_exploitation": 85,
    "authority_fabrication": 60,
    "emotional_coercion": 70,
    "social_proof_manufacturing": 15,
    "scarcity_fomo": 80,
    "reciprocity_trap": 10,
    "commitment_escalation": 45,
    "identity_manipulation": 30,
    "information_asymmetry": 55,
    "trust_exploitation": 65,
    "cognitive_overload": 40,
    "isolation_tactics": 20
  },
  "explanation": "High urgency exploitation combined with authority fabrication...",
  "recommended_action": "block",
  "confidence": 0.87
}
```

### Dashboard Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/dashboard/stats` | Aggregate threat statistics |
| `GET` | `/api/dashboard/threats` | Recent threat timeline |
| `GET` | `/api/alerts` | Paginated alert list |
| `GET` | `/api/alerts/{id}` | Single alert detail |
| `PATCH` | `/api/alerts/{id}` | Update alert status |
| `GET` | `/api/employees` | Employee risk profiles |
| `GET` | `/api/employees/{id}` | Individual employee detail |
| `GET` | `/api/settings` | Current system settings |
| `PUT` | `/api/settings` | Update thresholds/config |
| `WS` | `/ws/alerts` | Real-time alert stream |

### Health Check

```http
GET /health
```

---

## Scoring System

MindWall analyzes communications across **12 manipulation dimensions**, each scored 0–100:

| Score Range | Classification | Action |
|-------------|---------------|--------|
| 0–15 | No detectable signal | Proceed |
| 16–35 | Weak / incidental | Proceed |
| 36–60 | Moderate / deliberate | Verify |
| 61–80 | Strong / coordinated | Block |
| 81–100 | Definitive / adversarial | Block |

### The 12 Dimensions

1. **Urgency Exploitation** — Artificial time pressure to bypass rational evaluation
2. **Authority Fabrication** — False or inflated authority claims
3. **Emotional Coercion** — Fear, guilt, flattery to override logical thinking
4. **Social Proof Manufacturing** — Fabricated consensus or third-party endorsements
5. **Scarcity / FOMO** — Artificial scarcity or fear of missing out
6. **Reciprocity Trap** — Unsolicited favors creating obligation pressure
7. **Commitment Escalation** — Small agreements leveraged into larger compliance
8. **Identity Manipulation** — Targeting role, values, or in-group identity
9. **Information Asymmetry** — Deliberate ambiguity or information withholding
10. **Trust Exploitation** — Leveraging established relationships or institutional trust
11. **Cognitive Overload** — Excessive detail/complexity to impair judgment
12. **Isolation Tactics** — Discouraging external consultation or verification

---

## Browser Extension

The MindWall browser extension intercepts emails in Gmail's web interface using a Manifest V3 architecture.

### Installation (Developer Mode)

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `extension/` folder
5. The extension will inject threat scores into Gmail's email view

### How It Works

- Uses `MutationObserver` to detect when emails are opened in Gmail
- Extracts email content from the DOM
- Sends content to `localhost:8000/api/analyze`
- Injects a visual threat indicator badge into the email header

---

## Fine-Tuning

MindWall includes a complete fine-tuning pipeline for the Llama 3.1 8B model using QLoRA via Unsloth.

### Requirements

- NVIDIA GPU with 8GB+ VRAM
- Python 3.11+
- ~10GB disk for model weights

### Pipeline

```bash
cd finetune

# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate synthetic training data
python datasets/synthetic_generator.py

# 3. Prepare dataset (format + split)
python prepare_dataset.py

# 4. Train with QLoRA
python train.py

# 5. Evaluate on held-out test set
python evaluate.py

# 6. Export to GGUF for Ollama
python export.py

# 7. Load into Ollama
ollama create mindwall-llama3.1-8b -f Modelfile
```

### Training Configuration

The QLoRA configuration is in `finetune/configs/qlora_config.yaml`:

- **Base model:** `unsloth/Meta-Llama-3.1-8B-Instruct`
- **LoRA rank:** 64
- **LoRA alpha:** 128
- **Target modules:** `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`
- **Quantization:** 4-bit NF4
- **Batch size:** 4 (gradient accumulation: 8)
- **Learning rate:** 2e-4
- **Epochs:** 3
- **Max sequence length:** 4096

---

## Development

### Makefile Commands

```bash
make dev          # Start with docker-compose.override.yml (hot reload)
make up           # Production start
make down         # Stop all services
make logs         # Tail all container logs
make logs-api     # Tail API logs only
make build        # Rebuild all images
make test         # Run test suite
make lint         # Run linters
make clean        # Remove containers, volumes, data
```

### Local API Development

```bash
cd api
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
.\.venv\Scripts\activate     # Windows
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Local Dashboard Development

```bash
cd dashboard
npm install
npm run dev    # Vite dev server on :3000
```

### Project Structure

```
mindwall/
├── api/                    # FastAPI core engine
│   ├── analysis/           # LLM pipeline, pre-filter, scorer, behavioral engine
│   ├── core/               # Config, lifespan, structured logging
│   ├── db/                 # SQLAlchemy async, models, repositories, migrations
│   ├── middleware/          # Auth, request ID tracing
│   ├── routers/            # REST + WebSocket endpoints
│   ├── schemas/            # Pydantic request/response models
│   └── websocket/          # Connection manager, event serializers
├── proxy/                  # IMAP/SMTP transparent proxy
│   ├── imap/               # IMAP server, parser, interceptor, injector
│   ├── smtp/               # SMTP server, upstream relay
│   ├── mime/               # MIME parser, HTML sanitizer
│   └── ssl/                # TLS termination handler
├── dashboard/              # React 18 + Vite + Tailwind CSS
│   └── src/
│       ├── api/            # REST client, WebSocket hook
│       ├── components/     # Layout, alerts, dashboard charts, employee views
│       └── pages/          # Dashboard, Alerts, Employees, Settings
├── extension/              # Chrome/Firefox Manifest V3 extension
├── finetune/               # QLoRA fine-tuning pipeline
│   ├── configs/            # Training hyperparameters
│   └── datasets/           # Synthetic data generator, download scripts
├── docker-compose.yml      # Production orchestration
├── docker-compose.override.yml  # Dev overrides
├── setup.sh                # Linux/macOS setup
├── setup.ps1               # Windows PowerShell setup
├── Makefile                # Task runner
└── .env.example            # Environment template
```

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| `nvidia-smi` not found | Install NVIDIA drivers: https://developer.nvidia.com/cuda-downloads |
| Ollama container unhealthy | Check GPU access: `docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi` |
| Model pull fails | Retry: `docker compose exec ollama ollama pull llama3.1:8b` |
| Port 8000 in use | Change in `.env` and `docker-compose.yml` |
| IMAP connection refused | Ensure proxy container is running: `docker compose logs proxy` |
| Dashboard blank | Check API connection: `curl http://localhost:8000/health` |
| High memory usage | Reduce `OLLAMA_NUM_PARALLEL` in compose file |
| Slow inference | Ensure GPU passthrough: check `deploy.resources` in compose |

### Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f ollama
docker compose logs -f proxy
docker compose logs -f ui
```

---

## Security

MindWall is designed for **internal network deployment only**. See [SECURITY.md](SECURITY.md) for:

- Responsible disclosure policy
- Deployment hardening guidelines
- API authentication details

**Important:** Never expose MindWall ports (8000, 3000, 1143, 1025) to the public internet.

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Setting up a development environment
- Code style and standards
- Pull request process
- Issue reporting

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## Credits

**Developed by [Pradyumn Tandon](https://pradyumntandon.com) at [VRIP7](https://vrip7.com)**

- Website: https://pradyumntandon.com
- Organization: https://vrip7.com
- GitHub: https://github.com/vrip7

---

<p align="center">
  <sub>MindWall — Because the most dangerous attacks target the mind, not the machine.</sub>
</p>
