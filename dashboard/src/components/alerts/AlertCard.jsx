/**
 * MindWall — Alert Card Component
 * Compact card for alert feed lists
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React from 'react'
import { AlertTriangle, Clock, User, Mail, CheckCircle } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import clsx from 'clsx'

const SEVERITY_ICONS = {
  low: null,
  medium: AlertTriangle,
  high: AlertTriangle,
  critical: AlertTriangle,
}

export default function AlertCard({ alert, onClick, onAcknowledge }) {
  const Icon = SEVERITY_ICONS[alert.severity] || AlertTriangle
  const created = alert.created_at
    ? format(parseISO(alert.created_at), 'MMM d, HH:mm')
    : ''

  return (
    <div
      onClick={() => onClick?.(alert)}
      className={clsx(
        'card cursor-pointer hover:border-gray-600 transition-all group',
        !alert.acknowledged && 'border-l-2',
        !alert.acknowledged && alert.severity === 'critical' && 'border-l-red-500',
        !alert.acknowledged && alert.severity === 'high' && 'border-l-red-400',
        !alert.acknowledged && alert.severity === 'medium' && 'border-l-amber-400',
        !alert.acknowledged && alert.severity === 'low' && 'border-l-emerald-400',
        alert.acknowledged && 'opacity-60'
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          {Icon && (
            <div
              className={clsx(
                'p-1.5 rounded',
                alert.severity === 'critical' && 'bg-red-500/20 text-red-400',
                alert.severity === 'high' && 'bg-red-500/15 text-red-400',
                alert.severity === 'medium' && 'bg-amber-500/15 text-amber-400',
                alert.severity === 'low' && 'bg-emerald-500/15 text-emerald-400'
              )}
            >
              <Icon className="w-4 h-4" />
            </div>
          )}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className={clsx('severity-badge', `severity-${alert.severity}`)}>
                {alert.severity}
              </span>
              <span className="text-white font-medium text-sm truncate">
                {alert.headline || `Score: ${alert.aggregate_score?.toFixed(1)}`}
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <Mail className="w-3 h-3" />
                {alert.sender_email || 'Unknown'}
              </span>
              <span className="flex items-center gap-1">
                <User className="w-3 h-3" />
                {alert.recipient_email || 'Unknown'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className="text-xs text-gray-500 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {created}
          </span>
          {!alert.acknowledged && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onAcknowledge?.(alert.id)
              }}
              className="text-xs text-gray-500 hover:text-emerald-400 flex items-center gap-1 transition-colors opacity-0 group-hover:opacity-100"
              title="Acknowledge"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              Ack
            </button>
          )}
          {alert.acknowledged && (
            <span className="text-xs text-emerald-600 flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
            </span>
          )}
        </div>
      </div>

      {alert.explanation && (
        <p className="text-xs text-gray-500 mt-2 line-clamp-2">
          {alert.explanation}
        </p>
      )}
    </div>
  )
}
