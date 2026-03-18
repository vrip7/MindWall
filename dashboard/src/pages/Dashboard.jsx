/**
 * MindWall — Dashboard Page
 * Main overview: threat gauge, timeline, dimension radar, risk heatmap
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Shield, Mail, AlertTriangle, Users, Inbox } from 'lucide-react'
import { subDays, subHours } from 'date-fns'
import ThreatGauge from '../components/dashboard/ThreatGauge'
import DimensionRadar from '../components/dashboard/DimensionRadar'
import ThreatTimeline from '../components/dashboard/ThreatTimeline'
import RiskHeatmap from '../components/dashboard/RiskHeatmap'
import api from '../api/client'

function rangeToParams(range) {
  const now = new Date()
  let start
  switch (range) {
    case '24h': start = subHours(now, 24); break
    case '30d': start = subDays(now, 30); break
    default:    start = subDays(now, 7); break
  }
  return { start_date: start.toISOString(), end_date: now.toISOString() }
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [timeline, setTimeline] = useState([])
  const [emailAccountCount, setEmailAccountCount] = useState(0)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const [summaryRes, timelineRes, emailRes] = await Promise.all([
        api.getDashboardSummary(),
        api.getDashboardTimeline(rangeToParams('7d')),
        api.getEmailAccounts(),
      ])
      setSummary(summaryRes)
      setTimeline(timelineRes.entries || [])
      setEmailAccountCount(Array.isArray(emailRes) ? emailRes.length : 0)
    } catch (err) {
      console.error('Dashboard fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30_000)
    return () => clearInterval(interval)
  }, [fetchData])

  const handleRangeChange = async (range) => {
    try {
      const res = await api.getDashboardTimeline(rangeToParams(range))
      setTimeline(res.entries || [])
    } catch (err) {
      console.error('Timeline fetch error:', err)
    }
  }

  const activeAlertCount = summary?.unacknowledged_alerts
    ? Object.values(summary.unacknowledged_alerts).reduce((a, b) => a + b, 0)
    : 0

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading dashboard…</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <Shield className="w-6 h-6 text-mindwall-400" />
        Cognitive Firewall Dashboard
      </h1>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          icon={Mail}
          label="Emails Analyzed"
          value={summary?.total_analyses ?? 0}
          color="text-mindwall-400"
        />
        <StatCard
          icon={AlertTriangle}
          label="Active Alerts"
          value={activeAlertCount}
          color="text-red-400"
        />
        <StatCard
          icon={Users}
          label="Monitored Employees"
          value={summary?.employee_count ?? 0}
          color="text-purple-400"
        />
        <StatCard
          icon={Inbox}
          label="Email Accounts"
          value={emailAccountCount}
          color="text-cyan-400"
        />
        <StatCard
          icon={Shield}
          label="Avg Threat Score"
          value={(summary?.average_score ?? 0).toFixed(1)}
          color="text-amber-400"
        />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1">
          <ThreatGauge score={summary?.average_score ?? 0} />
        </div>
        <div className="lg:col-span-2">
          <ThreatTimeline
            data={timeline}
            onRangeChange={handleRangeChange}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DimensionRadar scores={summary?.avg_dimension_scores || {}} />
        <RiskHeatmap
          data={summary?.heatmap_data?.data || []}
          rowLabels={summary?.heatmap_data?.row_labels || []}
          colLabels={summary?.heatmap_data?.col_labels || []}
        />
      </div>
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="card">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-gray-800">
          <Icon className={`w-5 h-5 ${color}`} />
        </div>
        <div>
          <p className="text-xs text-gray-500">{label}</p>
          <p className="text-xl font-bold text-white">{value}</p>
        </div>
      </div>
    </div>
  )
}
