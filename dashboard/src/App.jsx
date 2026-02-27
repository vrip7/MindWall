/**
 * MindWall — Main Application Component
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Alerts from './pages/Alerts'
import Employees from './pages/Employees'
import Settings from './pages/Settings'

export default function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/employees" element={<Employees />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Router>
  )
}
