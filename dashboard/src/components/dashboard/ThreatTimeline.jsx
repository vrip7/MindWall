/**
 * MindWall — Threat Timeline (Line Chart)
 * Shows aggregate threat score over time
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React, { useState } from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { format, parseISO, subDays, subHours } from 'date-fns'
import clsx from 'clsx'

const RANGES = [
  { key: '24h', label: '24 Hours' },
  { key: '7d', label: '7 Days' },
  { key: '30d', label: '30 Days' },
]

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null
  return (
    <div className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm">
      <p className="text-gray-400 text-xs">{label}</p>
      <p className="font-medium text-mindwall-300">
        Score: {payload[0].value.toFixed(1)}
      </p>
      {payload[0].payload.count !== undefined && (
        <p className="text-gray-500 text-xs">
          {payload[0].payload.count} emails analyzed
        </p>
      )}
    </div>
  )
}

export default function ThreatTimeline({ data = [], onRangeChange }) {
  const [activeRange, setActiveRange] = useState('7d')

  const handleRange = (range) => {
    setActiveRange(range)
    onRangeChange?.(range)
  }

  const formatted = data.map((entry) => ({
    ...entry,
    time: formatTime(entry.bucket, activeRange),
  }))

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">Threat Timeline</h3>
        <div className="flex gap-1">
          {RANGES.map((r) => (
            <button
              key={r.key}
              onClick={() => handleRange(r.key)}
              className={clsx(
                'px-2 py-1 text-xs rounded transition-colors',
                activeRange === r.key
                  ? 'bg-mindwall-600 text-white'
                  : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
              )}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={formatted}>
          <defs>
            <linearGradient id="threatGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="time"
            tick={{ fill: '#6b7280', fontSize: 11 }}
            axisLine={{ stroke: '#374151' }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: '#6b7280', fontSize: 11 }}
            axisLine={{ stroke: '#374151' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine
            y={60}
            stroke="#ef4444"
            strokeDasharray="4 4"
            label={{
              value: 'High',
              position: 'right',
              fill: '#ef4444',
              fontSize: 10,
            }}
          />
          <ReferenceLine
            y={35}
            stroke="#f59e0b"
            strokeDasharray="4 4"
            label={{
              value: 'Medium',
              position: 'right',
              fill: '#f59e0b',
              fontSize: 10,
            }}
          />
          <Area
            type="monotone"
            dataKey="avg_score"
            stroke="#3b82f6"
            fill="url(#threatGradient)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

function formatTime(bucket, range) {
  if (!bucket) return ''
  try {
    const d = typeof bucket === 'string' ? parseISO(bucket) : new Date(bucket)
    if (range === '24h') return format(d, 'HH:mm')
    if (range === '7d') return format(d, 'EEE')
    return format(d, 'MMM d')
  } catch {
    return String(bucket)
  }
}
