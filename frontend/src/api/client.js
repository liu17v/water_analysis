import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => {
    const data = res.data
    if (data.status === 0) {
      ElMessage.error(data.messages || '请求失败')
      return Promise.reject(new Error(data.messages))
    }
    return data.datas || data
  },
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.hash !== '#/login') {
        window.location.hash = '#/login'
      }
    }
    ElMessage.error(err.response?.data?.detail || err.message || '网络错误')
    return Promise.reject(err)
  },
)

export default api
