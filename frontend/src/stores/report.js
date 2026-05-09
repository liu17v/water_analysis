import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import * as reportApi from '../api/report'

export const useReportStore = defineStore('report', () => {
  const reportStatus = ref(null)
  const similarTasks = ref([])
  const reportList = ref([])
  const reportTotal = ref(0)
  const loading = reactive({ list: false, generate: false, similar: false })
  const error = reactive({ list: null, generate: null, similar: null })

  async function fetchReportStatus(taskId) {
    reportStatus.value = await reportApi.getReportStatus(taskId)
    return reportStatus.value
  }

  async function generateReport(taskId) {
    loading.generate = true
    error.generate = null
    try {
      await reportApi.generateReport(taskId)
    } catch (e) {
      error.generate = e.message || '生成报告失败'
      throw e
    } finally {
      loading.generate = false
    }
  }

  async function searchSimilar(taskId) {
    loading.similar = true
    error.similar = null
    try {
      similarTasks.value = await reportApi.searchSimilar(taskId)
      return similarTasks.value
    } catch (e) {
      error.similar = e.message || '搜索相似案例失败'
      throw e
    } finally {
      loading.similar = false
    }
  }

  async function fetchReports(page = 1, pageSize = 20) {
    loading.list = true
    error.list = null
    try {
      const res = await reportApi.getReports(page, pageSize)
      reportList.value = res.items || res
      reportTotal.value = res.total || 0
      return res
    } catch (e) {
      error.list = e.message || '加载报告列表失败'
      throw e
    } finally {
      loading.list = false
    }
  }

  async function deleteReport(taskId) {
    await reportApi.deleteReport(taskId)
    reportList.value = reportList.value.filter(r => r.task_id !== taskId)
  }

  return {
    reportStatus, similarTasks, reportList, reportTotal,
    loading, error,
    fetchReportStatus, generateReport, searchSimilar,
    fetchReports, deleteReport,
  }
})
