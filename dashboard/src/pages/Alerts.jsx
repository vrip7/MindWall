/**
 * MindWall — Alerts Page
 * Alert feed with detail panel
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React, { useState, useEffect } from 'react'
import { AlertTriangle } from 'lucide-react'
import AlertFeed from '../components/alerts/AlertFeed'
import AlertDetail from '../components/alerts/AlertDetail'
import { wsManager } from '../api/websocket'

export default function Alerts() {
  const [selectedAlertId, setSelectedAlertId] = useState(null)
  const [wsAlerts, setWsAlerts] = useState([])

  useEffect(() => {
    const unsubscribe = wsManager.on('new_alert', (data) => {
      setWsAlerts((prev) => [data, ...prev])
    })

    wsManager.connect()

    return () => {
      unsubscribe()
    }
  }, [])

  return (
    <div className="h-full flex flex-col">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2 mb-4">
        <AlertTriangle className="w-6 h-6 text-red-400" />
        Alerts
      </h1>

      <div className="flex-1 min-h-0">
        <AlertFeed
          onSelectAlert={(alert) => setSelectedAlertId(alert.id)}
          wsAlerts={wsAlerts}
        />
      </div>

      {selectedAlertId && (
        <AlertDetail
          alertId={selectedAlertId}
          onClose={() => setSelectedAlertId(null)}
          onAcknowledged={() => {}}
        />
      )}
    </div>
  )
}
