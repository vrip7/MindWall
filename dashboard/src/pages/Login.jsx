/**
 * MindWall — Login Page
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, LogIn } from 'lucide-react'
import api from '../api/client'

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = await api.login({ username, password })
      localStorage.setItem('mindwall_api_key', res.api_key)
      onLogin()
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <Shield className="h-12 w-12 text-mindwall-500 mb-3" />
          <h1 className="text-2xl font-bold text-white">MindWall</h1>
          <p className="text-sm text-gray-500 mt-1">Cognitive Firewall Dashboard</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          {error && (
            <div className="text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-mindwall-500 focus:ring-1 focus:ring-mindwall-500"
              placeholder="Enter username"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-mindwall-500 focus:ring-1 focus:ring-mindwall-500"
              placeholder="Enter password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary flex items-center justify-center gap-2 py-2.5 disabled:opacity-50"
          >
            <LogIn className="w-4 h-4" />
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <div className="text-center mt-6">
          <p className="text-xs text-gray-600">
            Developed by{' '}
            <a href="https://pradyumntandon.com" target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-mindwall-400">
              Pradyumn Tandon
            </a>
            {' @ '}
            <a href="https://vrip7.com" target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-mindwall-400">
              VRIP7
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
