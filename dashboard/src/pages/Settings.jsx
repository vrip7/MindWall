/**
 * MindWall — Settings Page
 * Runtime-configurable thresholds and system settings
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Settings as SettingsIcon, Save, RotateCcw } from 'lucide-react'
import api from '../api/client'

const THRESHOLD_FIELDS = [
  {
    key: 'alert_threshold_critical',
    label: 'Critical Alert Threshold',
    description: 'Score at or above which an alert is classified as critical',
    min: 0,
    max: 100,
  },
  {
    key: 'alert_threshold_high',
    label: 'High Alert Threshold',
    description: 'Score at or above which an alert is classified as high severity',
    min: 0,
    max: 100,
  },
  {
    key: 'alert_threshold_medium',
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
              {settings.ollama_model || 'mindwall-llama3.1'}
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
