/**
 * MindWall — Threat Gauge Component
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React from 'react'
import clsx from 'clsx'

export default function ThreatGauge({ score, label = 'Org-Wide Threat Level' }) {
  const severity = getSeverity(score)
  const percentage = Math.min(100, Math.max(0, score))
  const rotation = (percentage / 100) * 180 - 90

  return (
    <div className="card flex flex-col items-center">
      <h3 className="text-sm font-medium text-gray-400 mb-4">{label}</h3>
      
      {/* Gauge */}
      <div className="relative w-48 h-24 overflow-hidden">
        <div className="absolute inset-0">
          {/* Background arc */}
          <svg viewBox="0 0 200 100" className="w-full h-full">
            <path
              d="M 10 100 A 90 90 0 0 1 190 100"
              fill="none"
              stroke="#374151"
              strokeWidth="12"
              strokeLinecap="round"
            />
            {/* Colored arc */}
            <path
              d="M 10 100 A 90 90 0 0 1 190 100"
              fill="none"
              stroke={getColor(severity)}
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={`${percentage * 2.83} 283`}
            />
          </svg>
        </div>
        
        {/* Needle */}
        <div
          className="absolute bottom-0 left-1/2 origin-bottom"
          style={{
            transform: `translateX(-50%) rotate(${rotation}deg)`,
            width: '2px',
            height: '70px',
            background: 'white',
            transition: 'transform 1s ease-out',
          }}
        />
        
        {/* Center dot */}
        <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-1/2 w-4 h-4 bg-gray-800 border-2 border-gray-600 rounded-full" />
      </div>

      {/* Score display */}
      <div className="mt-4 text-center">
        <span className={clsx('text-3xl font-bold', getTextColor(severity))}>
          {score.toFixed(1)}
        </span>
        <span className="text-gray-500 text-sm ml-1">/100</span>
      </div>
      
      <span className={clsx('severity-badge mt-2', `severity-${severity}`)}>
        {severity.toUpperCase()}
      </span>
    </div>
  )
}

function getSeverity(score) {
  if (score >= 80) return 'critical'
  if (score >= 60) return 'high'
  if (score >= 35) return 'medium'
  return 'low'
}

function getColor(severity) {
  const colors = {
    low: '#10b981',
    medium: '#f59e0b',
    high: '#ef4444',
    critical: '#dc2626',
  }
  return colors[severity] || colors.low
}

function getTextColor(severity) {
  const colors = {
    low: 'text-emerald-400',
    medium: 'text-amber-400',
    high: 'text-red-400',
    critical: 'text-red-300',
  }
  return colors[severity] || colors.low
}
