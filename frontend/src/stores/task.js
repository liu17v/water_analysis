import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import * as taskApi from '../api/task'

export const useTaskStore = defineStore('task', () => {
  // 任务列表
  const taskList = ref([])
  const total = ref(0)
  const loading = reactive({ list: false, detail: false, stats: false, rawData: false, visualization: false })
  const error = reactive({ list: null, detail: null, stats: null, rawData: null, visualization: null })

  // 当前任务详情
  const currentTask = ref(null)
  const currentStatus = ref(null)

  // 统计数据
  const statistics = ref(null)
  const distribution = ref(null)
  const rawData = ref({ items: [], total: 0 })
  const visualization = ref(null)
  const depthProfile = ref(null)

  async function fetchTasks(page = 1, pageSize = 20, extra = {}) {
    loading.list = true
    error.list = null
    try {
      const res = await taskApi.getTasks(page, pageSize, extra)
      taskList.value = res.items || res
      total.value = res.total || 0
      return res
    } catch (e) {
      error.list = e.message || '加载任务列表失败'
      throw e
    } finally {
      loading.list = false
    }
  }

  async function fetchTaskDetail(taskId) {
    loading.detail = true
    error.detail = null
    try {
      const res = await taskApi.getTasks(1, 1, { search: taskId })
      currentTask.value = res.items?.[0] || null
      return currentTask.value
    } catch (e) {
      error.detail = e.message || '加载任务详情失败'
      throw e
    } finally {
      loading.detail = false
    }
  }

  async function pollTaskStatus(taskId) {
    try {
      currentStatus.value = await taskApi.getTaskStatus(taskId)
      return currentStatus.value.status !== 'processing'
    } catch {
      return false
    }
  }

  async function fetchStatistics(taskId) {
    loading.stats = true
    error.stats = null
    try {
      statistics.value = await taskApi.getStatistics(taskId)
    } catch (e) {
      error.stats = e.message || '加载统计数据失败'
      throw e
    } finally {
      loading.stats = false
    }
  }

  async function fetchDistribution(taskId, indicator, bins = 20) {
    try {
      distribution.value = await taskApi.getDistribution(taskId, indicator, bins)
    } catch (e) {
      console.error('加载分布数据失败', e)
    }
  }

  async function fetchRawData(taskId, page = 1, pageSize = 50) {
    loading.rawData = true
    error.rawData = null
    try {
      const res = await taskApi.getRawData(taskId, page, pageSize)
      rawData.value = res
    } catch (e) {
      error.rawData = e.message || '加载原始数据失败'
      throw e
    } finally {
      loading.rawData = false
    }
  }

  async function fetchVisualization(taskId, indicator, depth) {
    loading.visualization = true
    error.visualization = null
    try {
      visualization.value = await taskApi.getVisualization(taskId, indicator, depth)
    } catch (e) {
      error.visualization = e.message || '加载可视化数据失败'
      throw e
    } finally {
      loading.visualization = false
    }
  }

  async function fetchDepthProfile(taskId, indicator) {
    try {
      depthProfile.value = await taskApi.getDepthProfile(taskId, indicator)
    } catch (e) {
      console.error('加载深度剖面失败', e)
    }
  }

  async function deleteTask(taskId) {
    try {
      await taskApi.deleteTask(taskId)
      taskList.value = taskList.value.filter(t => t.task_id !== taskId)
    } catch (e) {
      console.error('删除任务失败', e)
      throw e
    }
  }

  async function updateTask(taskId, data) {
    try {
      await taskApi.updateTask(taskId, data)
    } catch (e) {
      console.error('更新任务失败', e)
      throw e
    }
  }

  async function processTask(taskId) {
    try {
      await taskApi.processTask(taskId)
    } catch (e) {
      console.error('重新处理任务失败', e)
      throw e
    }
  }

  function clear() {
    currentTask.value = null
    currentStatus.value = null
    statistics.value = null
    distribution.value = null
    rawData.value = { items: [], total: 0 }
    visualization.value = null
    depthProfile.value = null
  }

  return {
    taskList, total, loading, error,
    currentTask, currentStatus,
    statistics, distribution, rawData, visualization, depthProfile,
    fetchTasks, fetchTaskDetail, pollTaskStatus,
    fetchStatistics, fetchDistribution, fetchRawData, fetchVisualization, fetchDepthProfile,
    deleteTask, updateTask, processTask, clear,
  }
})
