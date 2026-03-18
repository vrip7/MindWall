/**
 * MindWall — Settings Page
 * Runtime-configurable thresholds and system settings
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Settings as SettingsIcon, Save, RotateCcw, Mail, Plus, Trash2, Eye, EyeOff } from 'lucide-react'
import api from '../api/client'

const THRESHOLD_FIELDS = [
  {
    key: 'alert_critical_threshold',
    label: 'Critical Alert Threshold',
    description: 'Score at or above which an alert is classified as critical',
    min: 0,
    max: 100,
  },
  {
    key: 'alert_high_threshold',
    label: 'High Alert Threshold',
    description: 'Score at or above which an alert is classified as high severity',
    min: 0,
    max: 100,
  },
  {
    key: 'alert_medium_threshold',
    label: 'Medium Alert Threshold',
    description: 'Score at or above which an alert is classified as medium severity',
    min: 0,
    max: 100,
  },
  {
    key: 'prefilter_score_boost',
    label: 'Pre-filter Score Boost',
    description: 'Maximum additional score boost from the regex pre-filter stage',
    min: 0,
    max: 50,
  },
  {
    key: 'behavioral_weight',
    label: 'Behavioral Deviation Weight',
    description: 'Weight given to behavioral deviation in the final score merge (0.0 - 1.0)',
    min: 0,
    max: 1,
    step: 0.05,
  },
  {
    key: 'llm_weight',
    label: 'LLM Analysis Weight',
    description: 'Weight given to LLM dimension scores in the final score merge (0.0 - 1.0)',
    min: 0,
    max: 1,
    step: 0.05,
  },
]

export default function Settings() {
  const [settings, setSettings] = useState({})
  const [original, setOriginal] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  // Email accounts state
  const [emailAccounts, setEmailAccounts] = useState([])
  const [emailLoading, setEmailLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [emailSaving, setEmailSaving] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [emailForm, setEmailForm] = useState({
    email: '', display_name: '', imap_host: '', imap_port: 993,
    smtp_host: '', smtp_port: 587, username: '', password: '',
    use_tls: true, enabled: true,
  })

  const fetchSettings = useCallback(async () => {
    try {
      const res = await api.getSettings()
      setSettings(res)
      setOriginal(res)
    } catch (err) {
      console.error('Failed to fetch settings:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  // Email accounts
  const fetchEmailAccounts = useCallback(async () => {
    try {
      const res = await api.getEmailAccounts()
      setEmailAccounts(res)
    } catch (err) {
      console.error('Failed to fetch email accounts:', err)
    } finally {
      setEmailLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchEmailAccounts()
  }, [fetchEmailAccounts])

  const resetEmailForm = () => {
    setEmailForm({
      email: '', display_name: '', imap_host: '', imap_port: 993,
      smtp_host: '', smtp_port: 587, username: '', password: '',
      use_tls: true, enabled: true,
    })
    setShowPassword(false)
  }

  const handleEmailSubmit = async (e) => {
    e.preventDefault()
    setEmailSaving(true)
    try {
      await api.createEmailAccount(emailForm)
      await fetchEmailAccounts()
      resetEmailForm()
      setShowAddForm(false)
    } catch (err) {
      console.error('Failed to save email account:', err)
    } finally {
      setEmailSaving(false)
    }
  }

  const handleDeleteEmail = async (id) => {
    try {
      await api.deleteEmailAccount(id)
      setEmailAccounts((prev) => prev.filter((a) => a.id !== id))
    } catch (err) {
      console.error('Failed to delete email account:', err)
    }
  }

  const handleChange = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
    setSaved(false)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const res = await api.updateSettings(settings)
      setSettings(res)
      setOriginal(res)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      console.error('Failed to save settings:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    setSettings({ ...original })
    setSaved(false)
  }

  const hasChanges = JSON.stringify(settings) !== JSON.stringify(original)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading settings…</div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-gray-400" />
          Settings
        </h1>
        <div className="flex items-center gap-2">
          {saved && (
            <span className="text-sm text-emerald-400">Settings saved</span>
          )}
          <button
            onClick={handleReset}
            disabled={!hasChanges}
            className="btn-secondary text-sm flex items-center gap-1 disabled:opacity-30"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>
          <button
            onClick={handleSave}
            disabled={!hasChanges || saving}
            className="btn-primary text-sm flex items-center gap-1 disabled:opacity-30"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Threshold Section */}
      <div className="card space-y-5">
        <h2 className="text-lg font-medium text-white">
          Analysis Thresholds
        </h2>
        <p className="text-sm text-gray-500">
          Configure scoring thresholds and weights for the manipulation analysis
          pipeline. Changes take effect immediately for new analyses.
        </p>

        {THRESHOLD_FIELDS.map((field) => (
          <div key={field.key}>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm font-medium text-gray-300">
                {field.label}
              </label>
              <span className="text-sm font-mono text-mindwall-300">
                {settings[field.key] ?? '—'}
              </span>
            </div>
            <p className="text-xs text-gray-500 mb-2">{field.description}</p>
            <input
              type="range"
              min={field.min}
              max={field.max}
              step={field.step || 1}
              value={settings[field.key] ?? field.min}
              onChange={(e) =>
                handleChange(field.key, parseFloat(e.target.value))
              }
              className="w-full h-1.5 bg-gray-700 rounded-full appearance-none cursor-pointer accent-mindwall-500"
            />
            <div className="flex justify-between text-xs text-gray-600 mt-0.5">
              <span>{field.min}</span>
              <span>{field.max}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Email Proxy Accounts */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium text-white flex items-center gap-2">
            <Mail className="w-5 h-5 text-gray-400" />
            Email Accounts
          </h2>
          <button
            onClick={() => { setShowAddForm(!showAddForm); resetEmailForm() }}
            className="btn-primary text-sm flex items-center gap-1"
          >
            <Plus className="w-4 h-4" />
            Add Account
          </button>
        </div>
        <p className="text-sm text-gray-500">
          Connect your email accounts so the MindWall proxy can intercept and
          analyse incoming and outgoing messages in real time.
        </p>

        {/* Add / Edit form */}
        {showAddForm && (
          <form onSubmit={handleEmailSubmit} className="space-y-4 border border-gray-700 rounded-lg p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Email Address</label>
                <input
                  type="email" required value={emailForm.email}
                  onChange={(e) => setEmailForm(p => ({ ...p, email: e.target.value }))}
                  className="input w-full" placeholder="user@example.com"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Display Name</label>
                <input
                  type="text" value={emailForm.display_name}
                  onChange={(e) => setEmailForm(p => ({ ...p, display_name: e.target.value }))}
                  className="input w-full" placeholder="John Doe"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">IMAP Host</label>
                <input
                  type="text" required value={emailForm.imap_host}
                  onChange={(e) => setEmailForm(p => ({ ...p, imap_host: e.target.value }))}
                  className="input w-full" placeholder="imap.gmail.com"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">IMAP Port</label>
                <input
                  type="number" required min="1" max="65535" value={emailForm.imap_port}
                  onChange={(e) => setEmailForm(p => ({ ...p, imap_port: parseInt(e.target.value) || 993 }))}
                  className="input w-full"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">SMTP Host</label>
                <input
                  type="text" required value={emailForm.smtp_host}
                  onChange={(e) => setEmailForm(p => ({ ...p, smtp_host: e.target.value }))}
                  className="input w-full" placeholder="smtp.gmail.com"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">SMTP Port</label>
                <input
                  type="number" required min="1" max="65535" value={emailForm.smtp_port}
                  onChange={(e) => setEmailForm(p => ({ ...p, smtp_port: parseInt(e.target.value) || 587 }))}
                  className="input w-full"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Username</label>
                <input
                  type="text" required value={emailForm.username}
                  onChange={(e) => setEmailForm(p => ({ ...p, username: e.target.value }))}
                  className="input w-full" placeholder="user@example.com"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Password / App Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'} required value={emailForm.password}
                    onChange={(e) => setEmailForm(p => ({ ...p, password: e.target.value }))}
                    className="input w-full pr-9" placeholder="••••••••"
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

            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                <input
                  type="checkbox" checked={emailForm.use_tls}
                  onChange={(e) => setEmailForm(p => ({ ...p, use_tls: e.target.checked }))}
                  className="accent-mindwall-500"
                />
                Use TLS
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                <input
                  type="checkbox" checked={emailForm.enabled}
                  onChange={(e) => setEmailForm(p => ({ ...p, enabled: e.target.checked }))}
                  className="accent-mindwall-500"
                />
                Enabled
              </label>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <button
                type="submit" disabled={emailSaving}
                className="btn-primary text-sm flex items-center gap-1 disabled:opacity-30"
              >
                <Save className="w-4 h-4" />
                {emailSaving ? 'Saving…' : 'Save Account'}
              </button>
              <button
                type="button"
                onClick={() => { setShowAddForm(false); resetEmailForm() }}
                className="btn-secondary text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Accounts list */}
        {emailLoading ? (
          <div className="text-gray-500 text-sm">Loading email accounts…</div>
        ) : emailAccounts.length === 0 ? (
          <div className="text-gray-500 text-sm py-4 text-center">
            No email accounts configured. Add one above to start proxying email.
          </div>
        ) : (
          <div className="space-y-3">
            {emailAccounts.map((acct) => (
              <div key={acct.id} className="flex items-center justify-between border border-gray-700 rounded-lg p-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium truncate">{acct.email}</span>
                    {acct.display_name && (
                      <span className="text-gray-500 text-sm">({acct.display_name})</span>
                    )}
                    <span className={`text-xs px-1.5 py-0.5 rounded ${acct.enabled ? 'bg-emerald-900/60 text-emerald-400' : 'bg-gray-700 text-gray-400'}`}>
                      {acct.enabled ? 'Active' : 'Disabled'}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    IMAP: {acct.imap_host}:{acct.imap_port} &nbsp;|&nbsp; SMTP: {acct.smtp_host}:{acct.smtp_port}
                    {acct.use_tls && ' (TLS)'}
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteEmail(acct.id)}
                  className="text-gray-500 hover:text-red-400 ml-3 flex-shrink-0"
                  title="Remove account"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* System Info */}
      <div className="card space-y-3">
        <h2 className="text-lg font-medium text-white">System Info</h2>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-gray-500 block text-xs">API Version</span>
            <span className="text-gray-300">{settings.api_version || '1.0.0'}</span>
          </div>
          <div>
            <span className="text-gray-500 block text-xs">LLM Model</span>
            <span className="text-gray-300">
              {settings.ollama_model || 'qwen3:8b'}
            </span>
          </div>
          <div>
            <span className="text-gray-500 block text-xs">Database</span>
            <span className="text-gray-300">SQLite (aiosqlite)</span>
          </div>
          <div>
            <span className="text-gray-500 block text-xs">Developer</span>
            <span className="text-gray-300">
              <a
                href="https://pradyumntandon.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-mindwall-400 hover:underline"
              >
                Pradyumn Tandon
              </a>
              {' @ '}
              <a
                href="https://vrip7.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-mindwall-400 hover:underline"
              >
                VRIP7
              </a>
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
