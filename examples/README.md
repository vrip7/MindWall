# MindWall — Example Phishing Emails

This folder contains sample phishing and social engineering emails you can submit to the MindWall API to test its detection capabilities.

## Quick Start

### Using the test script (recommended)

```bash
# Run all examples against a local MindWall instance
python examples/test_examples.py

# Run a specific example
python examples/test_examples.py --file examples/ceo_fraud.json

# Target a remote instance
python examples/test_examples.py --url http://your-server:5297 --key YOUR_API_KEY
```

### Using cURL

```bash
curl -s -X POST http://localhost:5297/api/analyze \
  -H "Content-Type: application/json" \
  -H "X-MindWall-Key: CD080A0539991A69FC414E46CC3E7434" \
  -d @examples/ceo_fraud.json | python -m json.tool
```

### Using PowerShell

```powershell
$body = Get-Content examples\ceo_fraud.json -Raw
Invoke-RestMethod -Uri http://localhost:5297/api/analyze `
  -Method Post -ContentType "application/json" `
  -Headers @{ "X-MindWall-Key" = "CD080A0539991A69FC414E46CC3E7434" } `
  -Body $body
```

## Examples

| File | Category | Expected Severity | Description |
|------|----------|-------------------|-------------|
| `ceo_fraud.json` | Authority Impersonation | **Critical** | CEO requesting urgent wire transfer |
| `account_suspension.json` | Fear/Threat Induction | **High** | Fake account suspension notice with credential phishing link |
| `invoice_scam.json` | Artificial Urgency | **High** | Fraudulent invoice with changed bank details |
| `prize_winner.json` | Reciprocity Exploitation | **Medium** | Fake lottery/prize notification |
| `it_support_scam.json` | Authority + Urgency | **Critical** | Fake IT department requesting credentials |
| `colleague_request.json` | Social Proof + Urgency | **High** | Impersonating a colleague asking for gift cards |
| `shipping_notification.json` | Scarcity Tactics | **Medium** | Fake package delivery requiring action |
| `tax_refund.json` | Authority + Reciprocity | **High** | Government impersonation for tax refund |
| `job_offer_scam.json` | Emotional Escalation | **Medium** | Too-good-to-be-true job offer |
| `legitimate_email.json` | None (benign) | **Low** | Genuine business email — should score low |

## Manipulation Dimensions

MindWall scores emails across 12 manipulation dimensions:

1. **Artificial Urgency** — Manufactured time pressure
2. **Authority Impersonation** — Falsely claiming official capacity
3. **Fear/Threat Induction** — Using threats to compel action
4. **Reciprocity Exploitation** — Leveraging favors or gifts
5. **Scarcity Tactics** — Creating false scarcity
6. **Social Proof Manipulation** — Fabricating consensus
7. **Sender Behavioral Deviation** — Deviation from sender's patterns
8. **Cross-Channel Coordination** — Multi-channel social engineering
9. **Emotional Escalation** — Escalating emotions to override logic
10. **Request/Context Mismatch** — Request inconsistent with relationship
11. **Unusual Action Requested** — Atypical actions for business email
12. **Timing Anomaly** — Suspicious send timing

## Severity Levels

| Score Range | Severity | Recommended Action |
|-------------|----------|-------------------|
| 0–25 | Low | Proceed |
| 26–50 | Medium | Verify |
| 51–75 | High | Verify |
| 76–100 | Critical | Block |
