# Changelog

All notable changes to MindWall will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] — 2026-03-18

### Added

- **Example Phishing Emails** — 10 curated example emails (`examples/`) covering CEO fraud, account suspension, invoice scam, prize winner, IT support scam, colleague impersonation, shipping notification, tax refund, job offer scam, plus a legitimate control email
- **Test Runner Script** — `examples/test_examples.py` to batch-submit all examples against the API with colored terminal output and dimension bar charts

### Fixed

- **structlog event= collision** — Fixed `event=` keyword argument in `api/websocket/manager.py` conflicting with structlog's positional event parameter, causing HTTP 500 on high-scoring emails that triggered WebSocket broadcast

---

## [1.0.0] — 2025-01-01

### Added

- **Core Analysis Engine** — FastAPI-based 10-stage analysis pipeline with 12-dimension manipulation scoring on port 5297
- **IMAP/SMTP Proxy** — Transparent asyncio IMAP proxy (:1143) and SMTP relay (:1025) with automatic upstream server resolution from the API, raw byte forwarding, and decoupled analysis via asyncio queue
- **LLM Integration** — Ollama client for local Qwen3-8B inference with structured JSON output (GPU-only, Docker-internal network)
- **Behavioral Baseline Engine** — Per-sender communication pattern learning with EMA deviation scoring
- **Rule-Based Pre-Filter** — Fast keyword and regex pre-screening (zero GPU cost) with configurable score boost
- **12-Dimension Scoring** — Weighted aggregate scoring across: authority impersonation (0.15), artificial urgency (0.12), fear/threat induction (0.12), sender behavioral deviation (0.12), cross-channel coordination (0.08), reciprocity exploitation (0.07), scarcity tactics (0.07), emotional escalation (0.07), social proof manipulation (0.06), request/context mismatch (0.06), unusual action requested (0.05), timing anomaly (0.03)
- **Severity Classification** — Four-tier system: low (0–34, proceed), medium (35–59, verify + alert), high (60–79, verify + alert), critical (80–100, block + alert)
- **React Dashboard** — Real-time threat monitoring UI on port 4297 (React 18 + Tailwind CSS + Recharts + Vite) with threat gauge, timeline chart, dimension radar, risk heatmap, filterable alert feed, employee management, and runtime settings
- **Browser Extension** — Manifest V3 Chrome extension for Gmail web intercept via MutationObserver DOM injection with inline risk badges
- **Fine-Tuning Pipeline** — Unsloth QLoRA training for Qwen3-4B (r=8, alpha=16), synthetic data generator, evaluation framework, GGUF q4_k_m export for Ollama
- **Docker Compose** — Full production orchestration with NVIDIA GPU passthrough, health checks, dual-network isolation (`mindwall-internal` + `mindwall-host`)
- **Setup Scripts** — One-command setup for Linux/macOS (`setup.sh`) and Windows (`setup.ps1`) with automatic secret generation
- **Structured Logging** — JSON-formatted logs via structlog with UUID4 request ID tracing across services
- **API Authentication** — `X-MindWall-Key` header with constant-time `hmac.compare_digest()` validation
- **Dashboard Authentication** — Username/password login returning API key for frontend session
- **WebSocket Alerts** — Real-time push notifications at `/ws/alerts` for medium/high/critical severity threats
- **Clinical-Grade System Prompt** — Comprehensive LLM prompt with scoring calibration, behavioral constraints, and strict JSON output contract
- **Runtime Settings** — Dashboard settings page and `PUT /api/settings` for adjusting thresholds, weights, and LLM timeout without restart
- **Employee Management** — Employee + email account CRUD with per-employee risk profiles and upstream IMAP/SMTP configuration

### Security

- All inference runs on-premises — zero data leaves the deployment boundary
- Ollama on Docker-internal network (`internal: true`) with no internet access
- SQLite database with no network exposure
- TLS termination for upstream mail server connections (proxy handles plaintext locally, TLS to upstream)
- Constant-time API key comparison to prevent timing attacks
- Email bodies processed in-memory and discarded after analysis — not persisted
- No credentials logged; sender/recipient addresses appear only at INFO level
- Non-root Docker containers
