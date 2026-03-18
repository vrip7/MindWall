/**
 * MindWall — Main Application Component
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React, { useState, useCallback } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Alerts from './pages/Alerts'
import Employees from './pages/Employees'
import Settings from './pages/Settings'
import Login from './pages/Login'

export default function App() {
  const [authenticated, setAuthenticated] = useState(
    () => !!localStorage.getItem('mindwall_api_key')
  )

  const handleLogin = useCallback(() => setAuthenticated(true), [])
  const handleLogout = useCallback(() => {
    localStorage.removeItem('mindwall_api_key')
    setAuthenticated(false)
  }, [])

  if (!authenticated) {
    return (
      <Router>
        <Routes>
          <Route path="/login" element={<Login onLogin={handleLogin} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    )
  }

  return (
    <Router>
      <Layout onLogout={handleLogout}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/employees" element={<Employees />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/login" element={<Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  )
}
