/**
 * MindWall — Employee Risk Profile
 * Detailed per-employee view: threat senders, rolling risk, recent alerts
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React, { useState, useEffect } from 'react'
import {
  X,
  User,
  Shield,
  AlertTriangle,
  Mail,
  TrendingUp,
} from 'lucide-react'
import { format, parseISO } from 'date-fns'
import clsx from 'clsx'
import DimensionRadar from '../dashboard/DimensionRadar'
import api from '../../api/client'

export default function EmployeeRiskProfile({ email, onClose }) {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!email) return
    setLoading(true)
    api
      .getEmployeeRiskProfile(email)
      .then(setProfile)
      .catch((err) => console.error('Failed to load risk profile:', err))
      .finally(() => setLoading(false))
  }, [email])

  if (!email) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700 sticky top-0 bg-gray-900 z-10">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-mindwall-400" />
            <h2 className="text-lg font-semibold text-white">
              Employee Risk Profile
            </h2>
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

        {!loading && profile && (
          <div className="p-4 space-y-4">
            {/* Employee info */}
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-gray-700 flex items-center justify-center">
                <User className="w-6 h-6 text-gray-400" />
              </div>
              <div>
                <h3 className="text-white font-medium">
                  {profile.display_name || email}
                </h3>
                <p className="text-sm text-gray-500">{email}</p>
                {profile.department && (
                  <p className="text-xs text-gray-600">{profile.department}</p>
                )}
              </div>
              <div className="ml-auto text-right">
                <div className="text-2xl font-bold text-white">
                  {(profile.rolling_risk_score ?? 0).toFixed(1)}
                </div>
                <span
                  className={clsx(
                    'severity-badge',
                    `severity-${getSeverity(profile.rolling_risk_score)}`
                  )}
                >
                  {getSeverity(profile.rolling_risk_score)}
                </span>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-3">
              <StatBox
                icon={Mail}
                label="Total Emails"
                value={profile.total_emails ?? 0}
              />
              <StatBox
                icon={AlertTriangle}
                label="Flagged"
                value={profile.flagged_emails ?? 0}
                color="text-amber-400"
              />
              <StatBox
                icon={TrendingUp}
                label="30-Day Risk"
                value={(profile.rolling_risk_score ?? 0).toFixed(1)}
                color={
                  (profile.rolling_risk_score ?? 0) >= 60
                    ? 'text-red-400'
                    : 'text-emerald-400'
                }
              />
            </div>

            {/* Top threat senders */}
            {profile.top_threat_senders?.length > 0 && (
              <div className="bg-gray-800 rounded-lg p-3">
                <h4 className="text-xs font-medium text-gray-400 mb-2">
                  Top Threat Senders
                </h4>
                <div className="space-y-2">
                  {profile.top_threat_senders.map((sender) => (
                    <div
                      key={sender.sender_email}
                      className="flex items-center justify-between text-sm"
                    >
                      <span className="text-gray-300">
                        {sender.sender_email}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500">
                          {sender.count} emails
                        </span>
                        <span
                          className={clsx(
                            'font-mono text-sm',
                            sender.avg_score >= 60
                              ? 'text-red-400'
                              : sender.avg_score >= 35
                              ? 'text-amber-400'
                              : 'text-emerald-400'
                          )}
                        >
                          {sender.avg_score.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Average dimension scores radar */}
            {profile.avg_dimension_scores && (
              <DimensionRadar scores={profile.avg_dimension_scores} />
            )}

            {/* Recent alerts */}
            {profile.recent_alerts?.length > 0 && (
              <div className="bg-gray-800 rounded-lg p-3">
                <h4 className="text-xs font-medium text-gray-400 mb-2">
                  Recent Alerts
                </h4>
                <div className="space-y-1.5">
                  {profile.recent_alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="flex items-center justify-between text-sm py-1 border-b border-gray-700 last:border-0"
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className={clsx(
                            'severity-badge text-xs',
                            `severity-${alert.severity}`
                          )}
                        >
                          {alert.severity}
                        </span>
                        <span className="text-gray-400 text-xs">
                          {alert.sender_email}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {alert.created_at
                          ? format(parseISO(alert.created_at), 'MMM d, HH:mm')
                          : ''}
                      </span>
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

function StatBox({ icon: Icon, label, value, color = 'text-white' }) {
  return (
    <div className="bg-gray-800 rounded-lg p-3 text-center">
      <Icon className="w-4 h-4 text-gray-500 mx-auto mb-1" />
      <div className={clsx('text-xl font-bold', color)}>{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  )
}

function getSeverity(score) {
  if (!score || score < 35) return 'low'
  if (score < 60) return 'medium'
  if (score < 80) return 'high'
  return 'critical'
}
