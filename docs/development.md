# Development Guide

> Project structure, local development setup, and contributing workflow.

---

## Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Docker Desktop | 4.x+ | Container runtime |
| NVIDIA Container Toolkit | Latest | GPU pass-through for Ollama |
| Python | 3.12+ | API/proxy development |
| Node.js | 18+ | Dashboard development |
| Git | Latest | Version control |

---

## Project Structure

```
mindwall/
├── api/                     # FastAPI analysis engine (Python 3.12)
│   ├── analysis/            #   AI analysis pipeline
│   ├── core/                #   Config, lifecycle, logging
│   ├── db/                  #   Database models, repos, migrations
│   ├── middleware/           #   Auth, request ID
│   ├── routers/             #   HTTP + WS endpoints
│   ├── schemas/             #   Pydantic models
│   └── websocket/           #   WebSocket manager + events
├── proxy/                   # IMAP/SMTP transparent proxy (Python 3.12)
│   ├── imap/                #   IMAP server, upstream, interceptor
│   ├── smtp/                #   SMTP handler + upstream
│   ├── mime/                #   MIME parser + HTML sanitizer
│   └── ssl/                 #   TLS context factory
├── dashboard/               # React 18 frontend (Vite + Tailwind)
│   └── src/
│       ├── api/             #   HTTP client (Axios)
│       ├── components/      #   Shared UI components
│       └── pages/           #   Page components
├── extension/               # Chrome/Firefox extension (Manifest V3)
├── finetune/                # QLoRA fine-tuning pipeline
├── docs/                    # Documentation
├── docker-compose.yml       # Production compose
├── docker-compose.override.yml  # Dev compose (hot-reload)
├── Makefile                 # Task runner
├── setup.sh                 # Linux/macOS setup
└── setup.ps1                # Windows setup
```

---

## Local Development Setup

### Quick Start

```powershell
# Clone and navigate
git clone <repo-url>
cd mindwall

# Run setup script (creates .env, pulls images, pulls model)
.\setup.ps1          # Windows
# or
bash setup.sh        # Linux/macOS

# Start all services with hot-reload
docker compose up --build
```

### Development Mode (Hot-Reload)

The `docker-compose.override.yml` file enables hot-reload for all services:

```powershell
# Starts with override automatically (Docker Compose v2 behaviour)
docker compose up --build
```

**What the override changes:**

| Service | Override |
|---------|---------|
| API | Mounts `./api` into container, single worker, `--reload` flag, `DEBUG` logging |
| Proxy | Mounts `./proxy` into container, `DEBUG` logging |
| Dashboard | Mounts `./dashboard`, runs `npm install && npm run dev -- --host 0.0.0.0`, anonymous volume for `node_modules` |

### Production Mode

```powershell
# Explicitly use only the production compose file
docker compose -f docker-compose.yml up -d --build
```

Or use the Makefile:
```bash
make prod
```

---

## Makefile Targets

| Target | Command | Description |
|--------|---------|-------------|
| `make dev` | `docker compose up --build` | Start with dev overrides |
| `make prod` | `docker compose -f docker-compose.yml up -d --build` | Production deploy |
| `make build` | `docker compose build` | Build images only |
| `make down` | `docker compose down` | Stop all services |
| `make logs` | `docker compose logs -f` | Follow all logs |
| `make logs-api` | `docker compose logs -f api` | Follow API logs |
| `make logs-proxy` | `docker compose logs -f proxy` | Follow proxy logs |
| `make clean` | `docker compose down -v --rmi all --remove-orphans` | Full cleanup |
| `make test` | `cd api && python -m pytest tests/ -v` | Run API tests |
| `make lint` | `ruff check api/ proxy/` | Lint Python code |
| `make setup` | `bash setup.sh` | Run initial setup |
| `make pull-model` | `docker compose exec ollama ollama pull qwen3:8b` | Pull LLM model |
| `make load-model` | `docker compose exec ollama ollama create mindwall-qwen3-4b -f /root/.ollama/Modelfile` | Load fine-tuned model |
| `make db-reset` | Remove DB + restart API | Reset database |

---

## Working On Individual Services

### API Development

```powershell
# Start containers with hot-reload
docker compose up --build

# The API auto-reloads on file changes
# Edit files in api/ — changes reflected immediately

# View API logs
docker compose logs -f api

# Run tests locally
cd api
pip install -r requirements.txt
python -m pytest tests/ -v

# Lint
ruff check api/
```

**Key files to know:**
- `api/main.py` — App factory, router registration, lifespan
- `api/core/config.py` — All settings (Pydantic `BaseSettings`)
- `api/core/lifespan.py` — Startup (create tables, init pipeline), shutdown
- `api/analysis/pipeline.py` — The core 10-stage pipeline
- `api/db/models.py` — SQLAlchemy ORM models

### Proxy Development

```powershell
# Edit files in proxy/ — auto-restarts in dev mode
docker compose logs -f proxy
```

**Key files to know:**
- `proxy/main.py` — Starts both IMAP and SMTP servers
- `proxy/imap/server.py` — IMAP client handler (LOGIN, CAPABILITY, etc.)
- `proxy/imap/interceptor.py` — FETCH body interception + analysis
- `proxy/smtp/server.py` — SMTP handler (aiosmtpd)
- `proxy/config.py` — Environment-based config

### Dashboard Development

```powershell
# With Docker (hot-reload via Vite)
docker compose up dashboard --build

# Or locally without Docker:
cd dashboard
npm install
npm run dev -- --host 0.0.0.0 --port 4297
```

**Key files to know:**
- `dashboard/src/App.jsx` — Router + auth wrapper
- `dashboard/src/api/client.js` — Axios client with `X-MindWall-Key` interceptor
- `dashboard/src/pages/` — Page components (Dashboard, Alerts, Employees, Settings)
- `dashboard/vite.config.js` — Vite dev server config (port 4297)

### Extension Development

```
1. Edit files in extension/
2. Go to chrome://extensions/
3. Click "Reload" on the MindWall extension
4. Refresh the Gmail tab
```

---

## Database

### Location

- **Docker:** `/srv/app/data/db/mindwall.db` (mounted from `./data/db/`)
- **Host:** `./data/db/mindwall.db`

### Tables

| Table | Purpose |
|-------|---------|
| `employees` | Monitored employees |
| `email_accounts` | IMAP/SMTP credentials per employee |
| `analyses` | All email analysis results |
| `alerts` | Alerts for flagged emails |
| `sender_baselines` | Per-sender behavioural patterns |

### Reset

```powershell
# Via Makefile
make db-reset

# Or manually
Remove-Item ./data/db/mindwall.db
docker compose restart api
```

Tables are auto-created on startup via `api/db/database.py`.

---

## Docker Architecture

### Images

| Service | Base Image | Size |
|---------|-----------|------|
| ollama | `ollama/ollama:latest` | ~2 GB |
| api | `python:3.12-slim` | ~400 MB |
| proxy | `python:3.12-slim` | ~200 MB |
| dashboard | `node:18-alpine` → `nginx:alpine` (production) | ~50 MB |

### Volumes

| Mount | Container Path | Purpose |
|-------|---------------|---------|
| `./data/models` | `/root/.ollama` | Ollama model storage |
| `./data/db` | `/srv/app/data/db` | SQLite database |
| `./api` | `/srv/app` | Dev: API hot-reload |
| `./proxy` | `/app` | Dev: proxy hot-reload |
| `./dashboard` | `/app` | Dev: dashboard hot-reload |

### Rebuilding

```powershell
# Rebuild specific service
docker compose build api --no-cache

# Rebuild and restart
docker compose up -d --build api

# Rebuild everything
docker compose build --no-cache
docker compose up -d
```

---

## Adding a New API Endpoint

1. **Define schema** in `api/schemas/` — Pydantic request/response models
2. **Create router** in `api/routers/` — FastAPI router with endpoint function
3. **Register router** in `api/main.py` — `app.include_router(router, prefix="...")`
4. **Add middleware** if needed — Auth is applied globally via `api/middleware/auth.py`

### Example

```python
# api/routers/my_feature.py
from fastapi import APIRouter, Request
router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint(request: Request):
    return {"status": "ok"}
```

```python
# api/main.py
from .routers import my_feature
app.include_router(my_feature.router, prefix="/api/my-feature", tags=["my-feature"])
```

---

## Adding a New Analysis Dimension

1. **Add to enum** in `api/analysis/dimensions.py` — New `Dimension` member
2. **Set weight** in `DIMENSION_WEIGHTS` — Must sum to 1.0 (adjust others)
3. **Add to registry** in `DIMENSION_REGISTRY` — Name, description, weight
4. **Update LLM prompt** in `api/analysis/prompt_builder.py` — Add dimension to system prompt
5. **Update validation** in `api/analysis/pipeline.py` — Add to `expected_dims` list
6. **Update fallback** in `api/analysis/pipeline.py` — Add to `_fallback_scores`

---

## Logging

MindWall uses **structlog** for structured JSON logging:

```python
import structlog
logger = structlog.get_logger(__name__)
logger.info("pipeline.start", message_uid="12345", sender="user@example.com")
```

Output:
```json
{
  "event": "pipeline.start",
  "message_uid": "12345",
  "sender": "user@example.com",
  "timestamp": "2025-01-15T14:30:00Z",
  "level": "info"
}
```

Log levels are configurable via `LOG_LEVEL` environment variable.

---

## Testing

```powershell
# Run all API tests
cd api
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=term-missing

# Lint
ruff check api/ proxy/
```

---

## Common Development Tasks

### Check service health
```powershell
docker compose ps                    # Service status
curl http://localhost:5297/health     # API health
docker compose logs --tail 20 api    # Recent API logs
docker compose logs --tail 20 proxy  # Recent proxy logs
```

### Inspect the database
```powershell
# Open SQLite shell
sqlite3 ./data/db/mindwall.db

# Useful queries
SELECT COUNT(*) FROM analyses;
SELECT * FROM alerts WHERE acknowledged = 0;
SELECT email, risk_score FROM employees ORDER BY risk_score DESC;
SELECT sender_email, sample_count FROM sender_baselines;
```

### Test the analysis API directly
```powershell
curl -X POST http://localhost:5297/api/analyze `
  -H "Content-Type: application/json" `
  -H "X-MindWall-Key: your-api-key" `
  -d '{
    "message_uid": "test_001",
    "recipient_email": "employee@company.com",
    "sender_email": "test@example.com",
    "subject": "Test Email",
    "body": "This is a test email for analysis.",
    "channel": "imap"
  }'
```
