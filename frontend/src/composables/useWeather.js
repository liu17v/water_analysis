import { ref } from 'vue'
import { amapWeather } from '../utils/amap'

export function useWeather() {
  const weather = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchWeather(city) {
    loading.value = true
    error.value = null
    try {
      const data = await amapWeather(city)
      if (data) {
        weather.value = data
      } else {
        error.value = '暂无天气数据'
      }
    } catch (e) {
      error.value = e.message || '获取天气失败'
    } finally {
      loading.value = false
    }
  }

  return { weather, loading, error, fetchWeather }
}
