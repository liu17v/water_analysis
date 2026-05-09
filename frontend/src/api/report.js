import api from './client'

export function searchSimilar(taskId) {
  return api.post(`/task/${taskId}/similar`)
}
export function generateReport(taskId) {
  return api.post(`/task/${taskId}/generate_report`, {}, { timeout: 600000 })
}
export function getReports(page = 1, pageSize = 20) {
  return api.get('/reports', { params: { page, page_size: pageSize } })
}
export function getReportStatus(taskId) {
  return api.get(`/task/${taskId}/report_status`)
}
export function deleteReport(taskId) {
  return api.delete(`/report/${taskId}`)
}
