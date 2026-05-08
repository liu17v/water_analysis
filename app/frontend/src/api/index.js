import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => {
    const data = res.data
    if (data.status === 0) {
      ElMessage.error(data.messages || '请求失败')
      return Promise.reject(new Error(data.messages))
    }
    return data.datas || data
  },
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.hash !== '#/login') {
        window.location.hash = '#/login'
      }
    }
    ElMessage.error(err.response?.data?.detail || err.message || '网络错误')
    return Promise.reject(err)
  },
)

export default {
  // Upload
  upload(formData) {
    return api.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
  },

  // Task
  getTaskStatus(taskId) {
    return api.get(`/task/${taskId}/status`)
  },
  getTasks(page = 1, pageSize = 20) {
    return api.get('/tasks', { params: { page, page_size: pageSize } })
  },
  deleteTask(taskId) {
    return api.delete(`/task/${taskId}`)
  },

  // Visualization
  getVisualization(taskId, indicator, depth) {
    return api.get(`/task/${taskId}/visualization`, { params: { indicator, depth } })
  },

  // Anomalies
  getAnomalies(taskId, page = 1, pageSize = 20) {
    return api.get(`/task/${taskId}/anomalies`, { params: { page, page_size: pageSize } })
  },
  exportAnomalies(taskId) {
    return `/api/task/${taskId}/anomalies/export`
  },

  // Report
  searchSimilar(taskId) {
    return api.post(`/task/${taskId}/similar`)
  },
  generateReport(taskId) {
    return api.post(`/task/${taskId}/generate_report`)
  },

  // Statistics
  getStatistics(taskId) {
    return api.get(`/task/${taskId}/statistics`)
  },
  getDepthProfile(taskId, indicator = 'chlorophyll') {
    return api.get(`/task/${taskId}/depth_profile`, { params: { indicator } })
  },
  getRawData(taskId, page = 1, pageSize = 50) {
    return api.get(`/task/${taskId}/raw_data`, { params: { page, page_size: pageSize } })
  },

  // Dashboard
  getDashboardStats() {
    return api.get('/dashboard/stats')
  },

  // Distribution
  getDistribution(taskId, indicator, bins = 20) {
    return api.get(`/task/${taskId}/distribution`, { params: { indicator, bins } })
  },

  // Cross-task management
  getAllAnomalies(page = 1, pageSize = 20, filters = {}) {
    return api.get('/anomalies', { params: { page, page_size: pageSize, ...filters } })
  },
  getReports(page = 1, pageSize = 20) {
    return api.get('/reports', { params: { page, page_size: pageSize } })
  },
  getReportStatus(taskId) {
    return api.get(`/task/${taskId}/report_status`)
  },
  deleteReport(taskId) {
    return api.delete(`/report/${taskId}`)
  },

  // Auth
  login(username, password) {
    return api.post('/auth/login', { username, password })
  },
  register(username, password) {
    return api.post('/auth/register', { username, password })
  },
  getMe() {
    return api.get('/auth/me')
  },
  logout() {
    return api.post('/auth/logout')
  },

  // User management (admin)
  getUsers(page = 1, pageSize = 20) {
    return api.get('/users', { params: { page, page_size: pageSize } })
  },
  createUser(data) {
    return api.post('/users', data)
  },
  updateUser(userId, data) {
    return api.put(`/user/${userId}`, data)
  },
  deleteUser(userId) {
    return api.delete(`/user/${userId}`)
  },

  // Task update
  updateTask(taskId, data) {
    return api.put(`/task/${taskId}`, data)
  },
  processTask(taskId) {
    return api.post(`/task/${taskId}/process`)
  },
}
