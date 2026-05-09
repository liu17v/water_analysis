# Frontend Complete Rewrite Design

## Overview

Complete rewrite of the water-analysis frontend based on the existing 29 API endpoints.
Current frontend is discarded; rebuilt from scratch on Vue 3 + Element Plus with clean architecture.

## Tech Stack (unchanged)

| Layer | Choice |
|-------|--------|
| Framework | Vue 3 (Composition API + `<script setup>`) |
| Build | Vite 5 |
| UI Library | Element Plus |
| Charts | ECharts + vue-echarts |
| Maps | Leaflet + Amap tiles |
| State | Pinia |
| HTTP | Axios |
| Router | Vue Router 4 (History mode) |
| Language | JavaScript |

## Route Design

History mode, base `/ui/`. Vite `base: '/ui/'`.

| Path | Name | View | Notes |
|------|------|------|-------|
| `/ui/login` | Login | LoginView | No chrome |
| `/ui/` | Dashboard | DashboardView | Home |
| `/ui/upload` | Upload | UploadView | CSV upload |
| `/ui/tasks` | TaskList | TaskListView | Task list |
| `/ui/task/:id` | TaskDetail | TaskDetailView | Multi-tab detail |
| `/ui/task/:id/anomalies` | TaskAnomalies | AnomalyListView | Per-task anomalies |
| `/ui/task/:id/report` | TaskReport | ReportView | Report generation |
| `/ui/anomalies` | Anomalies | AnomalyListView | Global anomaly management |
| `/ui/compare` | Compare | CompareView | Dual-task comparison |
| `/ui/reports` | ReportManage | ReportManageView | Report management |
| `/ui/users` | UserManage | UserManageView | Admin only |

**Guards:**
- `beforeEach`: all routes except `/ui/login` require token; redirect to login if missing
- `/ui/users`: `meta.requiresAdmin` + store role check
- Logged-in users hitting `/ui/login` redirect to `/ui/`

**Backend sync:** `main.py` static mount path must align with the Vite base change.

## Directory Structure

```
frontend/src/
├── App.vue
├── main.js
├── api/
│   ├── index.js
│   ├── client.js            # Axios instance + interceptors
│   ├── auth.js
│   ├── dashboard.js
│   ├── task.js
│   ├── anomaly.js
│   └── report.js
├── stores/
│   ├── auth.js              # user, token, login/register/logout
│   ├── task.js              # taskList, currentTask, status polling, statistics, visualization, rawData, depthProfile
│   ├── dashboard.js         # stats aggregation
│   └── report.js            # reportStatus polling, similarTasks, reportList
├── composables/
│   ├── usePolling.js        # Generic polling: start/stop/isPolling
│   ├── useIndicator.js      # Indicator name/unit/color mapping
│   └── useStatus.js         # Status → label/color mapping
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

## Data Flow: View → Store → API

Views never call `api/*` directly. All data access goes through Pinia stores.

### Stores

**authStore** — `state: user, token` — `actions: login(), register(), fetchUser(), logout()`

**taskStore** — `state: taskList[], total, currentTask, currentStatus, statistics, distribution, visualization, rawData, depthProfile` — `actions: fetchTasks(), fetchTaskDetail(), pollTaskStatus(), fetchStatistics(), fetchVisualization(), fetchRawData()`

**dashboardStore** — `state: stats {}` — `actions: fetchStats()`

**reportStore** — `state: reportStatus, similarTasks[], reportList[]` — `actions: fetchReportStatus(), generateReport(), searchSimilar(), fetchReports(), deleteReport()`

### Async State Pattern

Every store action manages loading/error state internally:

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

Views consume `store.loading.xxx` for skeleton screens and `store.error.xxx` for error banners.
No manual loading/error refs in views.

## Report Timeout Fix

Current: one 600s request. New: async + polling.

1. `POST /api/task/:id/generate_report` → backend returns 202 immediately, starts background generation
2. Frontend polls `GET /api/task/:id/report_status` every 2s
3. Polling stops when `has_report=true` or `generating=false`
4. Backend `generate_report` handler needs minor change: fire-and-forget instead of blocking

## Component Reuse

Visualization components are used by views (not inlined):
- `ContourPanel` → TaskDetailView 2D contour tab
- `PointCloudFrame` → TaskDetailView 3D volume tab
- `DepthProfilePanel` → TaskDetailView depth profile tab
- `SampleMap` → TaskDetailView sample points tab, MapView
- `AnomalyMap` → AnomalyListView

All visualization components include: indicator picker, fullscreen toggle, loading state, error retry, resize handling.

## Error Handling (3 Layers)

1. **Axios interceptor:** 401 → clear token + redirect login; 500 → generic message; network error → connectivity message
2. **Store actions:** try/catch/finally; loading/error state → view reacts
3. **Components:** ElMessage for success/error feedback; confirm dialogs for destructive actions; loading buttons for async ops

Principle: every user action has initiate → pending → success/failure feedback. No silent failures.

## Views ↔ API Mapping

| View | APIs Called (via Store) |
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
