/**
 * MindWall — WebSocket Client Manager
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/alerts'

class WebSocketManager {
  constructor() {
    this.ws = null
    this.listeners = new Map()
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 10
    this.reconnectDelay = 2000
    this.pingInterval = null
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return
    }

    try {
      this.ws = new WebSocket(WS_URL)

      this.ws.onopen = () => {
        console.log('[MindWall WS] Connected')
        this.reconnectAttempts = 0
        this._emit('connection', { status: 'connected' })
        
        // Start ping interval
        this.pingInterval = setInterval(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send('ping')
          }
        }, 30000)
      }

      this.ws.onmessage = (event) => {
        try {
          if (event.data === 'pong') return
          const data = JSON.parse(event.data)
          this._emit(data.event || 'message', data)
          this._emit('any', data)
        } catch (e) {
          console.error('[MindWall WS] Parse error:', e)
        }
      }

      this.ws.onclose = (event) => {
        console.log('[MindWall WS] Disconnected:', event.code)
        this._cleanup()
        this._emit('connection', { status: 'disconnected' })
        this._scheduleReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('[MindWall WS] Error:', error)
        this._emit('error', { error })
      }
    } catch (e) {
      console.error('[MindWall WS] Connection failed:', e)
      this._scheduleReconnect()
    }
  }

  disconnect() {
    this._cleanup()
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event).add(callback)
    return () => this.listeners.get(event)?.delete(callback)
  }

  _emit(event, data) {
    const callbacks = this.listeners.get(event)
    if (callbacks) {
      callbacks.forEach(cb => {
        try { cb(data) } catch (e) { console.error('[MindWall WS] Listener error:', e) }
      })
    }
  }

  _cleanup() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  _scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[MindWall WS] Max reconnect attempts reached')
      return
    }
    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1)
    console.log(`[MindWall WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
    setTimeout(() => this.connect(), delay)
  }
}

export const wsManager = new WebSocketManager()
export default wsManager
