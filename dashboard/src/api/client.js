/**
 * MindWall — Axios HTTP Client
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor for API key
client.interceptors.request.use(
  (config) => {
    const apiKey = localStorage.getItem('mindwall_api_key')
    if (apiKey) {
      config.headers['X-MindWall-Key'] = apiKey
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      console.error('MindWall API: Authentication failed')
    }
    return Promise.reject(error)
  }
)

// API functions
export const api = {
  // Dashboard
  getDashboardSummary: () => client.get('/api/dashboard/summary'),
  getTimeline: (params) => client.get('/api/dashboard/timeline', { params }),

  // Alerts
  getAlerts: (params) => client.get('/api/alerts', { params }),
  getAlertDetail: (id) => client.get(`/api/alerts/${id}`),
  acknowledgeAlert: (id, data) => client.patch(`/api/alerts/${id}/acknowledge`, data),

  // Employees
  getEmployees: (params) => client.get('/api/employees', { params }),
  createEmployee: (data) => client.post('/api/employees', data),
  getEmployeeRiskProfile: (email) => client.get(`/api/employees/${encodeURIComponent(email)}/risk-profile`),

  // Settings
  getSettings: () => client.get('/api/settings'),
  updateSettings: (data) => client.put('/api/settings', data),

  // Health
  checkHealth: () => client.get('/health'),
}

export default client
