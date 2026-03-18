# Troubleshooting

> Common issues, diagnostic commands, and solutions.

---

## Quick Diagnostics

```powershell
# Check all services are running
docker compose ps

# Expected output: all services "running" or "healthy"
# mindwall-ollama   running (healthy)
# mindwall-api      running (healthy)
# mindwall-proxy    running
# mindwall-ui       running

# Check API health
curl http://localhost:5297/health
# Expected: {"status":"ok"}

# View recent logs (all services)
docker compose logs --tail 50

# View specific service logs
docker compose logs --tail 50 api
docker compose logs --tail 50 proxy
docker compose logs --tail 50 ollama
docker compose logs --tail 50 dashboard
```

---

## Container Issues

### Services won't start

**Symptom:** `docker compose up` fails or containers keep restarting.

```powershell
# Check for startup errors
docker compose logs ollama --tail 20
docker compose logs api --tail 20

# Common causes:
# 1. Ollama: No NVIDIA GPU detected
#    Solution: Install NVIDIA Container Toolkit
#    https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

# 2. API: Ollama not healthy yet
#    The API depends on Ollama being healthy. Wait for Ollama to start first:
docker compose up ollama -d
docker compose logs -f ollama  # Wait for "healthy" status
docker compose up -d           # Start remaining services

# 3. Port conflicts
#    Check if ports 5297, 4297, 1143, or 1025 are in use:
netstat -ano | findstr "5297 4297 1143 1025"
```

### GPU not detected

```powershell
# Verify NVIDIA Container Toolkit
docker run --gpus all nvidia/cuda:12.0-base nvidia-smi

# If this fails, install the toolkit:
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

# Check Ollama GPU usage
docker compose exec ollama nvidia-smi
```

### Out of disk space

```powershell
# Clean Docker resources
docker system prune -a --volumes

# Check Ollama model sizes
docker compose exec ollama ollama list

# Remove unused models
docker compose exec ollama ollama rm <model-name>
```

---

## IMAP Proxy Issues

### "Connection refused" when connecting email client

```powershell
# 1. Verify proxy is running
docker compose ps proxy

# 2. Check proxy is listening
docker compose logs proxy --tail 20
# Look for: "IMAP server started on 0.0.0.0:1143"

# 3. Test connection directly
# In PowerShell:
Test-NetConnection -ComputerName localhost -Port 1143
```

### Authentication fails

```powershell
# 1. Check proxy logs for the auth attempt
docker compose logs proxy --tail 50
# Look for: imap.login_attempt, imap.account_not_found, imap.auth_failed

# 2. Verify the email account exists in MindWall
curl -H "X-MindWall-Key: your-api-key" http://localhost:5297/api/email-accounts
# Check that the username matches what your email client sends

# 3. Common causes:
# - Email account not configured in MindWall (add via dashboard Employees page)
# - Wrong password (update via the dashboard)
# - Username mismatch (must be the exact email address used for login)
# - Email client trying TLS/SSL (set encryption to "None")
```

### "BAD Not authenticated" errors

The email client is sending commands that require authentication before actually logging in.

```powershell
# Check which command is failing
docker compose logs proxy --tail 30 | grep "BAD"

# Common fix: Ensure encryption is set to "None" in your email client
# When encryption is set to STARTTLS, clients try STARTTLS before LOGIN
# The proxy rejects STARTTLS (it runs plaintext locally)
```

### Emails not being analysed

```powershell
# 1. Check interceptor logs
docker compose logs proxy --tail 50
# Look for: "interceptor" or "submit_for_analysis" entries

# 2. Check API logs for analysis requests
docker compose logs api --tail 50
# Look for: "pipeline.start" and "pipeline.complete"

# 3. Verify API is reachable from proxy
docker compose exec proxy curl http://api:5297/health

# 4. Common causes:
# - API_SECRET_KEY mismatch between proxy and API
# - Email body too short (very short emails may not trigger interception)
```

---

## SMTP Proxy Issues

### Outgoing mail not sent

```powershell
# 1. Check for SMTP errors
docker compose logs proxy --tail 30

# 2. Verify upstream SMTP configuration
# The proxy auto-resolves from the API. Check the email account:
curl -H "X-MindWall-Key: your-key" "http://localhost:5297/api/email-accounts/lookup/youremail@gmail.com"

# 3. Common causes:
# - Gmail: App Password not configured (regular password won't work)
# - Upstream SMTP server rejects the connection (firewall, rate limit)
# - Wrong SMTP port in email account configuration (usually 587 for Gmail)
```

---

## Dashboard Issues

### Can't access dashboard

```powershell
# 1. Check dashboard container
docker compose ps dashboard
docker compose logs dashboard --tail 20

# 2. Verify port
curl http://localhost:4297

# 3. Check if Vite dev server is running (dev mode)
docker compose logs dashboard --tail 20
# Look for: "Local: http://localhost:4297/"
```

### Login fails

```powershell
# 1. Verify credentials
# Default: admin / MindWall@2026
# Or check your .env file for DASHBOARD_USERNAME / DASHBOARD_PASSWORD

# 2. Test API directly
curl -X POST http://localhost:5297/auth/login `
  -H "Content-Type: application/json" `
  -d '{"username":"admin","password":"MindWall@2026"}'

# 3. Check API logs
docker compose logs api --tail 20
```

### Dashboard shows no data

```powershell
# 1. Check if any analyses exist
curl -H "X-MindWall-Key: your-key" http://localhost:5297/api/dashboard/summary
# total_analyses should be > 0

# 2. Check WebSocket connection
# Open browser DevTools → Network → WS tab
# Look for ws://localhost:5297/ws/alerts connection

# 3. Check API connectivity from browser
# Open browser DevTools → Console
# Look for CORS or network errors
```

---

## LLM / Ollama Issues

### Model not loaded

```powershell
# List available models
docker compose exec ollama ollama list

# Pull the default model
docker compose exec ollama ollama pull qwen3:8b

# Or via Makefile
make pull-model
```

### Slow inference

```powershell
# Check GPU utilisation
docker compose exec ollama nvidia-smi

# Verify flash attention is enabled
# In docker-compose.yml: OLLAMA_FLASH_ATTENTION=1

# Check concurrent requests
# Set OLLAMA_NUM_PARALLEL based on your GPU memory:
# 8GB VRAM → OLLAMA_NUM_PARALLEL=2
# 16GB VRAM → OLLAMA_NUM_PARALLEL=4
# 24GB VRAM → OLLAMA_NUM_PARALLEL=6
```

### LLM returning invalid JSON

```powershell
# Check API logs for JSON parse errors
docker compose logs api --tail 50 | grep "llm_error"

# The pipeline has a fallback — if LLM returns invalid JSON:
# - Uses prefilter scores only
# - All 12 dimensions default to 0
# - Only prefilter boost is applied

# To diagnose, test Ollama directly:
docker compose exec ollama ollama run qwen3:8b "Respond with JSON: {\"test\": true}"
```

---

## Database Issues

### Corrupted database

```powershell
# Check database integrity
sqlite3 ./data/db/mindwall.db "PRAGMA integrity_check;"
# Should return: "ok"

# If corrupted, reset:
Remove-Item ./data/db/mindwall.db
docker compose restart api
# Tables will be auto-created on startup
```

### Duplicate analysis errors

```
IntegrityError: UNIQUE constraint failed: analyses.message_uid, analyses.recipient_email
```

This is expected — it means the same email was submitted twice (e.g. IMAP re-fetch). The unique constraint prevents duplicate processing.

---

## Network Issues

### API can't reach Ollama

```powershell
# Test internal network connectivity
docker compose exec api curl http://ollama:11434/api/version

# If this fails, check networks
docker network ls | grep mindwall
docker network inspect mindwall_mindwall-internal
# Both 'ollama' and 'api' should be attached
```

### Proxy can't reach API

```powershell
# Test from proxy container
docker compose exec proxy curl http://api:5297/health

# Verify API_BASE_URL in proxy environment
docker compose exec proxy printenv API_BASE_URL
# Should be: http://api:5297
```

---

## Rebuild Everything

When in doubt, a clean rebuild resolves most issues:

```powershell
# Stop everything
docker compose down

# Rebuild all images from scratch
docker compose build --no-cache

# Start fresh
docker compose up -d

# Pull model if needed
docker compose exec ollama ollama pull qwen3:8b

# Verify
docker compose ps
curl http://localhost:5297/health
```

---

## Log Level Reference

Set `LOG_LEVEL` in environment variables:

| Level | Shows |
|-------|-------|
| `DEBUG` | Everything — request bodies, SQL queries, full pipeline details |
| `INFO` | Normal operations — auth events, pipeline start/complete, alerts |
| `WARNING` | Potential issues — slow inference, fallback activation |
| `ERROR` | Failures — LLM errors, database errors, connection failures |

For debugging, set `LOG_LEVEL=DEBUG` in your `.env` file and restart.
