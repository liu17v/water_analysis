import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

api.interceptors.response.use(
  (res) => {
    const data = res.data
    // 业务层响应: status=1 成功, status=0 失败
    if (data.status === 0) {
      ElMessage.error(data.messages || '请求失败')
      return Promise.reject(new Error(data.messages))
    }
    return data.datas || data
  },
  (err) => {
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
    return api.get('/tasks', { params: { page: 1, page_size: 100 } })
  },
}
