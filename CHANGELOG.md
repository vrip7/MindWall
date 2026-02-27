# Changelog

All notable changes to MindWall will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2025-01-01

### Added

- **Core Analysis Engine** — FastAPI-based 12-dimension manipulation analysis pipeline
- **IMAP/SMTP Proxy** — Transparent asyncio proxy for intercepting email communications
- **LLM Integration** — Ollama client for local Llama 3.1 8B inference with structured JSON output
- **Behavioral Baseline Engine** — Per-sender communication pattern learning and deviation scoring
- **Rule-Based Pre-Filter** — Fast keyword and regex pre-screening (zero GPU cost)
- **12-Dimension Scoring** — Urgency, authority, emotional coercion, social proof, scarcity/FOMO, reciprocity, commitment escalation, identity manipulation, information asymmetry, trust exploitation, cognitive overload, isolation tactics
- **React Dashboard** — Real-time threat monitoring with WebSocket alerts, dimension radar, risk heatmap, employee risk profiles
- **Browser Extension** — Manifest V3 Chrome/Firefox extension for Gmail web intercept
- **Fine-Tuning Pipeline** — Unsloth QLoRA training, synthetic data generator, evaluation framework, GGUF export for Ollama
- **Docker Compose** — Full production orchestration with NVIDIA GPU passthrough, health checks, internal networking
- **Setup Scripts** — One-command setup for Linux/macOS (`setup.sh`) and Windows (`setup.ps1`)
- **Structured Logging** — JSON-formatted logs via structlog with request ID tracing
- **API Authentication** — Secret key-based internal API authentication
- **WebSocket Alerts** — Real-time push notifications for high-severity threats
- **Clinical-Grade System Prompt** — Comprehensive LLM prompt with scoring calibration, behavioral constraints, and strict output contract

### Security

- All inference runs on-premises — zero data leaves the deployment boundary
- SQLite database with no network exposure
- TLS termination for upstream mail server connections
- Docker internal network isolation between services
