import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as dashboardApi from '../api/dashboard'

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchStats() {
    loading.value = true
    error.value = null
    try {
      stats.value = await dashboardApi.getDashboardStats()
    } catch (e) {
      error.value = e.message || '加载仪表盘数据失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  return { stats, loading, error, fetchStats }
})
