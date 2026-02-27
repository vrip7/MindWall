/**
 * MindWall — Alert Detail Panel
 * Full detail view for a single alert, including dimension breakdown
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React, { useState, useEffect } from 'react'
import {
  X,
  AlertTriangle,
  Mail,
  User,
  Clock,
  CheckCircle,
  ExternalLink,
} from 'lucide-react'
import { format, parseISO } from 'date-fns'
import clsx from 'clsx'
import DimensionRadar from '../dashboard/DimensionRadar'
import api from '../../api/client'

export default function AlertDetail({ alertId, onClose, onAcknowledged }) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [acknowledging, setAcknowledging] = useState(false)

  useEffect(() => {
    if (!alertId) return
    setLoading(true)
    api
      .getAlertDetail(alertId)
      .then(setDetail)
      .catch((err) => console.error('Failed to load alert detail:', err))
      .finally(() => setLoading(false))
  }, [alertId])

  const handleAcknowledge = async () => {
    if (!detail || detail.acknowledged) return
    setAcknowledging(true)
    try {
      await api.acknowledgeAlert(detail.id)
      setDetail((prev) => ({ ...prev, acknowledged: true }))
      onAcknowledged?.(detail.id)
    } catch (err) {
      console.error('Failed to acknowledge:', err)
    } finally {
      setAcknowledging(false)
    }
  }

  if (!alertId) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700 sticky top-0 bg-gray-900 z-10">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <h2 className="text-lg font-semibold text-white">Alert Detail</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-gray-700 text-gray-400 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading && (
          <div className="p-8 text-center text-gray-500">Loading…</div>
        )}

        {!loading && detail && (
          <div className="p-4 space-y-4">
            {/* Severity & Score */}
            <div className="flex items-center gap-3">
              <span
                className={clsx(
                  'severity-badge text-sm',
                  `severity-${detail.severity}`
                )}
              >
                {detail.severity?.toUpperCase()}
              </span>
              <span className="text-2xl font-bold text-white">
                {detail.aggregate_score?.toFixed(1)}
              </span>
              <span className="text-gray-500 text-sm">/100</span>

              {!detail.acknowledged && (
                <button
                  onClick={handleAcknowledge}
                  disabled={acknowledging}
                  className="ml-auto btn-primary text-sm flex items-center gap-1"
                >
                  <CheckCircle className="w-4 h-4" />
                  {acknowledging ? 'Acknowledging…' : 'Acknowledge'}
                </button>
              )}
              {detail.acknowledged && (
                <span className="ml-auto text-sm text-emerald-500 flex items-center gap-1">
                  <CheckCircle className="w-4 h-4" />
                  Acknowledged
                </span>
              )}
            </div>

            {/* Meta */}
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="flex items-center gap-2 text-gray-400">
                <Mail className="w-4 h-4 shrink-0" />
                <div>
                  <span className="text-gray-500 text-xs block">Sender</span>
                  <span className="text-gray-200">
                    {detail.sender_email}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2 text-gray-400">
                <User className="w-4 h-4 shrink-0" />
                <div>
                  <span className="text-gray-500 text-xs block">Recipient</span>
                  <span className="text-gray-200">
                    {detail.recipient_email}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2 text-gray-400">
                <Clock className="w-4 h-4 shrink-0" />
                <div>
                  <span className="text-gray-500 text-xs block">Received</span>
                  <span className="text-gray-200">
                    {detail.received_at
                      ? format(parseISO(detail.received_at), 'PPpp')
                      : '—'}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2 text-gray-400">
                <ExternalLink className="w-4 h-4 shrink-0" />
                <div>
                  <span className="text-gray-500 text-xs block">Message UID</span>
                  <span className="text-gray-200 font-mono text-xs">
                    {detail.message_uid || '—'}
                  </span>
                </div>
              </div>
            </div>

            {/* Explanation */}
            {detail.explanation && (
              <div className="bg-gray-800 rounded-lg p-3">
                <h4 className="text-xs font-medium text-gray-400 mb-1">
                  AI Explanation
                </h4>
                <p className="text-sm text-gray-300 leading-relaxed">
                  {detail.explanation}
                </p>
              </div>
            )}

            {/* Dimension Radar */}
            {detail.dimension_scores && (
              <DimensionRadar scores={detail.dimension_scores} />
            )}

            {/* Dimension Score Table */}
            {detail.dimension_scores && (
              <div className="bg-gray-800 rounded-lg p-3">
                <h4 className="text-xs font-medium text-gray-400 mb-2">
                  Dimension Breakdown
                </h4>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                  {Object.entries(detail.dimension_scores)
                    .sort(([, a], [, b]) => b - a)
                    .map(([dim, score]) => (
                      <div
                        key={dim}
                        className="flex items-center justify-between text-xs py-0.5"
                      >
                        <span className="text-gray-400 capitalize">
                          {dim.replace(/_/g, ' ')}
                        </span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className={clsx(
                                'h-full rounded-full transition-all',
                                score >= 80
                                  ? 'bg-red-500'
                                  : score >= 60
                                  ? 'bg-red-400'
                                  : score >= 35
                                  ? 'bg-amber-400'
                                  : 'bg-emerald-400'
                              )}
                              style={{ width: `${Math.min(100, score)}%` }}
                            />
                          </div>
                          <span className="text-gray-300 w-8 text-right font-mono">
                            {score.toFixed(0)}
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
