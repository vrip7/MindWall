# Security

> Authentication model, credential management, and network isolation in MindWall.

---

## Authentication

### API Authentication

All API endpoints (except `/health` and `/auth/login`) are protected by the `X-MindWall-Key` header:

```
X-MindWall-Key: your-api-secret-key
```

The key is validated in `api/middleware/auth.py`:
- Uses `hmac.compare_digest()` for **constant-time comparison** (prevents timing attacks)
- Returns `401 Unauthorized` if the key is missing or invalid
- The key is configured via the `API_SECRET_KEY` environment variable

### Dashboard Login

The dashboard uses a separate login flow:

1. User submits `username` + `password` to `POST /auth/login`
2. Server validates using `hmac.compare_digest()` against `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD`
3. On success, returns `{"api_key": "<API_SECRET_KEY>"}`
4. Frontend stores the key in-memory and attaches to all subsequent API calls

### Proxy Authentication

The IMAP/SMTP proxy authenticates with the API using the same `X-MindWall-Key`:

```yaml
# docker-compose.yml
proxy:
  environment:
    - API_SECRET_KEY=${API_SECRET_KEY}
```

The proxy sets this header on all requests to the API (analysis submissions, account lookups).

---

## Credential Storage

### Email Account Passwords

Email account passwords (IMAP/SMTP credentials) are stored in the SQLite database:

- Stored in the `email_accounts` table
- Passwords are stored as-is (not hashed) because the proxy needs the **plaintext** password to authenticate with upstream mail servers
- The `GET /api/email-accounts` endpoint **redacts passwords** in the response
- The `GET /api/email-accounts/lookup/{username}` endpoint returns the full password but is protected by the `X-MindWall-Key` header

### API Secret Key

The `API_SECRET_KEY` should be treated as a deployment secret:

- Set via `.env` file (not committed to version control)
- The `setup.sh` / `setup.ps1` scripts generate a random key during initial setup
- Shared between the API, proxy, and dashboard

---

## Network Isolation

### Docker Networks

MindWall uses two Docker networks for defence-in-depth:

| Network | Type | Members | Internet |
|---------|------|---------|----------|
| `mindwall-internal` | Bridge, `internal: true` | ollama, api | **No internet access** |
| `mindwall-host` | Bridge | api, proxy, dashboard | Yes |

**Key isolation properties:**
- The Ollama LLM server **cannot access the internet**. It runs on the internal-only network and can only communicate with the API.
- The API bridges both networks — it reaches Ollama internally and serves HTTP externally.
- The proxy and dashboard only need external network access.

### Port Exposure

Only three ports are exposed to the host:

| Port | Service | Protocol |
|------|---------|----------|
| 5297 | API | HTTP + WebSocket |
| 1143 | Proxy | IMAP |
| 1025 | Proxy | SMTP |
| 4297 | Dashboard | HTTP |

The Ollama port (11434) is **not exposed** to the host — it's only accessible within the Docker internal network.

---

## Request Tracing

Every API request receives a unique `X-Request-ID` via `api/middleware/request_id.py`:

- Generated as a UUID4 string
- Attached to all log entries for that request
- Returned in the response headers
- Enables end-to-end request tracing across services

---

## Data Privacy

### What MindWall Stores

| Data | Location | Purpose | Retention |
|------|----------|---------|-----------|
| Email metadata | `analyses` table | Analysis records | Indefinite |
| Manipulation scores | `analyses` table | Risk assessment | Indefinite |
| LLM explanations | `analyses` table | Human review | Indefinite |
| Sender baselines | `sender_baselines` table | Behavioural detection | Indefinite |
| Email credentials | `email_accounts` table | Upstream auth | Until deleted |

### What MindWall Does NOT Store

- **Full email bodies** — Only the analysis results are persisted. The raw email text is processed in-memory and discarded after analysis.
- **Email attachments** — The MIME parser skips binary attachments entirely.
- **Personal browsing data** — The extension only activates on Gmail.

### Logging

- Structured JSON logs via structlog
- No email body content is logged
- No passwords are logged
- Sender/recipient email addresses appear in logs only at INFO level for tracing
- Log level is configurable (`LOG_LEVEL` environment variable)

---

## Security Headers

The proxy adds extra headers to IMAP responses for flagged emails:

```
X-MindWall-Score: 73.5
X-MindWall-Severity: critical
```

These are informational headers only — the actual protection comes from the subject line badges and dashboard alerts.

---

## Changing Default Credentials

After initial setup, change the following in your `.env` file:

```bash
# Generate a long random key
API_SECRET_KEY=$(openssl rand -hex 32)

# Set strong dashboard credentials
DASHBOARD_USERNAME=your_admin_username
DASHBOARD_PASSWORD=YourStr0ng!P@ssword
```

Then restart:
```powershell
docker compose down
docker compose up -d
```

---

## Limitations

- **No HTTPS on proxy** — The IMAP/SMTP proxy runs plaintext on localhost. This is by design (the proxy handles TLS to the upstream server). For remote deployments, wrap in a TLS-terminating reverse proxy.
- **No RBAC** — Single shared API key for all clients. No per-user roles or permissions.
- **No encryption at rest** — SQLite database is not encrypted. For sensitive deployments, use full-disk encryption on the host.
- **Plaintext credential storage** — Email passwords are stored unencrypted because the proxy needs plaintext passwords. Consider encrypting at rest using application-level encryption if needed.
