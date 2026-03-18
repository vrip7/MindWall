# Configuration

> Every environment variable and tunable setting in MindWall.

---

## Environment Variables

All configuration is loaded from environment variables. In Docker, these are set in `docker-compose.yml` or a `.env` file. For local development, copy `.env.example` to `.env`.

### API Service (`mindwall-api`)

| Variable | Default | Description |
|----------|---------|-------------|
| `API_SECRET_KEY` | `changeme` | Shared secret key. Clients send this as `X-MindWall-Key` header. **Change in production.** |
| `DATABASE_URL` | `sqlite+aiosqlite:////app/data/db/mindwall.db` | SQLAlchemy async database URL. |
| `LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `WORKERS` | `4` | Number of Uvicorn worker processes. Use `1` for debugging. |
| `DASHBOARD_USERNAME` | `admin` | Login username for the dashboard. |
| `DASHBOARD_PASSWORD` | `MindWall@2026` | Login password for the dashboard. **Change in production.** |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | URL of the Ollama LLM server (Docker DNS name). |
| `OLLAMA_MODEL` | `qwen3:8b` | Ollama model name for inference. |
| `OLLAMA_TIMEOUT_SECONDS` | `30` | Max seconds to wait for LLM inference. |

### Alert Thresholds

| Variable | Default | Description |
|----------|---------|-------------|
| `ALERT_MEDIUM_THRESHOLD` | `35.0` | Minimum score to generate a `medium` alert. Below this = `low` (no alert). |
| `ALERT_HIGH_THRESHOLD` | `60.0` | Minimum score for `high` severity alert. |
| `ALERT_CRITICAL_THRESHOLD` | `80.0` | Minimum score for `critical` severity alert. |

**Severity mapping:**
```
Score 0–34.99    → low       (no alert created)
Score 35–59.99   → medium    (alert created)
Score 60–79.99   → high      (alert created)
Score 80–100     → critical  (alert created)
```

### Pipeline Weights

| Variable | Default | Description |
|----------|---------|-------------|
| `PREFILTER_SCORE_BOOST` | `15.0` | Maximum additional score from pre-filter signals. Capped at rule-level. |
| `BEHAVIORAL_WEIGHT` | `0.6` | Weight for behavioral deviation engine (0–1). |
| `LLM_WEIGHT` | `0.4` | Weight for LLM dimension scores (0–1). |

The behavioural deviation score for `sender_behavioral_deviation` is blended: `(behavioral * 0.6) + (llm * 0.4)`. All other dimensions use the LLM score directly.

### Proxy Service (`mindwall-proxy`)

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `http://api:5297` | URL of the MindWall API (Docker-internal). |
| `API_SECRET_KEY` | _(empty)_ | Must match the API's `API_SECRET_KEY` for authentication. |
| `IMAP_LISTEN_HOST` | `0.0.0.0` | IMAP proxy bind address. |
| `IMAP_LISTEN_PORT` | `1143` | IMAP proxy port. Email clients connect here. |
| `SMTP_LISTEN_HOST` | `0.0.0.0` | SMTP proxy bind address. |
| `SMTP_LISTEN_PORT` | `1025` | SMTP proxy port for outbound monitoring. |
| `LOG_LEVEL` | `INFO` | Proxy log level. |

### Ollama LLM Server (`mindwall-ollama`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_NUM_PARALLEL` | `4` | Maximum concurrent inference requests. |
| `OLLAMA_MAX_LOADED_MODELS` | `1` | Models kept in GPU memory simultaneously. |
| `OLLAMA_FLASH_ATTENTION` | `1` | Enable flash attention for faster inference. |

### Dashboard (`mindwall-ui`)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:5297` | API URL used by the browser (must be reachable from user's machine). |
| `VITE_WS_URL` | `ws://localhost:5297/ws/alerts` | WebSocket URL for real-time alerts. |

---

## Modifying Settings at Runtime

The Settings page in the dashboard (or `PUT /api/settings`) allows modifying these settings **without restarting**:

- `ollama_timeout_seconds` — Also updates the internal HTTP client timeout.
- `alert_medium_threshold`, `alert_high_threshold`, `alert_critical_threshold` — Affects new analyses only.
- `prefilter_score_boost` — Adjusts pre-filter contribution.
- `behavioral_weight`, `llm_weight` — Adjusts scoring balance.
- `log_level` — Takes effect immediately.

Settings that **require a restart** if changed: `API_SECRET_KEY`, `DATABASE_URL`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `WORKERS`, `DASHBOARD_USERNAME`, `DASHBOARD_PASSWORD`.

---

## .env File

Create a `.env` file in the project root:

```bash
# .env — MindWall environment configuration
API_SECRET_KEY=your-secure-random-key-here
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=YourStrongPassword!
```

Docker Compose reads this file automatically. The `setup.sh` / `setup.ps1` scripts generate this file during first-time setup.

---

## 12-Dimension Weights

Each of the 12 manipulation dimensions has a fixed weight for the aggregate score calculation. These are defined in `api/analysis/dimensions.py`:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| `authority_impersonation` | 0.15 | Highest weight — impersonating authority figures |
| `artificial_urgency` | 0.12 | Manufactured time pressure |
| `fear_threat_induction` | 0.12 | Threats and consequences |
| `sender_behavioral_deviation` | 0.12 | Deviation from sender's baseline |
| `cross_channel_coordination` | 0.08 | Multi-channel attack coordination |
| `reciprocity_exploitation` | 0.07 | Leveraging past favors |
| `scarcity_tactics` | 0.07 | False scarcity signals |
| `emotional_escalation` | 0.07 | Escalating emotional intensity |
| `social_proof_manipulation` | 0.06 | Fabricating consensus |
| `request_context_mismatch` | 0.06 | Request inconsistent with context |
| `unusual_action_requested` | 0.05 | Atypical business requests |
| `timing_anomaly` | 0.03 | Suspicious send timing |

**Total: 1.00**

---

## Behavioral Deviation Weights

The deviation scorer (`api/analysis/behavioral/deviation.py`) uses four sub-components:

| Component | Weight | Description |
|-----------|--------|-------------|
| Word count deviation | 0.30 | How much the email length differs from sender's average |
| Formality deviation | 0.30 | Shift in formal/informal tone |
| Timing deviation | 0.25 | Email sent outside sender's typical hours |
| Sentence length deviation | 0.15 | Average sentence length difference |

The baseline engine uses an **Exponential Moving Average** (EMA) with `alpha = 0.15` to smooth updates. Deviation scoring requires at least **3 samples** from a sender before activating.

---

## Pre-Filter Signal Boosts

Each pre-filter signal adds a fixed score boost:

| Signal | Boost | Pattern type |
|--------|-------|-------------|
| `authority_reference_detected` | +8.0 | CEO/CFO/director/law enforcement mentions |
| `fear_threat_language_detected` | +7.0 | Account suspension/legal action threats |
| `urgency_language_detected` | +5.0 | "Immediately", "ASAP", "act now" |
| `suspicious_request_detected` | +5.0 × count (max +20.0) | Wire transfer, password, gift card |
| `spoofed_sender_pattern` | +10.0 | Domain spoofing patterns |
| `emotional_manipulation_detected` | +4.0 | "Please help", "counting on you" |
| `unusual_send_hour` | +3.0 | Hour < 5 or > 23 |
| `all_caps_subject` | +3.0 | Subject line entirely uppercase |
| `excessive_exclamation_marks` | +2.0 | More than 3 exclamation marks |
