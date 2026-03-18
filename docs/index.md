# MindWall Documentation

> **Cognitive Firewall — AI-Powered Human Manipulation Detection Engine**
>
> Developed by [Pradyumn Tandon](https://pradyumntandon.com) at [VRIP7](https://vrip7.com) · [GitHub](https://github.com/vrip7/mindwall)

---

## What is MindWall?

MindWall is an enterprise-grade, privacy-first system that detects **psychological manipulation** in business email communications. Traditional email security focuses on malware signatures and phishing URLs — MindWall goes deeper, analysing the *cognitive intent* behind messages using a 12-dimension behavioral framework backed by fine-tuned large language models running entirely on-premises.

Every incoming email is scored across twelve manipulation dimensions — urgency exploitation, authority fabrication, emotional coercion, social proof manufacturing, and eight more — producing a single 0–100 risk score with an actionable recommended response (proceed / verify / block). Zero data ever leaves the deployment boundary.

---

## Documentation Map

| Guide | Description |
|-------|-------------|
| [Getting Started](getting-started.md) | Prerequisites, one-command install, first-run verification |
| [Architecture](architecture.md) | System design, data flow, component interaction |
| [Configuration](configuration.md) | Every environment variable and tunable parameter |
| [API Reference](api-reference.md) | Complete REST + WebSocket endpoint documentation |
| [Dashboard Guide](dashboard.md) | Using the React real-time monitoring dashboard |
| [Email Client Setup](email-client-setup.md) | Configuring Thunderbird, Outlook, Apple Mail with the proxy |
| [Browser Extension](browser-extension.md) | Chrome/Firefox extension for Gmail web interception |
| [Proxy Internals](proxy.md) | IMAP/SMTP proxy deep-dive — protocol handling, interception, injection |
| [Analysis Pipeline](analysis-pipeline.md) | The 10-stage pipeline: pre-filter → LLM → scoring → alerting |
| [Fine-Tuning](fine-tuning.md) | QLoRA training pipeline for custom model adaptation |
| [Development](development.md) | Local development, project structure, testing, contributing |
| [Security](security.md) | Threat model, authentication, credential handling, network isolation |
| [Troubleshooting](troubleshooting.md) | Common errors, diagnostic commands, FAQ |

---

## Quick Links

- **Dashboard**: `http://localhost:4297`
- **API Health**: `http://localhost:5297/health`
- **API Docs** (debug mode): `http://localhost:5297/docs`
- **Ollama Status**: `http://localhost:11434/api/tags`

---

## Service Ports

| Port | Service | Protocol |
|------|---------|----------|
| 4297 | React Dashboard | HTTP |
| 5297 | FastAPI Engine | HTTP / WebSocket |
| 1143 | IMAP Proxy | IMAP (plaintext to proxy, TLS to upstream) |
| 1025 | SMTP Proxy | SMTP (plaintext to proxy, TLS to upstream) |
| 11434 | Ollama LLM | HTTP (internal only) |
