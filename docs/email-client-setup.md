# Email Client Setup

> Step-by-step instructions for configuring email clients to route through the MindWall proxy.

---

## How It Works

MindWall's IMAP/SMTP proxy sits between your email client and the upstream mail server. The proxy:

1. **Receives** your email client's connection on `localhost:1143` (IMAP) and `localhost:1025` (SMTP)
2. **Authenticates** using your real email credentials
3. **Resolves** the upstream server automatically from MindWall's database
4. **Opens** a TLS connection to the real mail server (e.g. `imap.gmail.com:993`)
5. **Forwards** all commands transparently
6. **Intercepts** incoming emails for real-time manipulation analysis
7. **Injects** risk badges into subject lines for high-risk emails

**You keep using your real email address and password.** The proxy handles the upstream TLS connection.

---

## Prerequisites

Before configuring your email client:

1. MindWall is running (`docker compose up -d`)
2. You've added the employee in the dashboard with email configuration:
   - IMAP host/port (e.g. `imap.gmail.com` / `993`)
   - SMTP host/port (e.g. `smtp.gmail.com` / `587`)
   - Username and password (app-specific password for Gmail)
3. Note the proxy connection info shown after adding the employee

---

## Connection Settings

Use these settings in **all** email clients:

| Setting | IMAP (Incoming) | SMTP (Outgoing) |
|---------|-----------------|------------------|
| **Server** | `localhost` | `localhost` |
| **Port** | `1143` | `1025` |
| **Encryption** | **None** | **None** |
| **Authentication** | Normal password | Normal password |
| **Username** | Your real email address | Your real email address |
| **Password** | Your real email password | Your real email password |

> **Why "None" for encryption?** The proxy runs locally on your machine. The connection from your email client to the proxy is over localhost (never leaves your computer). The proxy itself opens a secure TLS connection to the upstream mail server.

---

## Gmail — App Password Setup

Gmail requires an **App Password** for third-party clients:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Select **Mail** and your device → Generate
5. Copy the 16-character password (e.g. `abcd efgh ijkl mnop`)
6. Use this as the password in both MindWall and your email client

---

## Mozilla Thunderbird

### Add Account

1. Open Thunderbird → **Account Settings** → **Account Actions** → **Add Mail Account**
2. Enter your name, email address, and app password
3. Click **Configure manually**

### Manual Configuration

| Field | Incoming (IMAP) | Outgoing (SMTP) |
|-------|-----------------|------------------|
| Protocol | IMAP | SMTP |
| Hostname | `localhost` | `localhost` |
| Port | `1143` | `1025` |
| Connection Security | **None** | **None** |
| Authentication Method | **Normal password** | **Normal password** |
| Username | your email address | your email address |

4. Click **Re-test** — should show "The following settings were found"
5. Click **Done**

### Existing Account

1. **Account Settings** → select the account
2. **Server Settings**:
   - Server Name: `localhost`
   - Port: `1143`
   - Connection Security: None
   - Authentication: Normal password
3. **Outgoing Server (SMTP)**:
   - Server: `localhost`
   - Port: `1025`
   - Connection Security: None
   - Authentication: Normal password

---

## Microsoft Outlook (Desktop)

### New Account

1. **File** → **Add Account**
2. Click **Advanced options** → Check **Let me set up my account manually**
3. Choose **IMAP**
4. Fill in:

| Field | Value |
|-------|-------|
| Incoming mail server | `localhost` |
| Incoming port | `1143` |
| Encryption method | **None** |
| Outgoing mail server | `localhost` |
| Outgoing port | `1025` |
| Encryption method | **None** |

5. Enter your password → **Connect**

### Change Existing Account

1. **File** → **Account Settings** → **Account Settings**
2. Select the account → **Change**
3. Click **More Settings** → **Advanced** tab
4. Update server and port settings as above

---

## Apple Mail (macOS / iOS)

### macOS

1. **Mail** → **Settings** → **Accounts** → **+**
2. Select **Other Mail Account** → **Continue**
3. Enter name, email, password → **Sign In**
4. It will fail auto-discovery. Click **Configure Manually**
5. Account Type: **IMAP**
6. Incoming:
   - Mail Server: `localhost`
   - Port: `1143`
   - Uncheck **Use TLS/SSL**
7. Outgoing:
   - SMTP Server: `localhost`
   - Port: `1025`
   - Uncheck **Use TLS/SSL**
8. **Sign In**

### iOS

1. **Settings** → **Mail** → **Accounts** → **Add Account** → **Other**
2. **Add Mail Account** → enter credentials
3. IMAP settings:
   - Host Name: your computer's local IP (e.g. `192.168.1.100`)
   - Port: `1143`
   - SSL: **OFF**
4. SMTP settings:
   - Host Name: same local IP
   - Port: `1025`
   - SSL: **OFF**

> **Note for iOS:** Since MindWall runs on your computer, not a remote server, you'll need to use your computer's local network IP instead of `localhost`.

---

## Verification

After configuring your email client:

1. **Send a test email** from another account to the monitored address
2. **Check the email client** — the email should arrive normally
3. **Check the MindWall dashboard** at `http://localhost:4297`:
   - The **Alerts** page should show any flagged emails
   - The **Employees** page should show updated email counts
4. **Check proxy logs** for successful authentication:
   ```powershell
   docker compose logs proxy --tail 50
   ```
   You should see:
   ```
   imap.login_attempt  username=youremail@gmail.com
   imap.authenticated  username=youremail@gmail.com upstream=imap.gmail.com:993
   ```

---

## Risk Badges in Subject Lines

When MindWall detects a high-risk email (score ≥ 35), it modifies the subject line with a badge:

| Severity | Badge | Score Range |
|----------|-------|-------------|
| Medium | `[⚠ MW:MEDIUM]` | 35–59 |
| High | `[🔴 MW:HIGH]` | 60–79 |
| Critical | `[🚨 MW:CRITICAL]` | 80–100 |

Low-risk emails (score < 35) are delivered with no modification.

Example: `Subject: [🚨 MW:CRITICAL] Re: Wire Transfer Approval`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" | Ensure MindWall proxy container is running: `docker compose ps proxy` |
| "Authentication failed" | Verify the email account credentials in the MindWall dashboard |
| "Server not found" | Use `localhost` (not `127.0.0.1`) as the server name |
| TLS/SSL error | Ensure encryption is set to **None**, not STARTTLS or SSL/TLS |
| Emails not appearing | Check `docker compose logs proxy` for error messages |
| Gmail "less secure apps" | Use App Passwords instead — see Gmail section above |
| Outlook "encrypted connection" warning | Click through the warning — localhost traffic is safe |
