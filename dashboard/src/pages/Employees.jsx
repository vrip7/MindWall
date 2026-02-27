/**
 * MindWall — Employees Page
 * Employee listing with risk profile detail
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Users, UserPlus } from 'lucide-react'
import EmployeeTable from '../components/employees/EmployeeTable'
import EmployeeRiskProfile from '../components/employees/EmployeeRiskProfile'
import api from '../api/client'

export default function Employees() {
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedEmail, setSelectedEmail] = useState(null)
  const [showAddForm, setShowAddForm] = useState(false)

  const fetchEmployees = useCallback(async () => {
    try {
      const res = await api.getEmployees({ page: 1, page_size: 200 })
      setEmployees(res.items || [])
    } catch (err) {
      console.error('Failed to fetch employees:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchEmployees()
  }, [fetchEmployees])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Users className="w-6 h-6 text-purple-400" />
          Employees
        </h1>
        <button
          onClick={() => setShowAddForm(true)}
          className="btn-primary text-sm flex items-center gap-1"
        >
          <UserPlus className="w-4 h-4" />
          Add Employee
        </button>
      </div>

      {loading ? (
        <div className="text-center text-gray-500 py-12">
          Loading employees…
        </div>
      ) : (
        <EmployeeTable
          employees={employees}
          onSelect={(email) => setSelectedEmail(email)}
        />
      )}

      {selectedEmail && (
        <EmployeeRiskProfile
          email={selectedEmail}
          onClose={() => setSelectedEmail(null)}
        />
      )}

      {showAddForm && (
        <AddEmployeeModal
          onClose={() => setShowAddForm(false)}
          onAdded={() => {
            setShowAddForm(false)
            fetchEmployees()
          }}
        />
      )}
    </div>
  )
}

function AddEmployeeModal({ onClose, onAdded }) {
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [department, setDepartment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email.trim()) {
      setError('Email is required')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      await api.createEmployee({
        email: email.trim(),
        display_name: displayName.trim() || undefined,
        department: department.trim() || undefined,
      })
      onAdded()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add employee')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-md shadow-xl">
        <div className="p-4 border-b border-gray-700">
          <h2 className="text-lg font-semibold text-white">Add Employee</h2>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-3">
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Email <span className="text-red-400">*</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-mindwall-500"
              placeholder="employee@company.com"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Display Name
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-mindwall-500"
              placeholder="John Doe"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Department
            </label>
            <input
              type="text"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-mindwall-500"
              placeholder="Engineering"
            />
          </div>
          {error && (
            <p className="text-sm text-red-400">{error}</p>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary text-sm"
            >
              {submitting ? 'Adding…' : 'Add Employee'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
