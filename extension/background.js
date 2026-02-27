/**
 * MindWall — Background Service Worker (Manifest V3)
 * Handles communication between content script and MindWall API
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

const API_BASE = 'http://localhost:8000'
const API_KEY_STORAGE_KEY = 'mindwall_api_key'

/**
 * Retrieve API key from extension storage
 */
async function getApiKey() {
  return new Promise((resolve) => {
    chrome.storage.local.get([API_KEY_STORAGE_KEY], (result) => {
      resolve(result[API_KEY_STORAGE_KEY] || '')
    })
  })
}

/**
 * Submit email body to MindWall API for analysis
 */
async function analyzeEmail(payload) {
  const apiKey = await getApiKey()

  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MindWall-Key': apiKey,
    },
    body: JSON.stringify({
      message_uid: payload.message_uid,
      recipient_email: payload.recipient_email,
      sender_email: payload.sender_email,
      subject: payload.subject,
      body: payload.body,
      channel: 'gmail_web',
      received_at: payload.received_at || new Date().toISOString(),
    }),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`API error ${response.status}: ${text}`)
  }

  return response.json()
}

/**
 * Listen for messages from content script
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'ANALYZE_EMAIL') {
    analyzeEmail(message.payload)
      .then((result) => {
        sendResponse({ success: true, data: result })
      })
      .catch((err) => {
        console.error('[MindWall] Analysis failed:', err.message)
        sendResponse({ success: false, error: err.message })
      })

    // Return true to indicate async sendResponse
    return true
  }

  if (message.type === 'SET_API_KEY') {
    chrome.storage.local.set(
      { [API_KEY_STORAGE_KEY]: message.key },
      () => {
        sendResponse({ success: true })
      }
    )
    return true
  }

  if (message.type === 'HEALTH_CHECK') {
    fetch(`${API_BASE}/health`)
      .then((res) => res.json())
      .then((data) => sendResponse({ success: true, data }))
      .catch((err) =>
        sendResponse({ success: false, error: err.message })
      )
    return true
  }
})

/**
 * On install, log setup instructions
 */
chrome.runtime.onInstalled.addListener(() => {
  console.log(
    '[MindWall] Extension installed. Set API key via: ' +
      'chrome.runtime.sendMessage({type: "SET_API_KEY", key: "your-key"})'
  )
})
