/**
 * MindWall — Dimension Radar Chart
 * 12 manipulation dimensions visualized on a radar chart
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React from 'react'
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

const DIMENSION_LABELS = {
  urgency: 'Urgency',
  authority_impersonation: 'Authority',
  fear_inducement: 'Fear',
  reciprocity_exploitation: 'Reciprocity',
  scarcity: 'Scarcity',
  social_proof: 'Social Proof',
  behavioral_deviation: 'Behavioral',
  cross_channel_inconsistency: 'Cross-Channel',
  emotional_escalation: 'Emotional',
  context_mismatch: 'Context',
  unusual_action_request: 'Unusual Action',
  timing_anomaly: 'Timing',
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null
  const data = payload[0].payload
  return (
    <div className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm">
      <p className="font-medium text-gray-200">{data.fullName}</p>
      <p className="text-mindwall-300">Score: {data.value.toFixed(1)}</p>
    </div>
  )
}

export default function DimensionRadar({ scores = {}, baseline = null }) {
  const data = Object.entries(DIMENSION_LABELS).map(([key, label]) => ({
    dimension: label,
    fullName: label,
    value: scores[key] ?? 0,
    baseline: baseline?.[key] ?? null,
  }))

  return (
    <div className="card">
      <h3 className="text-sm font-medium text-gray-400 mb-4">
        Manipulation Dimensions
      </h3>
      <ResponsiveContainer width="100%" height={320}>
        <RadarChart data={data} cx="50%" cy="50%">
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fill: '#6b7280', fontSize: 10 }}
            tickCount={5}
          />
          {baseline && (
            <Radar
              name="Baseline"
              dataKey="baseline"
              stroke="#4b5563"
              fill="#4b5563"
              fillOpacity={0.15}
              strokeDasharray="4 4"
            />
          )}
          <Radar
            name="Current"
            dataKey="value"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.25}
            strokeWidth={2}
          />
          <Tooltip content={<CustomTooltip />} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
