/**
 * MindWall — Employees Page
 * Employee listing with risk profile detail and email account configuration
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Users, UserPlus, Eye, EyeOff, Copy, Check, Mail, Server } from 'lucide-react'
import EmployeeTable from '../components/employees/EmployeeTable'
import EmployeeRiskProfile from '../components/employees/EmployeeRiskProfile'
import api from '../api/client'

export default function Employees() {
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedEmail, setSelectedEmail] = useState(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [deleting, setDeleting] = useState(null)
  const [proxyInfo, setProxyInfo] = useState(null)

  const fetchEmployees = useCallback(async () => {
    try {
      const res = await api.getEmployees({ limit: 200, offset: 0 })
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

  const handleDelete = useCallback(async (id, name) => {
    if (!window.confirm(`Remove employee "${name}"? This will also remove their email account configuration. This cannot be undone.`)) return
    setDeleting(id)
    try {
      await api.deleteEmployee(id)
      setEmployees((prev) => prev.filter((e) => e.id !== id))
    } catch (err) {
      console.error('Failed to delete employee:', err)
      alert('Failed to remove employee.')
    } finally {
      setDeleting(null)
    }
  }, [])

  const handleViewProxy = useCallback(async (email) => {
    try {
      const info = await api.getEmployeeProxyInfo(email)
      setProxyInfo({ ...info, email })
    } catch (err) {
      if (err.response?.status === 404) {
        alert('No email account configured for this employee.')
      } else {
        console.error('Failed to fetch proxy info:', err)
      }
    }
  }, [])

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
          onDelete={handleDelete}
          onViewProxy={handleViewProxy}
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
          onAdded={(result) => {
            setShowAddForm(false)
            fetchEmployees()
            if (result?.proxy_connection) {
              setProxyInfo({
                ...result.proxy_connection,
                email: result.employee.email,
                _password: result._password,
              })
            }
          }}
        />
      )}

      {proxyInfo && (
        <ProxyInfoDialog
          info={proxyInfo}
          onClose={() => setProxyInfo(null)}
        />
      )}
    </div>
  )
}


function AddEmployeeModal({ onClose, onAdded }) {
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [department, setDepartment] = useState('')

  // Email account config
  const [imapHost, setImapHost] = useState('')
  const [imapPort, setImapPort] = useState(993)
  const [smtpHost, setSmtpHost] = useState('')
  const [smtpPort, setSmtpPort] = useState(587)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [useTls, setUseTls] = useState(true)
  const [showPassword, setShowPassword] = useState(false)

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const hasEmailConfig = imapHost.trim() && smtpHost.trim() && username.trim() && password.trim()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email.trim()) {
      setError('Email is required')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      const payload = {
        email: email.trim(),
        display_name: displayName.trim() || undefined,
        department: department.trim() || undefined,
      }

      // Include email account config if provided
      if (hasEmailConfig) {
        payload.imap_host = imapHost.trim()
        payload.imap_port = imapPort
        payload.smtp_host = smtpHost.trim()
        payload.smtp_port = smtpPort
        payload.username = username.trim()
        payload.password = password
        payload.use_tls = useTls
      }

      const result = await api.createEmployee(payload)
      onAdded({ ...result, _password: password })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add employee')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-lg shadow-xl max-h-[90vh] overflow-y-auto">
        <div className="p-4 border-b border-gray-700">
          <h2 className="text-lg font-semibold text-white">Add Employee</h2>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Employee Details */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5" />
              Employee Details
            </h3>
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
            <div className="grid grid-cols-2 gap-3">
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
            </div>
          </div>

          {/* Email Account Configuration */}
          <div className="space-y-3 border-t border-gray-700/50 pt-4">
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5" />
              Email Account Configuration
            </h3>
            <p className="text-xs text-gray-500">
              Connect the employee's email so the MindWall proxy can intercept
              and analyse messages. After saving you'll receive the proxy
              settings to configure in the email client.
            </p>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">IMAP Host</label>
                <input
                  type="text"
                  value={imapHost}
                  onChange={(e) => setImapHost(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-mindwall-500"
                  placeholder="imap.gmail.com"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">IMAP Port</label>
                <input
                  type="number"
                  min="1"
                  max="65535"
                  value={imapPort}
                  onChange={(e) => setImapPort(parseInt(e.target.value) || 993)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-mindwall-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">SMTP Host</label>
                <input
                  type="text"
                  value={smtpHost}
                  onChange={(e) => setSmtpHost(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-mindwall-500"
                  placeholder="smtp.gmail.com"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">SMTP Port</label>
                <input
                  type="number"
                  min="1"
                  max="65535"
                  value={smtpPort}
                  onChange={(e) => setSmtpPort(parseInt(e.target.value) || 587)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-mindwall-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-mindwall-500"
                  placeholder="user@example.com"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Password / App Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 py-2 pr-9 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-mindwall-500"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>

            <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
              <input
                type="checkbox"
                checked={useTls}
                onChange={(e) => setUseTls(e.target.checked)}
                className="accent-mindwall-500"
              />
              Use TLS
            </label>
          </div>

          {error && (
            <p className="text-sm text-red-400">{error}</p>
          )}

          <div className="flex justify-end gap-2 pt-2 border-t border-gray-700/50">
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


function ProxyInfoDialog({ info, onClose }) {
  const [copied, setCopied] = useState(null)

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 2000)
  }

  const CopyBtn = ({ value, label }) => (
    <button
      onClick={() => copyToClipboard(value, label)}
      className="ml-2 text-gray-500 hover:text-mindwall-400 transition-colors"
      title={`Copy ${label}`}
    >
      {copied === label ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
    </button>
  )

  const imapAddr = `${info.imap_proxy_host}:${info.imap_proxy_port}`
  const smtpAddr = `${info.smtp_proxy_host}:${info.smtp_proxy_port}`

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-md shadow-xl">
        <div className="p-4 border-b border-gray-700">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Server className="w-5 h-5 text-mindwall-400" />
            Proxy Configuration
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            Configure these settings in the email client for <span className="text-gray-300">{info.email}</span>
          </p>
        </div>

        <div className="p-4 space-y-4">
          {/* IMAP Proxy */}
          <div className="border border-gray-700 rounded-lg p-3 space-y-2">
            <h3 className="text-sm font-medium text-gray-300 flex items-center gap-1.5">
              <Mail className="w-4 h-4 text-blue-400" />
              IMAP (Incoming Mail)
            </h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-500 text-xs block">Server</span>
                <span className="text-gray-200 font-mono flex items-center">
                  {info.imap_proxy_host}
                  <CopyBtn value={info.imap_proxy_host} label="imap-host" />
                </span>
              </div>
              <div>
                <span className="text-gray-500 text-xs block">Port</span>
                <span className="text-gray-200 font-mono flex items-center">
                  {info.imap_proxy_port}
                  <CopyBtn value={String(info.imap_proxy_port)} label="imap-port" />
                </span>
              </div>
            </div>
            {info.original_imap && (
              <div className="text-xs text-gray-600">
                Upstream: {info.original_imap}
              </div>
            )}
          </div>

          {/* SMTP Proxy */}
          <div className="border border-gray-700 rounded-lg p-3 space-y-2">
            <h3 className="text-sm font-medium text-gray-300 flex items-center gap-1.5">
              <Mail className="w-4 h-4 text-emerald-400" />
              SMTP (Outgoing Mail)
            </h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-500 text-xs block">Server</span>
                <span className="text-gray-200 font-mono flex items-center">
                  {info.smtp_proxy_host}
                  <CopyBtn value={info.smtp_proxy_host} label="smtp-host" />
                </span>
              </div>
              <div>
                <span className="text-gray-500 text-xs block">Port</span>
                <span className="text-gray-200 font-mono flex items-center">
                  {info.smtp_proxy_port}
                  <CopyBtn value={String(info.smtp_proxy_port)} label="smtp-port" />
                </span>
              </div>
            </div>
            {info.original_smtp && (
              <div className="text-xs text-gray-600">
                Upstream: {info.original_smtp}
              </div>
            )}
          </div>

          {/* Credentials */}
          <div className="border border-gray-700 rounded-lg p-3 space-y-2">
            <h3 className="text-sm font-medium text-gray-300">Credentials</h3>
            <div className="text-sm space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-gray-500 text-xs">Username</span>
                <span className="text-gray-200 font-mono text-xs flex items-center">
                  {info.username}
                  <CopyBtn value={info.username} label="username" />
                </span>
              </div>
              {info._password && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-500 text-xs">Password</span>
                  <span className="text-gray-200 font-mono text-xs flex items-center">
                    {'•'.repeat(8)}
                    <CopyBtn value={info._password} label="password" />
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="btn-primary text-sm"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
