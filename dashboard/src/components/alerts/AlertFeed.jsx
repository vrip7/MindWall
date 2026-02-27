/**
 * MindWall — Alert Feed Component
 * Paginated, filterable alert list
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React, { useState, useEffect, useCallback } from 'react'
import { ChevronLeft, ChevronRight, Filter } from 'lucide-react'
import clsx from 'clsx'
import AlertCard from './AlertCard'
import api from '../../api/client'

const SEVERITY_OPTIONS = ['all', 'critical', 'high', 'medium', 'low']

export default function AlertFeed({ onSelectAlert, wsAlerts = [] }) {
  const [alerts, setAlerts] = useState([])
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [severity, setSeverity] = useState('all')
  const [showAcknowledged, setShowAcknowledged] = useState(false)
  const [loading, setLoading] = useState(false)

  const pageSize = 20

  const fetchAlerts = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, page_size: pageSize }
      if (severity !== 'all') params.severity = severity
      if (!showAcknowledged) params.acknowledged = false
      const res = await api.getAlerts(params)
      setAlerts(res.items || [])
      setTotalPages(Math.ceil((res.total || 0) / pageSize) || 1)
    } catch (err) {
      console.error('Failed to fetch alerts:', err)
    } finally {
      setLoading(false)
    }
  }, [page, severity, showAcknowledged])

  useEffect(() => {
    fetchAlerts()
  }, [fetchAlerts])

  // Prepend real-time alerts from WebSocket
  useEffect(() => {
    if (wsAlerts.length > 0) {
      setAlerts((prev) => {
        const existing = new Set(prev.map((a) => a.id))
        const fresh = wsAlerts.filter((a) => !existing.has(a.id))
        return [...fresh, ...prev]
      })
    }
  }, [wsAlerts])

  const handleAcknowledge = async (alertId) => {
    try {
      await api.acknowledgeAlert(alertId)
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, acknowledged: true } : a))
      )
    } catch (err) {
      console.error('Failed to acknowledge alert:', err)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Filters */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <div className="flex items-center gap-1 text-gray-400 text-sm">
          <Filter className="w-4 h-4" />
          <span>Severity:</span>
        </div>
        <div className="flex gap-1">
          {SEVERITY_OPTIONS.map((opt) => (
            <button
              key={opt}
              onClick={() => {
                setSeverity(opt)
                setPage(1)
              }}
              className={clsx(
                'px-2 py-1 text-xs rounded capitalize transition-colors',
                severity === opt
                  ? 'bg-mindwall-600 text-white'
                  : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
              )}
            >
              {opt}
            </button>
          ))}
        </div>

        <label className="flex items-center gap-1.5 text-xs text-gray-500 ml-auto cursor-pointer">
          <input
            type="checkbox"
            checked={showAcknowledged}
            onChange={(e) => {
              setShowAcknowledged(e.target.checked)
              setPage(1)
            }}
            className="rounded border-gray-600 bg-gray-700 text-mindwall-500 focus:ring-mindwall-500"
          />
          Show acknowledged
        </label>
      </div>

      {/* Alert list */}
      <div className="flex-1 overflow-y-auto space-y-2 min-h-0">
        {loading && alerts.length === 0 && (
          <div className="text-center text-gray-500 py-12">Loading alerts…</div>
        )}
        {!loading && alerts.length === 0 && (
          <div className="text-center text-gray-500 py-12">
            No alerts matching current filters
          </div>
        )}
        {alerts.map((alert) => (
          <AlertCard
            key={alert.id}
            alert={alert}
            onClick={onSelectAlert}
            onAcknowledge={handleAcknowledge}
          />
        ))}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-700">
        <span className="text-xs text-gray-500">
          Page {page} of {totalPages}
        </span>
        <div className="flex gap-1">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="p-1 rounded bg-gray-700 text-gray-400 hover:bg-gray-600 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="p-1 rounded bg-gray-700 text-gray-400 hover:bg-gray-600 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
