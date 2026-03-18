# Dashboard

> Real-time monitoring interface for MindWall.

**URL**: `http://localhost:4297`

---

## Login

The dashboard is protected by a login screen. Default credentials:

| Field | Default |
|-------|---------|
| Username | `admin` |
| Password | `MindWall@2026` |

On successful login, the frontend receives the API secret key and stores it in-memory. All subsequent API calls include the key as the `X-MindWall-Key` header.

---

## Overview Page

The main dashboard displays organisation-wide threat statistics:

### Stat Cards (Top Row)

| Card | Source | Description |
|------|--------|-------------|
| Total Emails Analyzed | `total_analyses` | Count of all emails processed |
| Average Risk Score | `average_score` | Organisation-wide mean manipulation score |
| Active Alerts | `unacknowledged_alerts.total` | Unreviewed alerts requiring attention |
| High Risk Emails | `high_risk_count` | Emails scoring ≥ 60 |

### Charts

| Component | Type | Description |
|-----------|------|-------------|
| **ThreatGauge** | Gauge chart | Circular gauge showing current average threat level (0–100) with color zones |
| **ThreatTimeline** | Area chart | Time-series of average manipulation scores over the selected date range |
| **DimensionRadar** | Radar chart | 12-axis radar showing average scores across all manipulation dimensions |
| **RiskHeatmap** | Heatmap grid | Employees × dimensions matrix with colour-coded cells |

### Auto-Refresh

The dashboard polls `GET /api/dashboard/summary` every **30 seconds** to update stats and charts.

---

## Alerts Page

Lists all alerts with filtering and detail views.

### Filter Options

- **Severity**: All, Low, Medium, High, Critical
- **Status**: All, Unacknowledged, Acknowledged
- **Pagination**: Configurable page size

### Alert List

Each alert shows:
- Severity badge (colour-coded)
- Sender email and display name
- Recipient email
- Subject line
- Manipulation score
- Time since creation
- Acknowledgement status

### Alert Detail Panel

Clicking an alert opens a detail view with:
- Full 12-dimension breakdown (individual scores)
- LLM-generated explanation
- Recommended action (`proceed` / `verify` / `block`)
- Pre-filter signals triggered
- Processing time
- Original email metadata
- **Acknowledge** button for marking as reviewed

---

## Employees Page

Employee management with email account configuration.

### Employee Table

| Column | Description |
|--------|-------------|
| Name / Email | Employee display name and address |
| Department | Organisational unit |
| Risk Score | 30-day rolling average manipulation score |
| Total Emails | Total emails analysed for this employee |
| Flagged Emails | Emails that triggered alerts (score ≥ 35) |
| Email Configured | Whether IMAP/SMTP credentials are configured |
| Actions | View risk profile, delete |

### Add Employee

Click **Add Employee** to open the creation form:

1. **Basic Info**: Email address, display name, department
2. **Email Configuration** (optional): IMAP host/port, SMTP host/port, username, password, TLS toggle

When email configuration is provided, the response includes **proxy connection info** that should be used to configure the employee's email client.

### Proxy Connection Info

After creating an employee with email configuration, you'll see:

```
IMAP Server: localhost
IMAP Port:   1143
SMTP Server: localhost
SMTP Port:   1025
Username:    employee@company.com
Password:    (their real email password)
Encryption:  None (proxy handles TLS to upstream)
```

### Risk Profile

Click an employee to view their detailed risk profile:
- Rolling risk score over time
- Per-dimension average scores
- Top threat senders (ranked by average manipulation score)
- Recent analyses with scores
- Recent alerts

---

## Settings Page

System configuration management.

### Editable Settings

| Setting | Range | Description |
|---------|-------|-------------|
| Ollama Timeout | 5–120s | Max LLM inference wait time |
| Medium Alert Threshold | 0–100 | Score to trigger medium alert |
| High Alert Threshold | 0–100 | Score to trigger high alert |
| Critical Alert Threshold | 0–100 | Score to trigger critical alert |
| Pre-filter Score Boost | 0–50 | Max score addition from pre-filter rules |
| Behavioural Weight | 0–1 | Contribution of behavioural engine |
| LLM Weight | 0–1 | Contribution of LLM scoring |
| Log Level | DEBUG/INFO/WARNING/ERROR | Logging verbosity |

### Read-Only Settings

These are displayed but cannot be changed at runtime:
- Ollama Base URL
- Ollama Model
- Worker Count

Changes to thresholds and weights take effect immediately for new analyses.

---

## WebSocket Real-Time Updates

The dashboard maintains a WebSocket connection to `ws://localhost:5297/ws/alerts`. When a new alert is created by the analysis pipeline, the dashboard receives a `new_alert` event and:

1. Shows a toast notification with sender, severity, and score
2. Updates the alert count in the navigation bar
3. Prepends the alert to the alerts page (if currently viewing)
4. Refreshes the dashboard summary statistics

---

## Tech Stack

| Technology | Version | Usage |
|-----------|---------|-------|
| React | 18.3.1 | UI framework |
| Vite | 6.0.3 | Build tool and dev server |
| Tailwind CSS | 3.4.16 | Utility-first styling |
| Recharts | 2.14.1 | Charts (gauge, area, radar) |
| Lucide React | — | Icon library |
| Axios | — | HTTP client |
| React Router | — | Client-side routing |
