import api from './client'
import * as auth from './auth'
import * as task from './task'
import * as report from './report'
import * as anomaly from './anomaly'
import * as dashboard from './dashboard'

export { login, register, getMe, logout, getUsers, createUser, updateUser, deleteUser } from './auth'
export { upload, getTaskStatus, getTasks, deleteTask, updateTask, processTask, getStatistics, getDepthProfile, getRawData, getVisualization, getDistribution } from './task'
export { searchSimilar, generateReport, getReports, getReportStatus, deleteReport } from './report'
export { getAnomalies, exportAnomalies, exportAnomaliesXlsx, getAllAnomalies } from './anomaly'
export { getDashboardStats } from './dashboard'

export default {
  ...auth,
  ...task,
  ...report,
  ...anomaly,
  ...dashboard,
}
