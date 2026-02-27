/**
 * MindWall — Gmail Content Script
 * Observes Gmail DOM for opened emails, extracts content, submits for analysis,
 * and injects risk badges into the Gmail UI.
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

;(function () {
  'use strict'

  /** Tracking set to avoid re-analyzing the same email view */
  const analyzedMessages = new Set()

  /** Debounce timer for mutation observer */
  let debounceTimer = null
  const DEBOUNCE_MS = 800

  /**
   * Severity → badge configuration
   */
  const SEVERITY_CONFIG = {
    critical: {
      bg: '#dc2626',
      text: '#fff',
      label: '🚨 CRITICAL RISK',
    },
    high: {
      bg: '#ef4444',
      text: '#fff',
      label: '🔴 HIGH RISK',
    },
    medium: {
      bg: '#f59e0b',
      text: '#000',
      label: '⚠️ MEDIUM RISK',
    },
    low: {
      bg: '#10b981',
      text: '#fff',
      label: '✅ LOW RISK',
    },
  }

  /**
   * Generate a deterministic UID from sender + subject + snippet
   */
  function generateMessageUID(sender, subject) {
    const raw = `${sender}|${subject}|${Date.now()}`
    let hash = 0
    for (let i = 0; i < raw.length; i++) {
      const char = raw.charCodeAt(i)
      hash = (hash << 5) - hash + char
      hash |= 0
    }
    return `gmail_web_${Math.abs(hash).toString(16)}`
  }

  /**
   * Extract sender email from Gmail header DOM
   */
  function extractSenderEmail(emailContainer) {
    // Gmail renders sender in a <span email="..."> attribute
    const senderSpan = emailContainer.querySelector('span[email]')
    if (senderSpan) return senderSpan.getAttribute('email')

    // Fallback: look for the "from" text
    const fromElement = emailContainer.querySelector('.gD')
    if (fromElement) return fromElement.getAttribute('email') || fromElement.textContent.trim()

    return null
  }

  /**
   * Extract subject from Gmail DOM
   */
  function extractSubject() {
    const subjectEl = document.querySelector('h2.hP')
    return subjectEl ? subjectEl.textContent.trim() : ''
  }

  /**
   * Extract the logged-in user's email (recipient)
   */
  function extractRecipientEmail() {
    // Gmail stores the user's email in a data attribute on body or in the account switcher
    const accountBtn = document.querySelector(
      'a[href*="SignOutOptions"], a[aria-label*="Google Account"]'
    )
    if (accountBtn) {
      const label = accountBtn.getAttribute('aria-label') || ''
      const match = label.match(/[\w.+-]+@[\w.-]+\.\w+/)
      if (match) return match[0]
    }

    // Fallback: check title which sometimes includes email
    const title = document.title
    const titleMatch = title.match(/[\w.+-]+@[\w.-]+\.\w+/)
    if (titleMatch) return titleMatch[0]

    return 'unknown@gmail.com'
  }

  /**
   * Extract plain text body from Gmail message body container
   */
  function extractEmailBody(emailContainer) {
    // Gmail uses .a3s.aiL for the message body
    const bodyEl = emailContainer.querySelector('.a3s.aiL')
    if (!bodyEl) return null

    // Clone to avoid modifying the DOM
    const clone = bodyEl.cloneNode(true)

    // Remove quoted text (Gmail wraps replies in .gmail_quote)
    const quotes = clone.querySelectorAll('.gmail_quote')
    quotes.forEach((q) => q.remove())

    // Remove signature
    const sigs = clone.querySelectorAll('.gmail_signature')
    sigs.forEach((s) => s.remove())

    // Convert block elements to newlines
    const blocks = clone.querySelectorAll('div, p, br, li, tr')
    blocks.forEach((el) => {
      if (el.tagName === 'BR') {
        el.replaceWith('\n')
      } else {
        el.insertAdjacentText('afterend', '\n')
      }
    })

    const text = clone.textContent || ''
    return text
      .replace(/\r\n/g, '\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim()
  }

  /**
   * Find the email message container(s) in the current view
   */
  function findEmailContainers() {
    // Gmail wraps each message in a div with class "gs"
    // The expanded/visible message has class "h7" on the wrapper
    const containers = document.querySelectorAll('.h7')
    if (containers.length > 0) return Array.from(containers)

    // Alternative: look for message body containers directly
    const bodyContainers = document.querySelectorAll('.a3s.aiL')
    return Array.from(bodyContainers).map(
      (el) => el.closest('.gs') || el.parentElement
    )
  }

  /**
   * Inject the MindWall risk badge into the Gmail message header
   */
  function injectBadge(emailContainer, result) {
    // Remove any existing badge
    const existing = emailContainer.querySelector('.mindwall-badge')
    if (existing) existing.remove()

    const severity = result.severity || 'low'
    const config = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.low
    const score = result.aggregate_score != null ? result.aggregate_score.toFixed(1) : '?'

    const badge = document.createElement('span')
    badge.className = 'mindwall-badge'
    badge.style.cssText = `
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: ${config.bg};
      color: ${config.text};
      margin-left: 8px;
      cursor: help;
      user-select: none;
      vertical-align: middle;
      line-height: 1.4;
    `
    badge.textContent = `${config.label} (${score})`
    badge.title = `MindWall Score: ${score}/100\nSeverity: ${severity}\n${result.explanation || ''}`

    // Insert badge near the sender info
    const headerRow =
      emailContainer.querySelector('.gE.iv.gt') || // message header bar
      emailContainer.querySelector('.iw') || // sender area
      emailContainer.querySelector('.gD') // sender name

    if (headerRow) {
      headerRow.parentElement.insertBefore(badge, headerRow.nextSibling)
    } else {
      // Fallback: prepend to the container
      emailContainer.insertBefore(badge, emailContainer.firstChild)
    }
  }

  /**
   * Inject a "loading" indicator while analysis is in progress
   */
  function injectLoadingBadge(emailContainer) {
    const existing = emailContainer.querySelector('.mindwall-badge')
    if (existing) existing.remove()

    const badge = document.createElement('span')
    badge.className = 'mindwall-badge'
    badge.style.cssText = `
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 500;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #374151;
      color: #9ca3af;
      margin-left: 8px;
      vertical-align: middle;
      line-height: 1.4;
    `
    badge.textContent = '🛡️ MindWall analyzing…'

    const headerRow =
      emailContainer.querySelector('.gE.iv.gt') ||
      emailContainer.querySelector('.iw') ||
      emailContainer.querySelector('.gD')

    if (headerRow) {
      headerRow.parentElement.insertBefore(badge, headerRow.nextSibling)
    } else {
      emailContainer.insertBefore(badge, emailContainer.firstChild)
    }
  }

  /**
   * Process a single email container
   */
  async function processEmailContainer(container) {
    const body = extractEmailBody(container)
    if (!body || body.length < 20) return // Skip trivially short emails

    const sender = extractSenderEmail(container)
    if (!sender) return

    const subject = extractSubject()
    const uid = generateMessageUID(sender, subject)

    // Skip if already analyzed in this session
    if (analyzedMessages.has(uid)) return
    analyzedMessages.add(uid)

    const recipient = extractRecipientEmail()

    injectLoadingBadge(container)

    try {
      const response = await new Promise((resolve, reject) => {
        chrome.runtime.sendMessage(
          {
            type: 'ANALYZE_EMAIL',
            payload: {
              message_uid: uid,
              sender_email: sender,
              recipient_email: recipient,
              subject: subject,
              body: body,
              received_at: new Date().toISOString(),
            },
          },
          (result) => {
            if (chrome.runtime.lastError) {
              reject(new Error(chrome.runtime.lastError.message))
            } else if (result && result.success) {
              resolve(result.data)
            } else {
              reject(new Error(result?.error || 'Unknown error'))
            }
          }
        )
      })

      injectBadge(container, response)
    } catch (err) {
      console.warn('[MindWall] Analysis error:', err.message)
      // Remove loading badge on error
      const badge = container.querySelector('.mindwall-badge')
      if (badge) badge.remove()
    }
  }

  /**
   * Scan current view for email containers and process them
   */
  function scanForEmails() {
    const containers = findEmailContainers()
    containers.forEach((container) => {
      if (container && !container.dataset.mindwallProcessed) {
        container.dataset.mindwallProcessed = 'true'
        processEmailContainer(container)
      }
    })
  }

  /**
   * Debounced scan triggered by MutationObserver
   */
  function debouncedScan() {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(scanForEmails, DEBOUNCE_MS)
  }

  /**
   * Initialize MutationObserver to watch for Gmail DOM changes
   */
  function initObserver() {
    const targetNode = document.querySelector('div[role="main"]') || document.body

    const observer = new MutationObserver((mutations) => {
      let shouldScan = false
      for (const mutation of mutations) {
        if (mutation.addedNodes.length > 0) {
          shouldScan = true
          break
        }
      }
      if (shouldScan) {
        debouncedScan()
      }
    })

    observer.observe(targetNode, {
      childList: true,
      subtree: true,
    })

    // Initial scan
    scanForEmails()
  }

  /**
   * Wait for Gmail to finish loading its UI
   */
  function waitForGmail() {
    const check = setInterval(() => {
      // Gmail renders the main content area with role="main"
      const main = document.querySelector('div[role="main"]')
      if (main) {
        clearInterval(check)
        console.log('[MindWall] Gmail detected. Initializing cognitive firewall…')
        initObserver()
      }
    }, 500)

    // Timeout after 30 seconds
    setTimeout(() => clearInterval(check), 30_000)
  }

  // Start
  waitForGmail()
})()
