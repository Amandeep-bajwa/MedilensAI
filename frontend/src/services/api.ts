import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000
})

// Attach Bearer token to all outgoing requests if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('medilens_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Intercept 401s to purge stale credentials
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('medilens_token')
      localStorage.removeItem('medilens_user')
    }
    return Promise.reject(error)
  }
)
