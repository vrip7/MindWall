# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ Active  |

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please report security issues responsibly:

1. **Email:** Send a detailed report to **security@vrip7.com**
2. **Subject line:** `[MindWall Security] Brief description`
3. **Include:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fix (if any)

### Response Timeline

| Stage | Timeline |
|-------|----------|
| Acknowledgment | Within 48 hours |
| Initial assessment | Within 5 business days |
| Fix development | Within 30 days (critical), 90 days (non-critical) |
| Public disclosure | After fix is released and deployed |

## Security Architecture

### Deployment Model

MindWall is designed for **internal network deployment only**. All components run within a single Docker Compose stack on an organization's private infrastructure.

### Key Security Properties

| Property | Implementation |
|----------|---------------|
| **Data isolation** | Zero external API calls — all LLM inference runs locally via Ollama |
| **Network boundary** | All services communicate over Docker internal network (`mindwall-internal`) |
| **Authentication** | API key authentication via `X-API-Key` header |
| **Secret management** | Secrets generated at setup, stored in `.env` (not committed to git) |
| **Database** | SQLite — file-based, no network-exposed database server |
| **TLS** | Proxy handles TLS termination for upstream mail server connections |

### Hardening Recommendations

1. **Network isolation:** Deploy on a dedicated VLAN or subnet
2. **Firewall rules:** Only allow internal clients to reach ports 1143, 1025, 3000, 8000
3. **Never expose to internet:** MindWall ports should not be publicly accessible
4. **Rotate API keys:** Regenerate `API_SECRET_KEY` periodically
5. **Update regularly:** Keep Docker images, NVIDIA drivers, and Ollama updated
6. **Monitor logs:** Enable structured logging and forward to your SIEM
7. **Restrict Docker:** Use non-root containers where possible (already configured)
8. **Backup:** Regularly back up `data/db/mindwall.db`

### What MindWall Does NOT Do

- Does not send any data to external servers
- Does not phone home or collect telemetry
- Does not store email credentials (passed through to upstream)
- Does not modify email content (read-only analysis for IMAP)

## Scope

The following are **in scope** for security reports:

- Authentication bypass
- SQL injection in the API layer
- WebSocket hijacking
- IMAP/SMTP proxy vulnerabilities
- Container escape risks
- Sensitive data exposure in logs
- Dependency vulnerabilities

The following are **out of scope:**

- Attacks requiring physical access to the server
- Social engineering of administrators
- Denial of service on localhost services
- Issues in upstream dependencies with existing CVEs (report to upstream)

---

**Maintained by [Pradyumn Tandon](https://pradyumntandon.com) at [VRIP7](https://vrip7.com)**
