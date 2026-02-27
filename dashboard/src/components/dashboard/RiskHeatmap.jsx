/**
 * MindWall — Risk Heatmap
 * Grid-based heatmap showing threat levels per employee/time bucket
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React from 'react'
import clsx from 'clsx'

function getCellColor(score) {
  if (score === null || score === undefined) return 'bg-gray-800'
  if (score >= 80) return 'bg-red-600'
  if (score >= 60) return 'bg-red-500/70'
  if (score >= 35) return 'bg-amber-500/60'
  if (score > 0) return 'bg-emerald-500/40'
  return 'bg-gray-800'
}

function getCellTooltip(row, col, score) {
  if (score === null || score === undefined) return `${row} — ${col}: No data`
  return `${row} — ${col}: ${score.toFixed(1)}`
}

export default function RiskHeatmap({ data = [], rowLabels = [], colLabels = [] }) {
  if (!data.length || !rowLabels.length || !colLabels.length) {
    return (
      <div className="card">
        <h3 className="text-sm font-medium text-gray-400 mb-4">Risk Heatmap</h3>
        <p className="text-gray-500 text-sm text-center py-8">
          Insufficient data for heatmap visualization
        </p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 className="text-sm font-medium text-gray-400 mb-4">Risk Heatmap</h3>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="p-1 text-xs text-gray-500 text-left w-28" />
              {colLabels.map((col) => (
                <th
                  key={col}
                  className="p-1 text-xs text-gray-500 font-normal text-center"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rowLabels.map((row, ri) => (
              <tr key={row}>
                <td className="p-1 text-xs text-gray-400 truncate max-w-[7rem]">
                  {row}
                </td>
                {colLabels.map((col, ci) => {
                  const score = data[ri]?.[ci] ?? null
                  return (
                    <td key={col} className="p-0.5">
                      <div
                        title={getCellTooltip(row, col, score)}
                        className={clsx(
                          'w-full aspect-square rounded-sm min-w-[1.5rem] min-h-[1.5rem] transition-colors',
                          getCellColor(score)
                        )}
                      />
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-3 mt-4 text-xs text-gray-500">
        <span>Low</span>
        <div className="flex gap-0.5">
          <div className="w-4 h-3 rounded-sm bg-emerald-500/40" />
          <div className="w-4 h-3 rounded-sm bg-amber-500/60" />
          <div className="w-4 h-3 rounded-sm bg-red-500/70" />
          <div className="w-4 h-3 rounded-sm bg-red-600" />
        </div>
        <span>Critical</span>
      </div>
    </div>
  )
}
