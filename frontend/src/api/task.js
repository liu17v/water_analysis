import api from './client'

// Upload
export function upload(formData) {
  return api.post('/upload', formData)
}

// Task CRUD
export function getTaskStatus(taskId) {
  return api.get(`/task/${taskId}/status`)
}
export function getTasks(page = 1, pageSize = 20, extra = {}) {
  return api.get('/tasks', { params: { page, page_size: pageSize, ...extra } })
}
export function deleteTask(taskId) {
  return api.delete(`/task/${taskId}`)
}
export function updateTask(taskId, data) {
  return api.put(`/task/${taskId}`, data)
}
export function processTask(taskId) {
  return api.post(`/task/${taskId}/process`)
}

// Statistics
export function getStatistics(taskId) {
  return api.get(`/task/${taskId}/statistics`)
}
export function getDepthProfile(taskId, indicator = 'chlorophyll') {
  return api.get(`/task/${taskId}/depth_profile`, { params: { indicator } })
}
export function getRawData(taskId, page = 1, pageSize = 50) {
  return api.get(`/task/${taskId}/raw_data`, { params: { page, page_size: pageSize } })
}

// Visualization
export function getVisualization(taskId, indicator, depth) {
  return api.get(`/task/${taskId}/visualization`, { params: { indicator, depth } })
}

// Distribution
export function getDistribution(taskId, indicator, bins = 20) {
  return api.get(`/task/${taskId}/distribution`, { params: { indicator, bins } })
}
