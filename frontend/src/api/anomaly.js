import api from './client'

export function getAnomalies(taskId, page = 1, pageSize = 20) {
  return api.get(`/task/${taskId}/anomalies`, { params: { page, page_size: pageSize } })
}
export function exportAnomalies(taskId) {
  return `/api/task/${taskId}/anomalies/export`
}
export function exportAnomaliesXlsx(taskId) {
  return `/api/task/${taskId}/anomalies/export?format=xlsx`
}
export function getAllAnomalies(page = 1, pageSize = 20, filters = {}) {
  return api.get('/anomalies', { params: { page, page_size: pageSize, ...filters } })
}
