# API Reference

> Complete HTTP and WebSocket endpoint documentation.

**Base URL**: `http://localhost:5297`  
**Authentication**: All endpoints except `/auth/login` and `/health` require the `X-MindWall-Key` header.

---

## Authentication

### POST `/auth/login`

Validate dashboard credentials and retrieve the API key.

**Request:**
```json
{
  "username": "admin",
  "password": "MindWall@2026"
}
```

**Response (200):**
```json
{
  "api_key": "your-api-secret-key"
}
```

**Response (401):**
```json
{
  "detail": "Invalid username or password"
}
```

**Notes:** Uses constant-time comparison (`hmac.compare_digest`) to prevent timing attacks.

---

## Health Check

### GET `/health`

**No authentication required.**

**Response (200):**
```json
{
  "status": "ok"
}
```

---

## Analysis

### POST `/api/analyze`

Submit an email for psychological manipulation analysis. Called by the IMAP proxy and browser extension.

**Headers:**
```
X-MindWall-Key: your-api-secret-key
```

**Request:**
```json
{
  "message_uid": "imap_12345",
  "recipient_email": "employee@company.com",
  "sender_email": "external@sender.com",
  "sender_display_name": "John Smith",
  "subject": "Urgent: Wire Transfer Required",
  "body": "Plain text email body content...",
  "channel": "imap",
  "received_at": "2025-01-15T14:30:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message_uid` | string | Yes | Unique ID — IMAP UID or extension-generated hash |
| `recipient_email` | string | Yes | Employee's email address |
| `sender_email` | string | Yes | External sender's email |
| `sender_display_name` | string | No | Sender's display name |
| `subject` | string | No | Email subject line |
| `body` | string | Yes | Plain-text email body |
| `channel` | string | Yes | `imap` or `gmail_web` |
| `received_at` | datetime | No | Original email timestamp (ISO 8601) |

**Response (200):**
```json
{
  "analysis_id": 42,
  "manipulation_score": 73.5,
  "severity": "high",
  "explanation": "This email exhibits strong authority impersonation...",
  "recommended_action": "verify",
  "dimension_scores": {
    "artificial_urgency": 85.0,
    "authority_impersonation": 92.0,
    "fear_threat_induction": 45.0,
    "reciprocity_exploitation": 0.0,
    "scarcity_tactics": 30.0,
    "social_proof_manipulation": 0.0,
    "sender_behavioral_deviation": 67.0,
    "cross_channel_coordination": 0.0,
    "emotional_escalation": 20.0,
    "request_context_mismatch": 88.0,
    "unusual_action_requested": 75.0,
    "timing_anomaly": 15.0
  },
  "processing_time_ms": 2340
}
```

| Field | Type | Description |
|-------|------|-------------|
| `manipulation_score` | float | Aggregate score 0–100 |
| `severity` | string | `low`, `medium`, `high`, or `critical` |
| `recommended_action` | string | `proceed`, `verify`, or `block` |
| `dimension_scores` | object | 12-dimension individual scores (0–100 each) |

---

## Dashboard

### GET `/api/dashboard/summary`

Organisation-wide threat summary statistics.

**Response (200):**
```json
{
  "total_analyses": 1250,
  "average_score": 28.4,
  "high_risk_count": 45,
  "critical_count": 12,
  "average_processing_ms": 1850.0,
  "unacknowledged_alerts": {
    "low": 0,
    "medium": 23,
    "high": 8,
    "critical": 3
  },
  "employee_count": 15,
  "avg_dimension_scores": {
    "artificial_urgency": 22.5,
    "authority_impersonation": 18.3
  },
  "heatmap_data": {
    "data": [[12.5, 45.0, null], [33.2, 22.1, 67.8]],
    "row_labels": ["employee1@co.com", "employee2@co.com"],
    "col_labels": ["artificial_urgency", "authority_impersonation", "fear_threat_induction"]
  }
}
```

### GET `/api/dashboard/timeline`

Aggregated threat score timeline.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | datetime | None | Start of the time range (ISO 8601) |
| `end_date` | datetime | None | End of the time range |
| `limit` | int | 100 | Max entries (1–1000) |

**Response (200):**
```json
{
  "entries": [
    {
      "bucket": "2025-01-15T00:00:00Z",
      "avg_score": 34.2,
      "count": 45
    }
  ],
  "start_date": "2025-01-01T00:00:00Z",
  "end_date": "2025-01-15T23:59:59Z"
}
```

---

## Alerts

### GET `/api/alerts`

Paginated alert list with optional filters.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `severity` | string | None | Filter: `low`, `medium`, `high`, `critical` |
| `acknowledged` | bool | None | Filter by acknowledgement status |
| `limit` | int | 20 | Items per page (1–100) |
| `offset` | int | 0 | Pagination offset |

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "analysis_id": 42,
      "severity": "high",
      "acknowledged": false,
      "acknowledged_by": null,
      "acknowledged_at": null,
      "created_at": "2025-01-15T14:32:00Z",
      "recipient_email": "employee@company.com",
      "sender_email": "attacker@evil.com",
      "subject": "Urgent: Wire Transfer",
      "manipulation_score": 73.5,
      "explanation": "Strong authority impersonation...",
      "recommended_action": "verify"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

### GET `/api/alerts/{alert_id}`

Full alert detail with dimension breakdown.

**Response (200):** All fields from `AlertSummary` plus:
```json
{
  "sender_display_name": "John Smith",
  "dimension_scores": { ... },
  "channel": "imap",
  "received_at": "2025-01-15T14:30:00Z",
  "analyzed_at": "2025-01-15T14:30:02Z",
  "prefilter_triggered": true,
  "prefilter_signals": ["urgency_language_detected", "authority_reference_detected"],
  "processing_time_ms": 2340
}
```

### PATCH `/api/alerts/{alert_id}/acknowledge`

Mark an alert as reviewed.

**Request:**
```json
{
  "acknowledged_by": "admin"
}
```

**Response (200):**
```json
{
  "status": "acknowledged",
  "alert_id": 1
}
```

---

## Employees

### GET `/api/employees`

Paginated employee list with rolling risk scores.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 100 | Items per page (1–500) |
| `offset` | int | 0 | Pagination offset |
| `sort_by_risk` | bool | true | Sort by risk score descending |

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "email": "employee@company.com",
      "display_name": "Jane Doe",
      "department": "Finance",
      "risk_score": 45.2,
      "total_emails": 250,
      "flagged_emails": 12,
      "email_account_configured": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-15T14:30:00Z"
    }
  ],
  "total": 15,
  "limit": 100,
  "offset": 0
}
```

### POST `/api/employees`

Create a new employee and optionally configure their email account.

**Request:**
```json
{
  "email": "newuser@company.com",
  "display_name": "New User",
  "department": "Engineering",
  "imap_host": "imap.gmail.com",
  "imap_port": 993,
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "username": "newuser@company.com",
  "password": "app-specific-password",
  "use_tls": true
}
```

If `imap_host`, `smtp_host`, `username`, and `password` are all provided, an email account is created and proxy connection info is returned.

**Response (201):**
```json
{
  "employee": {
    "id": 2,
    "email": "newuser@company.com",
    "display_name": "New User",
    "department": "Engineering",
    "risk_score": 0.0,
    "total_emails": 0,
    "flagged_emails": 0,
    "email_account_configured": true,
    "created_at": "2025-01-15T15:00:00Z",
    "updated_at": "2025-01-15T15:00:00Z"
  },
  "email_account_configured": true,
  "proxy_connection": {
    "imap_proxy_host": "localhost",
    "imap_proxy_port": 1143,
    "smtp_proxy_host": "localhost",
    "smtp_proxy_port": 1025,
    "username": "newuser@company.com"
  }
}
```

### DELETE `/api/employees/{employee_id}`

Delete an employee and their associated email account.

**Response**: `204 No Content`

### GET `/api/employees/{email}/proxy-info`

Get proxy connection info for an employee.

**Response (200):**
```json
{
  "imap_proxy_host": "localhost",
  "imap_proxy_port": 1143,
  "smtp_proxy_host": "localhost",
  "smtp_proxy_port": 1025,
  "username": "newuser@company.com",
  "original_imap": "imap.gmail.com:993",
  "original_smtp": "smtp.gmail.com:587",
  "use_tls": true,
  "enabled": true
}
```

### GET `/api/employees/{email}/risk-profile`

Full risk profile including sender baselines.

**Response (200):**
```json
{
  "email": "employee@company.com",
  "display_name": "Jane Doe",
  "department": "Finance",
  "rolling_risk_score": 45.2,
  "total_emails": 250,
  "flagged_emails": 12,
  "total_analyses": 250,
  "avg_dimension_scores": {
    "artificial_urgency": 22.5,
    "authority_impersonation": 18.3
  },
  "top_threat_senders": [
    {
      "sender_email": "suspicious@external.com",
      "avg_score": 67.8,
      "count": 5
    }
  ],
  "recent_analyses": [
    {
      "message_uid": "imap_12345",
      "sender_email": "external@sender.com",
      "subject": "Re: Budget",
      "manipulation_score": 15.2,
      "severity": "low",
      "analyzed_at": "2025-01-15T14:30:00Z"
    }
  ],
  "recent_alerts": []
}
```

---

## Email Accounts

### GET `/api/email-accounts`

List all configured email accounts (passwords redacted).

**Response (200):**
```json
[
  {
    "id": 1,
    "email": "user@company.com",
    "display_name": "User Name",
    "imap_host": "imap.gmail.com",
    "imap_port": 993,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "user@company.com",
    "use_tls": true,
    "enabled": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

### POST `/api/email-accounts`

Create or update an email account (upsert by email).

**Request:**
```json
{
  "email": "user@company.com",
  "display_name": "User Name",
  "imap_host": "imap.gmail.com",
  "imap_port": 993,
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "username": "user@company.com",
  "password": "app-specific-password",
  "use_tls": true,
  "enabled": true
}
```

### GET `/api/email-accounts/lookup/{username}`

**Internal use only.** Resolve upstream server config by login username. Used by the IMAP/SMTP proxy to auto-discover the upstream server for a given user.

**Response (200):** Full account config including password.

### DELETE `/api/email-accounts/{account_id}`

Delete an email account configuration.

**Response**: `204 No Content`

---

## Settings

### GET `/api/settings`

Get current system settings.

**Response (200):**
```json
{
  "ollama_base_url": "http://ollama:11434",
  "ollama_model": "qwen3:8b",
  "ollama_timeout_seconds": 30,
  "alert_medium_threshold": 35.0,
  "alert_high_threshold": 60.0,
  "alert_critical_threshold": 80.0,
  "prefilter_score_boost": 15.0,
  "behavioral_weight": 0.6,
  "llm_weight": 0.4,
  "log_level": "INFO",
  "workers": 4
}
```

### PUT `/api/settings`

Update system settings (partial update — only include fields to change).

**Request:**
```json
{
  "ollama_timeout_seconds": 45,
  "alert_medium_threshold": 40.0,
  "log_level": "DEBUG"
}
```

**Validation:**
- `ollama_timeout_seconds`: 5–120
- Thresholds: 0–100
- `prefilter_score_boost`: 0–50
- `behavioral_weight` / `llm_weight`: 0–1
- `log_level`: `DEBUG`, `INFO`, `WARNING`, `ERROR`

**Response (200):** Updated `SystemSettings` object.

---

## WebSocket

### WS `/ws/alerts`

Real-time alert stream for the dashboard.

**Connection:**
```javascript
const ws = new WebSocket("ws://localhost:5297/ws/alerts");
```

**Incoming Events:**
```json
{
  "event": "new_alert",
  "alert_id": 5,
  "analysis_id": 42,
  "recipient_email": "employee@company.com",
  "sender_email": "attacker@evil.com",
  "subject": "Urgent: Wire Transfer",
  "manipulation_score": 73.5,
  "severity": "high",
  "explanation": "Strong authority impersonation...",
  "recommended_action": "verify",
  "dimension_scores": { ... }
}
```

**Keep-alive:** Send `"ping"` text frames to receive `"pong"` responses.

---

## Error Responses

All errors follow the FastAPI standard format:

```json
{
  "detail": "Error description"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request / validation error |
| 401 | Missing or invalid `X-MindWall-Key` |
| 404 | Resource not found |
| 409 | Duplicate resource (e.g. duplicate email) |
| 422 | Request validation error (Pydantic) |
| 500 | Internal server error |
