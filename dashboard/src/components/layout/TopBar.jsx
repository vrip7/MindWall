/**
 * MindWall — Top Bar
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React, { useState, useEffect } from 'react'
import { Bell, Wifi, WifiOff, Shield } from 'lucide-react'
import wsManager from '../../api/websocket'

export default function TopBar() {
  const [wsConnected, setWsConnected] = useState(false)
  const [alertCount, setAlertCount] = useState(0)

  useEffect(() => {
    // Connect WebSocket
    wsManager.connect()

    const unsubConnection = wsManager.on('connection', (data) => {
      setWsConnected(data.status === 'connected')
    })

    const unsubAlert = wsManager.on('new_alert', () => {
      setAlertCount(prev => prev + 1)
    })

    return () => {
      unsubConnection()
      unsubAlert()
    }
  }, [])

  return (
    <header className="h-16 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <Shield className="h-5 w-5 text-mindwall-500" />
        <span className="text-sm text-gray-400">AI-Powered Human Manipulation Detection</span>
      </div>

      <div className="flex items-center gap-4">
        {/* WebSocket status */}
        <div className="flex items-center gap-2">
          {wsConnected ? (
            <div className="flex items-center gap-1.5 text-emerald-400">
              <Wifi className="h-4 w-4" />
              <span className="text-xs">Live</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-red-400">
              <WifiOff className="h-4 w-4" />
              <span className="text-xs">Disconnected</span>
            </div>
          )}
        </div>

        {/* Alert notification */}
        <button 
          className="relative p-2 text-gray-400 hover:text-gray-200 transition-colors"
          onClick={() => setAlertCount(0)}
        >
          <Bell className="h-5 w-5" />
          {alertCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
              {alertCount > 99 ? '99+' : alertCount}
            </span>
          )}
        </button>
      </div>
    </header>
  )
}
