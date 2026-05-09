# Frontend 完整重写实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 基于后端 29 个 API 端点，完整重写前端，解决 API 调用混乱、组件复用差、错误处理薄弱、UI 粗糙、报告超时等问题。

**架构：** View → Pinia Store → API 单向数据流。统一 loading/error 状态管理。History 模式路由，base 为 `/ui/`。可视化组件从 views 中分离为共享组件。

**技术栈：** Vue 3 (Composition API + `<script setup>`), Vite 5, Element Plus, ECharts, Leaflet, Pinia, Axios, Vue Router 4 (History mode)

---

## 文件清单

### 修改文件
| 文件 | 变更说明 |
|------|---------|
| `frontend/vite.config.js` | base 改为 `/ui/` |
| `frontend/src/main.js` | 不变（已满足需求） |
| `frontend/src/App.vue` | 引入 AppSidebar/AppHeader 子组件，简化根布局 |
| `frontend/src/api/client.js` | 401 拦截器从 hash 跳转改为 history push |
| `frontend/src/api/index.js` | 统一导出（增加导出函数） |
| `frontend/src/stores/auth.js` | 改为 setup 语法，保持逻辑不变 |
| `frontend/src/router/index.js` | 改为 createWebHistory，base `/ui/`，更新路径前缀 |

### 重写文件（用新逻辑替换全部内容）
| 文件 | 说明 |
|------|------|
| `frontend/src/stores/task.js` | 完整的 task store，覆盖所有 API |
| `frontend/src/views/*.vue` (10 files) | 所有视图 |
| `frontend/src/composables/useTask.js` | 拆分为 useIndicator + useStatus |

### 新建文件
| 文件 | 说明 |
|------|------|
| `frontend/src/stores/dashboard.js` | 仪表盘 store |
| `frontend/src/stores/report.js` | 报告 store |
| `frontend/src/composables/usePolling.js` | 通用轮询 composable |
| `frontend/src/composables/useIndicator.js` | 指标映射 composable |
| `frontend/src/composables/useStatus.js` | 状态映射 composable |
| `frontend/src/components/layout/AppSidebar.vue` | 侧边栏 |
| `frontend/src/components/layout/AppHeader.vue` | 顶栏 |
| `frontend/src/components/common/StatusTag.vue` | 状态标签 |
| `frontend/src/components/common/IndicatorSelect.vue` | 指标选择器 |
| `frontend/src/components/common/LoadingOverlay.vue` | 加载遮罩 |
| `frontend/src/components/common/EmptyState.vue` | 空状态 |
| `frontend/src/components/visualization/ContourPanel.vue` | 2D 等值线 |
| `frontend/src/components/visualization/PointCloudFrame.vue` | 3D 体渲染 |
| `frontend/src/components/visualization/DepthProfilePanel.vue` | 深度剖面 |
| `frontend/src/components/map/SampleMap.vue` | 采样点地图 |
| `frontend/src/components/map/AnomalyMap.vue` | 异常点地图 |

### 删除文件
| 文件 | 原因 |
|------|------|
| `frontend/src/composables/useTask.js` | 拆分为 useIndicator + useStatus |
| `frontend/src/components/ContourPanel.vue` | 迁移到 visualization/ 目录 |
| `frontend/src/components/PointCloudFrame.vue` | 迁移到 visualization/ 目录 |
| `frontend/src/components/FileDrop.vue` | 不再需要独立组件，功能合入 UploadView |

---

## 任务分解

---

### Task 1: Vite 配置 + 路由

**前置依赖：** 无

**涉及文件：**
- 修改: `frontend/vite.config.js`
- 修改: `frontend/src/router/index.js`
- 修改: `frontend/src/api/client.js`

#### Step 1: 修改 vite.config.js

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => ({
  plugins: [vue()],
  base: '/ui/',
  server: {
    port: 3000,
    proxy: {
      '/api': { target: 'http://localhost:8000', timeout: 600000, proxyTimeout: 600000 },
      '/reports': { target: 'http://localhost:8000', timeout: 600000, proxyTimeout: 600000 },
      '/3d': { target: 'http://localhost:8000', timeout: 600000, proxyTimeout: 600000 },
    },
  },
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
}))
```

变更要点：`base` 从 `mode === 'production' ? '/static/' : '/'` 简化为 `'/ui/'`。（开发/生产都用 `/ui/`，后端统一处理。）

#### Step 2: 重写 router/index.js

```js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('../views/UploadView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/tasks',
    name: 'TaskList',
    component: () => import('../views/TaskListView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/task/:id',
    name: 'TaskDetail',
    component: () => import('../views/TaskDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/task/:id/anomalies',
    name: 'TaskAnomalies',
    component: () => import('../views/AnomalyListView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/task/:id/report',
    name: 'TaskReport',
    component: () => import('../views/ReportView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/anomalies',
    name: 'AnomalyManage',
    component: () => import('../views/AnomalyListView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/compare',
    name: 'Compare',
    component: () => import('../views/CompareView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/reports',
    name: 'ReportManage',
    component: () => import('../views/ReportManageView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/users',
    name: 'UserManage',
    component: () => import('../views/UserManageView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
]

const router = createRouter({
  history: createWebHistory('/ui/'),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }
  if (to.meta.guest && token) {
    return next('/')
  }
  next()
})

export default router
```

变更要点：`createWebHashHistory` → `createWebHistory('/ui/')`，路径加上 `/ui/` 前缀，`MapView` 路由移除（地图功能合入组件）。

#### Step 3: 更新 api/client.js 的重定向逻辑

```js
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
      window.location.href = '/ui/login'
    }
    ElMessage.error(err.response?.data?.detail || err.message || '网络错误')
    return Promise.reject(err)
  },
)

export default api
```

变更要点：`window.location.hash` → `window.location.href`。

#### Step 4: 验证

运行 `npm run dev`，确认 dev server 启动在 3000 端口，访问 `http://localhost:3000/ui/login` 能正常加载。

#### Step 5: 提交测试结果

确认无误后，继续下一任务。

---

### Task 2: API 层统一导出

**前置依赖：** 无（独立于 Task 1）

**涉及文件：**
- 修改: `frontend/src/api/index.js`

#### Step 1: 重写 api/index.js

```js
export { login, register, getMe, logout, getUsers, createUser, updateUser, deleteUser } from './auth'
export { upload, getTaskStatus, getTasks, deleteTask, updateTask, processTask, getStatistics, getDepthProfile, getRawData, getVisualization, getDistribution } from './task'
export { searchSimilar, generateReport, getReports, getReportStatus, deleteReport } from './report'
export { getAnomalies, exportAnomalies, exportAnomaliesXlsx, getAllAnomalies } from './anomaly'
export { getDashboardStats } from './dashboard'
```

与当前一致，不需要改动。注：`api/index.js` 只用于 store 层导入，views 不直接引用。

---

### Task 3: Composables

**前置依赖：** 无

**涉及文件：**
- 创建: `frontend/src/composables/usePolling.js`
- 创建: `frontend/src/composables/useIndicator.js`
- 创建: `frontend/src/composables/useStatus.js`
- 删除: `frontend/src/composables/useTask.js`（被分解为上两个 composable）

#### Step 1: 创建 usePolling.js

```js
import { ref, onUnmounted } from 'vue'

/**
 * 通用轮询 composable
 * @param {Function} fn - 轮询执行的异步函数，返回 true 时停止轮询
 * @param {number} interval - 轮询间隔（ms）
 * @param {number} maxDuration - 最大轮询时长（ms），默认不限制
 * @returns {{ start: Function, stop: Function, isPolling: Ref<boolean>, elapsed: Ref<number> }}
 */
export function usePolling(fn, interval = 2000, maxDuration = 0) {
  const isPolling = ref(false)
  const elapsed = ref(0)
  let timer = null
  let startTime = null
  let durationTimer = null

  function start() {
    if (isPolling.value) return
    isPolling.value = true
    elapsed.value = 0
    startTime = Date.now()

    const tick = async () => {
      if (!isPolling.value) return
      const shouldStop = await fn()
      elapsed.value = Date.now() - startTime
      if (shouldStop || (maxDuration > 0 && elapsed.value >= maxDuration)) {
        stop()
        return
      }
      timer = setTimeout(tick, interval)
    }

    tick()

    if (maxDuration > 0) {
      durationTimer = setTimeout(() => {
        if (isPolling.value) stop()
      }, maxDuration)
    }
  }

  function stop() {
    isPolling.value = false
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    if (durationTimer) {
      clearTimeout(durationTimer)
      durationTimer = null
    }
  }

  onUnmounted(stop)

  return { start, stop, isPolling, elapsed }
}
```

#### Step 2: 创建 useIndicator.js

```js
const INDICATOR_OPTIONS = [
  { label: '叶绿素 (Chl)', value: 'chlorophyll' },
  { label: '溶解氧 (DO)', value: 'dissolved_oxygen' },
  { label: '水温 (Temp)', value: 'temperature' },
  { label: 'pH', value: 'ph' },
  { label: '浊度 (Turb)', value: 'turbidity' },
]

const INDICATOR_LABEL = {
  chlorophyll: '叶绿素', dissolved_oxygen: '溶解氧',
  temperature: '水温', ph: 'pH', turbidity: '浊度',
}

const INDICATOR_SHORT = {
  chlorophyll: 'chl', dissolved_oxygen: 'odo',
  temperature: 'temp', ph: 'ph', turbidity: 'turb',
}

const INDICATOR_UNIT = {
  chlorophyll: 'µg/L', dissolved_oxygen: 'mg/L',
  temperature: '°C', ph: '', turbidity: 'NTU',
}

const INDICATOR_COLOR = {
  chlorophyll: '#67c23a', dissolved_oxygen: '#409eff',
  temperature: '#e6a23c', ph: '#f56c6c', turbidity: '#909399',
}

export function useIndicator() {
  function shortLabel(code) {
    return INDICATOR_LABEL[code] || code
  }
  function shortCode(full) {
    return INDICATOR_SHORT[full] || 'chl'
  }
  function indicatorUnit(full) {
    return INDICATOR_UNIT[full] || ''
  }
  function indicatorColor(code) {
    return INDICATOR_COLOR[code] || '#909399'
  }

  return { shortLabel, shortCode, indicatorUnit, indicatorColor, INDICATOR_OPTIONS }
}
```

#### Step 3: 创建 useStatus.js

```js
const STATUS_MAP = {
  pending: '待处理', processing: '处理中',
  success: '已完成', failed: '失败',
}

const STATUS_TYPE_MAP = {
  pending: 'info', processing: 'warning',
  success: 'success', failed: 'danger',
}

export function useStatus() {
  function statusLabel(s) {
    return STATUS_MAP[s] || s
  }
  function statusType(s) {
    return STATUS_TYPE_MAP[s] || 'info'
  }
  return { statusLabel, statusType }
}
```

#### Step 4: 删除旧的 useTask.js

```bash
rm "D:\water_analysis\frontend\src\composables\useTask.js"
```

---

### Task 4: Pinia Stores

**前置依赖：** Task 2 (API layer), Task 3 (composables)

**涉及文件：**
- 创建: `frontend/src/stores/dashboard.js`
- 创建: `frontend/src/stores/report.js`
- 重写: `frontend/src/stores/auth.js`（改为 setup 语法）
- 重写: `frontend/src/stores/task.js`

#### Step 1: 重写 stores/auth.js（setup 语法）

```js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('token') || '')

  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const username = computed(() => user.value?.username || '')
  const role = computed(() => user.value?.role || '')
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(username, password) {
    const res = await authApi.login(username, password)
    token.value = res.token
    user.value = res.user
    localStorage.setItem('token', res.token)
    localStorage.setItem('user', JSON.stringify(res.user))
  }

  async function register(username, password) {
    await authApi.register(username, password)
  }

  async function fetchUser() {
    try {
      const res = await authApi.getMe()
      user.value = res
      localStorage.setItem('user', JSON.stringify(res))
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    authApi.logout().catch(() => {})
  }

  return { user, token, isLoggedIn, username, role, isAdmin, login, register, fetchUser, logout }
})
```

仅改为 setup 语法，行为不变。

#### Step 2: 创建 stores/dashboard.js

```js
import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
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
```

#### Step 3: 重写 stores/task.js

```js
import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import * as taskApi from '../api/task'

export const useTaskStore = defineStore('task', () => {
  // 任务列表
  const taskList = ref([])
  const total = ref(0)
  const loading = reactive({ list: false, detail: false, stats: false, rawData: false, visualization: false })
  const error = reactive({ list: null, detail: null, stats: null, rawData: null, visualization: null })

  // 当前任务详情（从 taskList 中获取的完整信息）
  const currentTask = ref(null)

  // 当前任务状态（轮询用）
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
    distribution.value = await taskApi.getDistribution(taskId, indicator, bins)
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
    depthProfile.value = await taskApi.getDepthProfile(taskId, indicator)
  }

  async function deleteTask(taskId) {
    await taskApi.deleteTask(taskId)
    taskList.value = taskList.value.filter(t => t.task_id !== taskId)
  }

  async function updateTask(taskId, data) {
    await taskApi.updateTask(taskId, data)
  }

  async function processTask(taskId) {
    await taskApi.processTask(taskId)
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
```

#### Step 4: 创建 stores/report.js

```js
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
```

---

### Task 5: Layout 组件 + App.vue

**前置依赖：** Task 4 (stores)

**涉及文件：**
- 创建: `frontend/src/components/layout/AppSidebar.vue`
- 创建: `frontend/src/components/layout/AppHeader.vue`
- 重写: `frontend/src/App.vue`

#### Step 1: 创建 AppSidebar.vue

```vue
<template>
  <el-aside :width="isCollapse ? '64px' : '220px'" class="app-aside">
    <div class="logo" @click="$router.push('/')">
      <el-icon :size="24"><Odometer /></el-icon>
      <span v-show="!isCollapse" class="logo-text">水质监测系统</span>
    </div>
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapse"
      :collapse-transition="false"
      router
      background-color="#1a3a5c"
      text-color="#bfcbd9"
      active-text-color="#409eff"
    >
      <el-menu-item index="/">
        <el-icon><DataBoard /></el-icon>
        <span>仪表盘</span>
      </el-menu-item>
      <el-menu-item index="/upload">
        <el-icon><Upload /></el-icon>
        <span>数据上传</span>
      </el-menu-item>
      <el-menu-item index="/tasks">
        <el-icon><List /></el-icon>
        <span>任务列表</span>
      </el-menu-item>
      <el-menu-item index="/compare">
        <el-icon><Sort /></el-icon>
        <span>数据对比</span>
      </el-menu-item>
      <el-menu-item index="/anomalies">
        <el-icon><WarningFilled /></el-icon>
        <span>异常管理</span>
      </el-menu-item>
      <el-menu-item index="/reports">
        <el-icon><Document /></el-icon>
        <span>智能报告</span>
      </el-menu-item>
      <el-menu-item v-if="authStore.isAdmin" index="/users">
        <el-icon><UserFilled /></el-icon>
        <span>用户管理</span>
      </el-menu-item>
    </el-menu>
    <div class="collapse-btn" @click="emit('toggle')">
      <el-icon :size="16">
        <component :is="isCollapse ? 'DArrowRight' : 'DArrowLeft'" />
      </el-icon>
    </div>
  </el-aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

defineProps({ isCollapse: Boolean })
const emit = defineEmits(['toggle'])
const route = useRoute()
const authStore = useAuthStore()

const activeMenu = computed(() => {
  const path = route.path
  if (['/', '/upload', '/tasks', '/compare', '/anomalies', '/reports', '/users'].includes(path)) return path
  return ''
})
</script>

<style scoped>
.app-aside { background: #1a3a5c; transition: width 0.3s; overflow: hidden; display: flex; flex-direction: column; }
.logo { display: flex; align-items: center; gap: 10px; padding: 16px 20px; color: #fff; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.1); }
.logo-text { font-size: 16px; font-weight: 700; white-space: nowrap; }
.collapse-btn { padding: 12px; text-align: center; color: #bfcbd9; cursor: pointer; border-top: 1px solid rgba(255,255,255,0.1); }
.collapse-btn:hover { color: #fff; background: rgba(255,255,255,0.05); }
</style>
```

#### Step 2: 创建 AppHeader.vue

```vue
<template>
  <el-header class="app-header">
    <div class="header-left">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item v-if="breadcrumb1" :to="breadcrumb1.to">{{ breadcrumb1.label }}</el-breadcrumb-item>
        <el-breadcrumb-item v-if="breadcrumb2">{{ breadcrumb2 }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-right">
      <el-tag type="success" size="small" effect="dark">系统运行中</el-tag>
      <span class="header-user">
        <el-icon><UserFilled /></el-icon>
        <span style="margin:0 4px">{{ authStore.username || '管理员' }}</span>
        <span v-if="authStore.role" class="role-tag">{{ authStore.isAdmin ? '管理员' : '用户' }}</span>
      </span>
      <el-button text type="danger" size="small" @click="handleLogout">
        <el-icon><SwitchButton /></el-icon> 退出
      </el-button>
    </div>
  </el-header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const breadcrumb1 = computed(() => {
  const path = route.path
  const map = {
    '/upload': { label: '数据上传', to: '/upload' },
    '/tasks': { label: '任务列表', to: '/tasks' },
    '/compare': { label: '数据对比', to: '/compare' },
    '/anomalies': { label: '异常管理', to: '/anomalies' },
    '/reports': { label: '智能报告', to: '/reports' },
    '/users': { label: '用户管理', to: '/users' },
  }
  if (map[path]) return map[path]
  if (path.startsWith('/task/')) return { label: '任务详情', to: null }
  return null
})

const breadcrumb2 = computed(() => {
  if (route.path.match(/\/anomalies$/)) return '异常点列表'
  if (route.path.match(/\/report$/)) return '报告生成'
  return null
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-header { background: #fff; display: flex; align-items: center; justify-content: space-between; padding: 0 24px; height: 56px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.header-right { display: flex; align-items: center; gap: 12px; }
.header-user { display: flex; align-items: center; font-size: 13px; color: #606266; }
.role-tag { font-size: 11px; color: #909399; }
</style>
```

#### Step 3: 重写 App.vue

```vue
<template>
  <router-view v-if="isLoginPage" />
  <el-container v-else class="app-container">
    <AppSidebar :is-collapse="isCollapse" @toggle="isCollapse = !isCollapse" />
    <el-container>
      <AppHeader />
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from './components/layout/AppSidebar.vue'
import AppHeader from './components/layout/AppHeader.vue'

const route = useRoute()
const isCollapse = ref(false)
const isLoginPage = computed(() => route.path === '/login')
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; background: #f0f2f5; }
.app-container { min-height: 100vh; }
.el-menu { border-right: none !important; flex: 1; }
.app-main { padding: 20px; min-height: calc(100vh - 56px); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
```

---

### Task 6: 通用组件

**前置依赖：** Task 3 (composables)

**涉及文件：** `frontend/src/components/common/*.vue` (4 files)

#### Step 1: 创建 StatusTag.vue

```vue
<template>
  <el-tag :type="statusType(status)" size="small" effect="plain">
    {{ statusLabel(status) }}
  </el-tag>
</template>

<script setup>
import { useStatus } from '../../composables/useStatus'

defineProps({ status: { type: String, required: true } })
const { statusLabel, statusType } = useStatus()
</script>
```

#### Step 2: 创建 IndicatorSelect.vue

```vue
<template>
  <el-select :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" :placeholder="placeholder" :size="size">
    <el-option v-for="opt in INDICATOR_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
  </el-select>
</template>

<script setup>
import { useIndicator } from '../../composables/useIndicator'

defineProps({ modelValue: String, placeholder: { type: String, default: '选择指标' }, size: { type: String, default: 'default' } })
defineEmits(['update:modelValue'])
const { INDICATOR_OPTIONS } = useIndicator()
</script>
```

#### Step 3: 创建 LoadingOverlay.vue

```vue
<template>
  <div v-if="visible" class="loading-overlay">
    <el-icon class="loading-icon" :size="32"><Loading /></el-icon>
    <p v-if="text" class="loading-text">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({ visible: Boolean, text: { type: String, default: '' } })
</script>

<style scoped>
.loading-overlay { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 0; }
.loading-icon { animation: rotating 1.5s linear infinite; color: #409eff; }
.loading-text { margin-top: 12px; color: #909399; font-size: 14px; }
@keyframes rotating { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
```

#### Step 4: 创建 EmptyState.vue

```vue
<template>
  <div class="empty-state">
    <el-icon :size="48" color="#dcdfe6"><FolderDelete /></el-icon>
    <p>{{ text || '暂无数据' }}</p>
  </div>
</template>

<script setup>
defineProps({ text: { type: String, default: '' } })
</script>

<style scoped>
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 0; color: #909399; font-size: 14px; gap: 12px; }
</style>
```

---

### Task 7: 可视化组件

**前置依赖：** 无

**涉及文件：**
- 创建: `frontend/src/components/visualization/ContourPanel.vue`
- 创建: `frontend/src/components/visualization/PointCloudFrame.vue`
- 创建: `frontend/src/components/visualization/DepthProfilePanel.vue`

#### Step 1: 创建 ContourPanel.vue

```vue
<template>
  <div class="contour-panel">
    <div class="panel-header">
      <IndicatorSelect v-model="indicator" size="small" />
      <el-select v-if="depths?.length" v-model="selectedDepth" size="small" placeholder="选择深度" style="width:140px">
        <el-option v-for="d in depths" :key="d" :label="`${d}m`" :value="d" />
      </el-select>
      <el-button size="small" @click="refresh"><el-icon><Refresh /></el-icon></el-button>
      <el-button size="small" @click="toggleFullscreen"><el-icon><FullScreen /></el-icon></el-button>
    </div>
    <div ref="containerRef" class="iframe-container" :class="{ fullscreen: isFullscreen }">
      <LoadingOverlay v-if="loading" visible text="加载等值线..." />
      <iframe v-show="!loading" :src="iframeUrl" frameborder="0" @load="loading = false" @error="loading = false" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import IndicatorSelect from '../common/IndicatorSelect.vue'
import LoadingOverlay from '../common/LoadingOverlay.vue'

const props = defineProps({
  taskId: { type: String, required: true },
  depths: { type: Array, default: () => [] },
  defaultIndicator: { type: String, default: 'chlorophyll' },
})

const indicator = ref(props.defaultIndicator)
const selectedDepth = ref(props.depths?.[0])
const isFullscreen = ref(false)
const loading = ref(true)
const containerRef = ref(null)

const iframeUrl = computed(() => {
  const depth = selectedDepth.value || ''
  return `/api/task/${props.taskId}/contour_html?indicator=${indicator.value}&depth=${depth}`
})

function refresh() {
  loading.value = true
  const iframe = containerRef.value?.querySelector('iframe')
  if (iframe) iframe.src = iframe.src
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  if (!isFullscreen.value) {
    document.exitFullscreen?.()
  } else {
    containerRef.value?.requestFullscreen?.()
  }
}

watch(isFullscreen, (val) => {
  if (!val) document.exitFullscreen?.()
})

watch(() => props.depths, (d) => {
  if (d?.length && !selectedDepth.value) selectedDepth.value = d[0]
})
</script>

<style scoped>
.contour-panel { display: flex; flex-direction: column; gap: 8px; }
.panel-header { display: flex; gap: 8px; align-items: center; }
.iframe-container { position: relative; width: 100%; height: 500px; border: 1px solid #ebeef5; border-radius: 4px; overflow: hidden; }
.iframe-container.fullscreen { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 9999; background: #fff; }
.iframe-container iframe { width: 100%; height: 100%; }
</style>
```

#### Step 2: 创建 PointCloudFrame.vue

```vue
<template>
  <div class="pointcloud-panel">
    <div class="panel-header">
      <IndicatorSelect v-model="indicator" size="small" />
      <el-button size="small" @click="refresh"><el-icon><Refresh /></el-icon></el-button>
      <el-button size="small" @click="isFullscreen = !isFullscreen"><el-icon><FullScreen /></el-icon></el-button>
    </div>
    <div ref="containerRef" class="iframe-container" :class="{ fullscreen: isFullscreen }">
      <LoadingOverlay v-if="loading" visible text="加载 3D 渲染..." />
      <iframe v-show="!loading" :src="iframeUrl" frameborder="0" @load="loading = false" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import IndicatorSelect from '../common/IndicatorSelect.vue'
import LoadingOverlay from '../common/LoadingOverlay.vue'

const props = defineProps({
  taskId: { type: String, required: true },
  defaultIndicator: { type: String, default: 'chlorophyll' },
})

const indicator = ref(props.defaultIndicator)
const isFullscreen = ref(false)
const loading = ref(true)
const containerRef = ref(null)

const iframeUrl = computed(() => `/3d/${props.taskId}_${indicator.value}.html`)

function refresh() {
  loading.value = true
  const iframe = containerRef.value?.querySelector('iframe')
  if (iframe) iframe.src = iframe.src
}
</script>

<style scoped>
.pointcloud-panel { display: flex; flex-direction: column; gap: 8px; }
.panel-header { display: flex; gap: 8px; align-items: center; }
.iframe-container { position: relative; width: 100%; height: 500px; border: 1px solid #ebeef5; border-radius: 4px; overflow: hidden; }
.iframe-container.fullscreen { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 9999; background: #fff; }
.iframe-container iframe { width: 100%; height: 100%; }
</style>
```

#### Step 3: 创建 DepthProfilePanel.vue

```vue
<template>
  <div class="depth-profile-panel">
    <div class="panel-header">
      <IndicatorSelect v-model="indicator" size="small" />
      <el-button size="small" @click="refresh"><el-icon><Refresh /></el-icon></el-button>
      <el-button size="small" @click="isFullscreen = !isFullscreen"><el-icon><FullScreen /></el-icon></el-button>
    </div>
    <div ref="containerRef" class="iframe-container" :class="{ fullscreen: isFullscreen }">
      <LoadingOverlay v-if="loading" visible text="加载深度剖面..." />
      <iframe v-show="!loading" :src="iframeUrl" frameborder="0" @load="loading = false" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import IndicatorSelect from '../common/IndicatorSelect.vue'
import LoadingOverlay from '../common/LoadingOverlay.vue'

const props = defineProps({
  taskId: { type: String, required: true },
  defaultIndicator: { type: String, default: 'chlorophyll' },
})

const indicator = ref(props.defaultIndicator)
const isFullscreen = ref(false)
const loading = ref(true)
const containerRef = ref(null)

const iframeUrl = computed(() => `/api/task/${props.taskId}/depth_profile_html?indicator=${indicator.value}`)

function refresh() {
  loading.value = true
  const iframe = containerRef.value?.querySelector('iframe')
  if (iframe) iframe.src = iframe.src
}
</script>

<style scoped>
.depth-profile-panel { display: flex; flex-direction: column; gap: 8px; }
.panel-header { display: flex; gap: 8px; align-items: center; }
.iframe-container { position: relative; width: 100%; height: 500px; border: 1px solid #ebeef5; border-radius: 4px; overflow: hidden; }
.iframe-container.fullscreen { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 9999; background: #fff; }
.iframe-container iframe { width: 100%; height: 100%; }
</style>
```

---

### Task 8: 地图组件

**前置依赖：** 无

**涉及文件：**
- 创建: `frontend/src/components/map/SampleMap.vue`
- 创建: `frontend/src/components/map/AnomalyMap.vue`

#### Step 1: 创建 SampleMap.vue

```vue
<template>
  <div class="sample-map">
    <div class="map-controls">
      <IndicatorSelect v-model="indicator" size="small" />
      <el-select v-model="layerType" size="small" style="width:120px">
        <el-option label="街道图" value="road" />
        <el-option label="卫星图" value="satellite" />
        <el-option label="混合图" value="hybrid" />
      </el-select>
      <el-input-number v-if="depths?.length" v-model="depthFilter" :min="Math.min(...depths)" :max="Math.max(...depths)" :step="1" size="small" placeholder="深度过滤" />
    </div>
    <div ref="mapContainer" class="map-container" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { createAmapLayers } from '../../utils/amap'
import { useIndicator } from '../../composables/useIndicator'
import IndicatorSelect from '../common/IndicatorSelect.vue'

const props = defineProps({
  dataPoints: { type: Array, default: () => [] },
  depths: { type: Array, default: () => [] },
})

const { indicatorColor } = useIndicator()
const indicator = ref('chlorophyll')
const layerType = ref('road')
const depthFilter = ref(null)
const mapContainer = ref(null)

let map = null
let markers = []
let layers = null

function initMap() {
  if (!mapContainer.value) return
  map = L.map(mapContainer.value).setView([30.5, 114.3], 10)
  layers = createAmapLayers(L)
  layers.road.addTo(map)
  updateMarkers()
}

function updateMarkers() {
  if (!map) return
  markers.forEach(m => map.removeLayer(m))
  markers = []

  const filtered = depthFilter.value != null
    ? props.dataPoints.filter(p => Math.abs(p.depth_m - depthFilter.value) < 0.5)
    : props.dataPoints

  filtered.forEach(p => {
    const value = p[indicator.value] ?? 0
    const color = indicatorColor(indicator.value)
    const marker = L.circleMarker([p.lat, p.lon], {
      radius: 6, fillColor: color, color: '#fff', weight: 1, fillOpacity: 0.7,
    })
    marker.bindTooltip(`${indicator.value}: ${value.toFixed(2)}<br>深度: ${p.depth_m}m`)
    marker.addTo(map)
    markers.push(marker)
  })
}

watch([indicator, depthFilter], () => updateMarkers())
watch(layerType, (val) => {
  if (!map || !layers) return
  Object.values(layers).forEach(l => map.removeLayer(l))
  layers[val]?.addTo(map)
})

onMounted(initMap)
onUnmounted(() => { map?.remove() })
</script>

<style scoped>
.sample-map { display: flex; flex-direction: column; gap: 8px; }
.map-controls { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.map-container { width: 100%; height: 500px; border: 1px solid #ebeef5; border-radius: 4px; }
</style>
```

#### Step 2: 创建 AnomalyMap.vue

```vue
<template>
  <div class="anomaly-map">
    <div ref="mapContainer" class="map-container" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { createAmapLayers } from '../../utils/amap'

const props = defineProps({
  anomalies: { type: Array, default: () => [] },
})

const mapContainer = ref(null)
let map = null
let markers = []
let layers = null

function getColor(value) {
  return value > 50 ? '#f56c6c' : value > 20 ? '#e6a23c' : '#67c23a'
}

function updateMarkers() {
  if (!map) return
  markers.forEach(m => map.removeLayer(m))
  markers = []

  props.anomalies.forEach(a => {
    const marker = L.circleMarker([a.lat, a.lon], {
      radius: 8, fillColor: getColor(a.value), color: '#fff', weight: 1, fillOpacity: 0.8,
    })
    marker.bindTooltip(`指标: ${a.indicator}<br>值: ${a.value.toFixed(2)}<br>方法: ${a.method}`)
    marker.addTo(map)
    markers.push(marker)
  })
}

onMounted(() => {
  if (!mapContainer.value) return
  map = L.map(mapContainer.value).setView([30.5, 114.3], 10)
  layers = createAmapLayers(L)
  layers.road.addTo(map)
  updateMarkers()
})

onUnmounted(() => { map?.remove() })

watch(() => props.anomalies, () => updateMarkers(), { deep: true })
</script>

<style scoped>
.anomaly-map { width: 100%; }
.map-container { width: 100%; height: 400px; border: 1px solid #ebeef5; border-radius: 4px; }
</style>
```

---

### Task 9: LoginView

**前置依赖：** Task 4 (auth store)

**涉及文件：**
- 重写: `frontend/src/views/LoginView.vue`

参考当前 `LoginView.vue` 的实现，但改为 setup 语法风格。核心逻辑不变：
- login/register 切换
- 表单校验
- 登录后 router.push('/')

```vue
<template>
  <!-- 从现有 LoginView.vue 复制，改为 setup 语法 -->
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const isLogin = ref(true)
const form = ref({ username: '', password: '', confirmPassword: '' })
const loading = ref(false)
const formRef = ref(null)

const rules = {
  username: [{ required: true, min: 2, max: 32, message: '用户名长度 2-32 字符', trigger: 'blur' }],
  password: [{ required: true, min: 6, max: 64, message: '密码长度 6-64 字符', trigger: 'blur' }],
  confirmPassword: [{
    validator: (rule, value, cb) => value === form.value.password ? cb() : cb(new Error('两次密码不一致')),
    trigger: 'blur',
  }],
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate()
  loading.value = true
  try {
    if (isLogin.value) {
      await authStore.login(form.value.username, form.value.password)
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      await authStore.register(form.value.username, form.value.password)
      ElMessage.success('注册成功，请登录')
      isLogin.value = true
    }
  } finally {
    loading.value = false
  }
}
</script>
```

---

### Task 10: DashboardView

**前置依赖：** Task 4 (dashboard store), Task 3 (composables)

**涉及文件：**
- 重写: `frontend/src/views/DashboardView.vue`

核心变更：用 `useDashboardStore` 替代直接调 `api.getDashboardStats`。图表使用 vue-echarts 内联构建（不创建共享 Chart 组件）。

从现有 DashboardView.vue 复制 ECharts 图表构建逻辑（PieChart, BarChart, LineChart 等），但数据源改为 `dashboardStore.stats`。模板结构：

```vue
<template>
  <div class="dashboard">
    <el-row :gutter="16">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <el-card shadow="hover">
          <div class="stat-value">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12"><div ref="statusChartRef" style="height:300px" /></el-col>
      <el-col :span="12"><div ref="anomalyChartRef" style="height:300px" /></el-col>
    </el-row>
    <!-- 趋势图、近期异常列表、任务表格 — 沿用现有布局，数据通过 store -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import * as echarts from 'echarts'

const dashboardStore = useDashboardStore()
const stats = computed(() => dashboardStore.stats || {})
const statusChartRef = ref(null)
const anomalyChartRef = ref(null)
let statusChart = null
let anomalyChart = null

// ... 从现有 DashboardView.vue 复制 ECharts 初始化、更新、resize 逻辑
// 所有数据引用改为 stats.value.xxx
</script>
```

注意：从现有 `DashboardView.vue` 复制 ECharts 图表代码时，将数据源从 `ref` 改为 `stats.value`。保留现有的 30s 轮询逻辑（`setInterval` + visibility 监听）。

---

### Task 11: UploadView

**前置依赖：** Task 4 (task store), Task 3 (composables)

**涉及文件：**
- 重写: `frontend/src/views/UploadView.vue`

核心变更：所有 API 调用通过 `useTaskStore`。FileDrop 组件不再独立，使用 Element Plus 内置的 `el-upload` 拖拽上传替代。

```vue
<template>
  <div class="upload">
    <el-card>
      <template #header>上传 CSV 数据</template>
      <el-upload drag action="/api/upload" :headers="uploadHeaders" :on-success="handleUploadSuccess"
        :on-error="handleUploadError" accept=".csv" :show-file-list="false" :disabled="uploading">
        <el-icon :size="48" color="#409eff"><UploadFilled /></el-icon>
        <div v-if="!uploading">将 CSV 文件拖到此处或<em>点击上传</em></div>
        <div v-else>上传中...</div>
      </el-upload>
      <!-- 任务列表表格：使用 taskStore.taskList 和 taskStore.loading.list -->
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useTaskStore } from '../stores/task'
import { usePolling } from '../composables/usePolling'
import { useStatus } from '../composables/useStatus'
import { ElMessage, ElMessageBox } from 'element-plus'
import StatusTag from '../components/common/StatusTag.vue'

const taskStore = useTaskStore()
const { statusLabel } = useStatus()
const uploading = ref(false)

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})

// 从现有 UploadView.vue 复制任务列表表格、编辑、删除、重处理逻辑
// API 调用替换：
//   api.getTasks() → taskStore.fetchTasks()
//   api.getTaskStatus() → taskStore.pollTaskStatus()
//   api.updateTask() → taskStore.updateTask()
//   api.deleteTask() → taskStore.deleteTask()
//   api.processTask() → taskStore.processTask()
// 轮询用 usePolling() 替代 setInterval

onMounted(() => { taskStore.fetchTasks(1, 10) })
</script>
```

---

### Task 12: TaskListView

**前置依赖：** Task 4 (task store), Task 7 (components)

**涉及文件：**
- 重写: `frontend/src/views/TaskListView.vue`

核心变更：所有 API 通过 `useTaskStore`。使用 `StatusTag` 组件替代内联状态标签。

---

### Task 13: TaskDetailView

**前置依赖：** Task 4 (task store), Task 7 (visualization), Task 8 (map), Task 6 (common)

**涉及文件：**
- 重写: `frontend/src/views/TaskDetailView.vue`

核心变更：6 个 tab — 直接使用以下共享组件：
- 统计 tab：内联 stat cards + histogram dialog
- 采样点 tab：`<SampleMap :dataPoints />`
- 2D 等值线 tab：`<ContourPanel :taskId :depths />`
- 3D 体渲染 tab：`<PointCloudFrame :taskId />`
- 深度剖面 tab：`<DepthProfilePanel :taskId />`
- 原始数据 tab：内联表格

不再需要内联 iframe 逻辑。不再直接调用 api。

```vue
<template>
  <div v-loading="taskStore.loading.detail">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="统计" name="stats">
        <StatCards :statistics="taskStore.statistics" />
      </el-tab-pane>
      <el-tab-pane label="采样点" name="map">
        <SampleMap :data-points="dataPoints" :depths="depths" />
      </el-tab-pane>
      <el-tab-pane label="2D 等值线" name="contour">
        <ContourPanel :task-id="taskId" :depths="depths" />
      </el-tab-pane>
      <el-tab-pane label="3D 体渲染" name="volume">
        <PointCloudFrame :task-id="taskId" />
      </el-tab-pane>
      <el-tab-pane label="深度剖面" name="depth">
        <DepthProfilePanel :task-id="taskId" />
      </el-tab-pane>
      <el-tab-pane label="原始数据" name="raw">
        <RawDataTable :task-id="taskId" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
```

---

### Task 14: AnomalyListView

**前置依赖：** Task 4 (task store / report store), Task 8 (AnomalyMap)

**涉及文件：**
- 创建: `frontend/src/views/AnomalyListView.vue`
- 删除: `frontend/src/views/AnomalyView.vue`

核心变更：用 `AnomalyMap` 组件替代内联 Leaflet 地图。支持两种模式（全局 / 按任务）。

---

### Task 15: CompareView

**前置依赖：** Task 4 (task store)

**涉及文件：**
- 重写: `frontend/src/views/CompareView.vue`

核心变更：通过 `taskStore.fetchStatistics()` / `taskStore.fetchDepthProfile()` 替代直接调 api。

---

### Task 16: ReportView

**前置依赖：** Task 4 (task store, report store), Task 3 (usePolling)

**涉及文件：**
- 重写: `frontend/src/views/ReportView.vue`

核心变更：用 `useReportStore` + `useTaskStore`。用 `usePolling` 替代手动 setInterval。

```vue
<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useTaskStore } from '../stores/task'
import { useReportStore } from '../stores/report'
import { usePolling } from '../composables/usePolling'
import { ElMessage } from 'element-plus'

const route = useRoute()
const taskId = route.params.id
const taskStore = useTaskStore()
const reportStore = useReportStore()

// 轮询任务状态
const taskPolling = usePolling(() => taskStore.pollTaskStatus(taskId), 2000)
// 轮询报告生成状态
const { start: startReportPolling, stop: stopReportPolling, isPolling: reportPolling } = usePolling(async () => {
  const status = await reportStore.fetchReportStatus(taskId)
  return status?.has_report || !status?.generating
}, 2000, 600000)

async function handleGenerate() {
  await reportStore.searchSimilar(taskId)
  await reportStore.generateReport(taskId)
  startReportPolling()
  ElMessage.success('报告生成已启动')
}
</script>
```

---

### Task 17: ReportManageView

**前置依赖：** Task 4 (task store, report store), Task 3 (usePolling)

**涉及文件：**
- 重写: `frontend/src/views/ReportManageView.vue`

核心变更：通过 store 替代直接 api 调用，使用 `usePolling`。

---

### Task 18: UserManageView

**前置依赖：** Task 4 (auth store)

**涉及文件：**
- 重写: `frontend/src/views/UserManageView.vue`

核心变更：通过 `authStore.getUsers()` 等替代直接调 api。当前 auth store 中没有这些方法，需要添加。

补充 auth store 的额外方法：

在 `stores/auth.js` 中增加：
```js
async function getUsers(page = 1, pageSize = 20) {
  return await authApi.getUsers(page, pageSize)
}
async function createUser(data) {
  await authApi.createUser(data)
}
async function updateUser(userId, data) {
  await authApi.updateUser(userId, data)
}
async function deleteUser(userId) {
  await authApi.deleteUser(userId)
}
```

并在 return 中导出：
```js
return { ..., getUsers, createUser, updateUser, deleteUser }
```

---

### Task 19: 修复报告生成超时（后端）

**前置依赖：** 无

**涉及文件：**
- 修改: `app/routers/report.py`

当前问题：`generate_report` 端点是同步/阻塞的，前端需要等 LLM 调用 + 图表生成 + docx 构建完成（可能超过 600s）。

修改方案：改为后台 fire-and-forget，立即返回。

```python
@router.post("/task/{task_id}/generate_report")
async def generate_report(task_id: str, background_tasks: BackgroundTasks, db=Depends(get_db)):
    task = await data_service.get_task(db, task_id)
    if not task:
        raise BusinessException("任务不存在", status_code=404)
    if task.status != "success":
        raise BusinessException("任务未完成，无法生成报告", status_code=400)
    if task.report_phase is not None:
        raise BusinessException("报告正在生成中", status_code=409)

    task.report_phase = "分析数据中"
    await db.commit()

    background_tasks.add_task(generate_report_in_background, task_id)
    return {"status": "started", "message": "报告生成已启动"}
```

需要将当前的同步 `generate` 调用逻辑移到 `generate_report_in_background` 异步函数中。这需要从现有的 `generate_report` 端点中提取生成逻辑。

---

### Task 20: 清理旧文件

**前置依赖：** 所有 views 和 components 已完成

**涉及文件：**
| 文件 | 原因 |
|------|------|
| `frontend/src/components/ContourPanel.vue` | 已迁移到 `visualization/` |
| `frontend/src/components/PointCloudFrame.vue` | 已迁移到 `visualization/` |
| `frontend/src/components/FileDrop.vue` | 功能合入 UploadView |
| `frontend/src/composables/useTask.js` | 已分解为 useIndicator + useStatus + usePolling |
| `frontend/src/views/MapView.vue` | 地图功能已组件化为 SampleMap/AnomalyMap |
| `frontend/src/views/AnomalyView.vue` | 已更名为 AnomalyListView |

---

## 执行顺序

```
Task 1 (vite + router) ─────────────────────┐
Task 2 (api layer) ─────────────────────────┤
Task 3 (composables) ───────────────────────┤
Task 4 (stores) ◄──── depends on Task 2, 3 ─┤
Task 5 (App.vue + layout) ◄── depends on 4  ├── 并行执行
Task 6 (common components) ◄── depends on 3 ┤
Task 7 (visualization) ─────────────────────┤
Task 8 (map components) ────────────────────┘
Task 9-18 (views) ◄──── depends on 4, 5, 6, 7, 8
Task 19 (backend fix) ────────────────────── (可并行)
Task 20 (cleanup) ───── depends on 9-18     (最后)
```

**建议执行方式：**
1. Task 1-4 顺序执行（建立基础设施）
2. Task 5-8 在 Task 1-4 完成后并行执行
3. Task 9-18 在 Task 5-8 完成后并行执行（每次 dispatch 2-3 个 view）
4. Task 19 可随时并行
5. Task 20 最后执行
