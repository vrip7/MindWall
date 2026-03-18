/**
 * MindWall — Axios HTTP Client
 * Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)
 */

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5297'

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

// Response interceptor — extract data and handle errors
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      // Clear stale key and redirect to login
      localStorage.removeItem('mindwall_api_key')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// API functions
export const api = {
  // Auth
  login: (data) => client.post('/auth/login', data),

  // Dashboard
  getDashboardSummary: () => client.get('/api/dashboard/summary'),
  getDashboardTimeline: (params) => client.get('/api/dashboard/timeline', { params }),

  // Alerts
  getAlerts: (params) => client.get('/api/alerts', { params }),
  getAlertDetail: (id) => client.get(`/api/alerts/${id}`),
  acknowledgeAlert: (id, data) => client.patch(`/api/alerts/${id}/acknowledge`, data),

  // Employees
  getEmployees: (params) => client.get('/api/employees', { params }),
  createEmployee: (data) => client.post('/api/employees', data),
  deleteEmployee: (id) => client.delete(`/api/employees/${id}`),
  getEmployeeRiskProfile: (email) => client.get(`/api/employees/${encodeURIComponent(email)}/risk-profile`),
  getEmployeeProxyInfo: (email) => client.get(`/api/employees/${encodeURIComponent(email)}/proxy-info`),

  // Settings
  getSettings: () => client.get('/api/settings'),
  updateSettings: (data) => client.put('/api/settings', data),

  // Email Accounts
  getEmailAccounts: () => client.get('/api/email-accounts'),
  createEmailAccount: (data) => client.post('/api/email-accounts', data),
  deleteEmailAccount: (id) => client.delete(`/api/email-accounts/${id}`),

  // Health
  checkHealth: () => client.get('/health'),
}

export default api
