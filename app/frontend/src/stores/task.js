import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref([])
  const currentTask = ref(null)
  const visualization = ref(null)
  const anomalies = ref([])

  async function fetchTasks(page = 1) {
    const res = await api.getTasks(page)
    tasks.value = res.data
    return res
  }

  async function fetchTaskStatus(taskId) {
    const status = await api.getTaskStatus(taskId)
    currentTask.value = status
    return status
  }

  async function fetchVisualization(taskId, indicator, depth) {
    const res = await api.getVisualization(taskId, indicator, depth)
    visualization.value = res.data
    return res.data
  }

  async function fetchAnomalies(taskId, page = 1) {
    const res = await api.getAnomalies(taskId, page)
    anomalies.value = res.data
    return res
  }

  function clear() {
    currentTask.value = null
    visualization.value = null
    anomalies.value = []
  }

  return {
    tasks,
    currentTask,
    visualization,
    anomalies,
    fetchTasks,
    fetchTaskStatus,
    fetchVisualization,
    fetchAnomalies,
    clear,
  }
})
