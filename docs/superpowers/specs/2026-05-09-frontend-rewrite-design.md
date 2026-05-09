# 前端完整重建设计

## 概述

基于现有的 29 个 API 端点，对水质分析前端进行完整重写。
废弃当前前端，基于 Vue 3 + Element Plus 从零重构，采用清晰架构。

## 技术栈（不变）

| 层 | 选择 |
|-------|--------|
| 框架 | Vue 3 (Composition API + `<script setup>`) |
| 构建工具 | Vite 5 |
| UI 库 | Element Plus |
| 图表 | ECharts + vue-echarts |
| 地图 | Leaflet + 高德地图瓦片 |
| 状态管理 | Pinia |
| HTTP | Axios |
| 路由 | Vue Router 4 (History 模式) |
| 语言 | JavaScript |

## 路由设计

History 模式，基础路径 `/ui/`。Vite `base: '/ui/'`。

| 路径 | 名称 | 视图 | 备注 |
|------|------|------|-------|
| `/ui/login` | 登录 | LoginView | 无外壳布局 |
| `/ui/` | 仪表盘 | DashboardView | 首页 |
| `/ui/upload` | 上传 | UploadView | CSV 上传 |
| `/ui/tasks` | 任务列表 | TaskListView | 任务列表 |
| `/ui/task/:id` | 任务详情 | TaskDetailView | 多标签详情 |
| `/ui/task/:id/anomalies` | 任务异常 | AnomalyListView | 按任务查看异常 |
| `/ui/task/:id/report` | 任务报告 | ReportView | 报告生成 |
| `/ui/anomalies` | 异常管理 | AnomalyListView | 全局异常管理 |
| `/ui/compare` | 对比 | CompareView | 双任务对比 |
| `/ui/reports` | 报告管理 | ReportManageView | 报告管理 |
| `/ui/users` | 用户管理 | UserManageView | 仅管理员 |

**路由守卫：**
- `beforeEach`：除 `/ui/login` 外所有路由需要 token；缺失则重定向到登录
- `/ui/users`：`meta.requiresAdmin` + store 角色校验
- 已登录用户访问 `/ui/login` 时重定向到 `/ui/`

**后端同步：** `main.py` 静态挂载路径必须与 Vite base 路径保持一致。

## 目录结构

```
frontend/src/
├── App.vue
├── main.js
├── api/
│   ├── index.js
│   ├── client.js            # Axios 实例 + 拦截器
│   ├── auth.js
│   ├── dashboard.js
│   ├── task.js
│   ├── anomaly.js
│   └── report.js
├── stores/
│   ├── auth.js              # 用户、token、登录/注册/退出
│   ├── task.js              # taskList、currentTask、状态轮询、统计、可视化、原始数据、深度剖面
│   ├── dashboard.js         # 统计汇总
│   └── report.js            # 报告状态轮询、相似任务、报告列表
├── composables/
│   ├── usePolling.js        # 通用轮询：开始/停止/是否轮询中
│   ├── useIndicator.js      # 指标名称/单位/颜色映射
│   └── useStatus.js         # 状态 → 标签/颜色映射
├── components/
│   ├── layout/
│   │   ├── AppSidebar.vue
│   │   └── AppHeader.vue
│   ├── common/
│   │   ├── StatusTag.vue
│   │   ├── IndicatorSelect.vue
│   │   ├── LoadingOverlay.vue
│   │   └── EmptyState.vue
│   ├── visualization/
│   │   ├── ContourPanel.vue
│   │   ├── PointCloudFrame.vue
│   │   └── DepthProfilePanel.vue
│   └── map/
│       ├── SampleMap.vue
│       └── AnomalyMap.vue
├── views/
│   ├── LoginView.vue
│   ├── DashboardView.vue
│   ├── UploadView.vue
│   ├── TaskListView.vue
│   ├── TaskDetailView.vue
│   ├── AnomalyListView.vue
│   ├── CompareView.vue
│   ├── ReportView.vue
│   ├── ReportManageView.vue
│   └── UserManageView.vue
└── router/
    └── index.js
```

## 数据流：视图 → Store → API

视图不直接调用 `api/*`。所有数据访问通过 Pinia store 进行。

### Stores

**authStore** — `state: user, token` — `actions: login(), register(), fetchUser(), logout()`

**taskStore** — `state: taskList[], total, currentTask, currentStatus, statistics, distribution, visualization, rawData, depthProfile` — `actions: fetchTasks(), fetchTaskDetail(), pollTaskStatus(), fetchStatistics(), fetchVisualization(), fetchRawData()`

**dashboardStore** — `state: stats {}` — `actions: fetchStats()`

**reportStore** — `state: reportStatus, similarTasks[], reportList[]` — `actions: fetchReportStatus(), generateReport(), searchSimilar(), fetchReports(), deleteReport()`

### 异步状态模式

每个 store action 内部管理 loading/error 状态：

```js
const loading = reactive({ list: false, detail: false })
const error = reactive({ list: null, detail: null })

async function fetchTasks(params) {
  loading.list = true; error.list = null
  try { taskList.value = (await taskApi.getTasks(params)).items }
  catch (e) { error.list = e.message || '加载失败'; throw e }
  finally { loading.list = false }
}
```

视图通过 `store.loading.xxx` 实现骨架屏，通过 `store.error.xxx` 展示错误横幅。
视图中无需手动维护 loading/error ref。

## 报告超时修复

当前：单个 600 秒请求。新方案：异步 + 轮询。

1. `POST /api/task/:id/generate_report` → 后端立即返回 202，开始后台生成
2. 前端每 2 秒轮询 `GET /api/task/:id/report_status`
3. 当 `has_report=true` 或 `generating=false` 时停止轮询
4. 后端 `generate_report` 处理器需做小幅修改：改为 fire-and-forget 而非阻塞

## 组件复用

可视化组件被视图使用（非内联）：
- `ContourPanel` → TaskDetailView 二维等值线标签页
- `PointCloudFrame` → TaskDetailView 三维体渲染标签页
- `DepthProfilePanel` → TaskDetailView 深度剖面标签页
- `SampleMap` → TaskDetailView 采样点标签页、MapView
- `AnomalyMap` → AnomalyListView

所有可视化组件包含：指标选择器、全屏切换、加载状态、错误重试、自适应大小。

## 错误处理（三层）

1. **Axios 拦截器：** 401 → 清除 token + 重定向到登录；500 → 通用提示；网络错误 → 连接异常提示
2. **Store actions：** try/catch/finally；loading/error 状态 → 视图响应
3. **组件：** ElMessage 展示成功/错误反馈；破坏性操作使用确认对话框；异步操作使用加载按钮

原则：每个用户操作都有 发起 → 等待 → 成功/失败 的反馈。不允许静默失败。

## 视图 ↔ API 映射

| 视图 | 调用的 API（通过 Store） |
|------|------------------------|
| LoginView | auth.login, auth.register |
| DashboardView | dashboard.fetchStats |
| UploadView | task.upload, task.fetchTasks, task.updateTask, task.deleteTask, task.processTask, task.pollTaskStatus |
| TaskListView | task.fetchTasks, task.updateTask, task.deleteTask, task.processTask |
| TaskDetailView | task.pollTaskStatus, task.fetchStatistics, task.fetchDistribution, task.fetchRawData, task.fetchVisualization |
| AnomalyListView | anomaly.fetchAnomalies, anomaly.fetchAllAnomalies |
| CompareView | task.fetchTasks, task.fetchStatistics, task.fetchDepthProfile |
| ReportView | task.pollTaskStatus, report.searchSimilar, report.generateReport, report.fetchReportStatus |
| ReportManageView | report.fetchReports, task.fetchTasks, report.generateReport, report.fetchReportStatus, report.deleteReport |
| UserManageView | auth.fetchUsers, auth.createUser, auth.updateUser, auth.deleteUser |