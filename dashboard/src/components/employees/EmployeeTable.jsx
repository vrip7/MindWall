/**
 * MindWall — Employee Table Component
 * Sortable, searchable employee list with risk indicators
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React, { useState, useMemo } from 'react'
import { Search, ArrowUpDown, User, TrendingUp, TrendingDown } from 'lucide-react'
import clsx from 'clsx'

export default function EmployeeTable({ employees = [], onSelect }) {
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('risk_score')
  const [sortDir, setSortDir] = useState('desc')

  const filtered = useMemo(() => {
    let list = employees
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(
        (e) =>
          e.email?.toLowerCase().includes(q) ||
          e.display_name?.toLowerCase().includes(q) ||
          e.department?.toLowerCase().includes(q)
      )
    }
    list = [...list].sort((a, b) => {
      const av = a[sortKey] ?? 0
      const bv = b[sortKey] ?? 0
      return sortDir === 'asc' ? av - bv : bv - av
    })
    return list
  }, [employees, search, sortKey, sortDir])

  const toggleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const SortHeader = ({ colKey, label }) => (
    <th
      onClick={() => toggleSort(colKey)}
      className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300 transition-colors select-none"
    >
      <span className="flex items-center gap-1">
        {label}
        <ArrowUpDown className="w-3 h-3" />
      </span>
    </th>
  )

  return (
    <div className="space-y-3">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search employees…"
          className="w-full pl-9 pr-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-mindwall-500"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-700">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Employee
              </th>
              <SortHeader colKey="risk_score" label="Risk Score" />
              <SortHeader colKey="total_emails" label="Emails" />
              <SortHeader colKey="flagged_emails" label="Flagged" />
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Trend
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {filtered.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="px-3 py-8 text-center text-sm text-gray-500"
                >
                  No employees found
                </td>
              </tr>
            )}
            {filtered.map((emp) => (
              <tr
                key={emp.email}
                onClick={() => onSelect?.(emp.email)}
                className="hover:bg-gray-800/60 cursor-pointer transition-colors"
              >
                <td className="px-3 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
                      <User className="w-4 h-4 text-gray-400" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-200">
                        {emp.display_name || emp.email}
                      </p>
                      {emp.display_name && (
                        <p className="text-xs text-gray-500">{emp.email}</p>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-3 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className={clsx(
                          'h-full rounded-full',
                          getRiskColor(emp.risk_score)
                        )}
                        style={{
                          width: `${Math.min(100, emp.risk_score || 0)}%`,
                        }}
                      />
                    </div>
                    <span
                      className={clsx(
                        'text-sm font-mono',
                        getRiskTextColor(emp.risk_score)
                      )}
                    >
                      {(emp.risk_score || 0).toFixed(1)}
                    </span>
                  </div>
                </td>
                <td className="px-3 py-3 text-sm text-gray-400">
                  {emp.total_emails ?? 0}
                </td>
                <td className="px-3 py-3 text-sm text-gray-400">
                  {emp.flagged_emails ?? 0}
                </td>
                <td className="px-3 py-3">
                  {emp.risk_trend === 'up' && (
                    <TrendingUp className="w-4 h-4 text-red-400" />
                  )}
                  {emp.risk_trend === 'down' && (
                    <TrendingDown className="w-4 h-4 text-emerald-400" />
                  )}
                  {(!emp.risk_trend || emp.risk_trend === 'stable') && (
                    <span className="text-xs text-gray-600">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function getRiskColor(score) {
  if (!score || score < 35) return 'bg-emerald-400'
  if (score < 60) return 'bg-amber-400'
  if (score < 80) return 'bg-red-400'
  return 'bg-red-500'
}

function getRiskTextColor(score) {
  if (!score || score < 35) return 'text-emerald-400'
  if (score < 60) return 'text-amber-400'
  if (score < 80) return 'text-red-400'
  return 'text-red-300'
}
