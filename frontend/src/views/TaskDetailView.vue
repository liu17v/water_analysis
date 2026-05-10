<template>
  <div class="task-detail">
    <el-page-header @back="$router.back()" content="任务详情" style="margin-bottom:16px" />

    <!-- 任务信息毛玻璃卡片 -->
    <div v-if="task" class="glass-info-card">
      <el-row :gutter="24" align="middle">
        <el-col :span="16">
          <div class="info-grid">
            <div class="info-row">
              <span class="info-label">任务ID</span>
              <span class="info-value mono">{{ task.task_id }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">水库名称</span>
              <span class="info-value">
                <template v-if="editingReservoir">
                  <el-input v-model="editReservoirName" size="small" style="width:160px"
                    @keyup.enter="saveReservoirName" @keyup.escape="editingReservoir = false" />
                  <el-button size="small" type="primary" link @click="saveReservoirName">确定</el-button>
                  <el-button size="small" link @click="editingReservoir = false">取消</el-button>
                </template>
                <template v-else>
                  {{ task.reservoir_name || '未知' }}
                  <el-button size="small" link type="primary" @click="editingReservoir = true; editReservoirName = task.reservoir_name || ''">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                </template>
              </span>
            </div>
            <div class="info-row">
              <span class="info-label">原始文件</span>
              <span class="info-value">{{ task.original_filename || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">状态</span>
              <span class="info-value">
                <el-tag :type="statusType(task.status)" size="small" effect="dark">
                  {{ statusLabel(task.status) }}
                </el-tag>
              </span>
            </div>
            <div class="info-row">
              <span class="info-label">采样点 / 异常点</span>
              <span class="info-value">
                {{ task.total_points }} 点 /
                <span :class="task.anomaly_count > 0 ? 'text-danger' : ''">{{ task.anomaly_count }} 异常</span>
              </span>
            </div>
          </div>
        </el-col>
        <el-col :span="8" class="info-actions-col">
          <el-button v-if="task.status === 'success'" type="primary" @click="$router.push(`/task/${task.task_id}/report`)">
            <el-icon><Document /></el-icon> 生成报告
          </el-button>
          <el-button v-if="task.status === 'success'" @click="$router.push(`/task/${task.task_id}/anomalies`)">
            <el-icon><Download /></el-icon> 导出
          </el-button>
        </el-col>
      </el-row>
      <el-progress v-if="task.status === 'processing'" :percentage="progress" :stroke-width="10" class="info-progress" />
    </div>

    <!-- Processing state -->
    <div v-if="task?.status === 'processing'" class="processing-state">
      <div class="processing-icon">
        <el-icon :size="48" class="is-loading"><Loading /></el-icon>
      </div>
      <p class="processing-text">任务处理中，请稍候...</p>
      <p class="processing-sub">{{ progress }}%</p>
    </div>

    <!-- Tabs (only when success) -->
    <template v-if="task?.status === 'success'">
      <el-tabs v-model="activeTab" class="glass-tabs" @tab-change="onTabChange">

        <el-tab-pane label="统计数据" name="stats">
          <div v-loading="statsLoading" class="tab-content">
            <el-row :gutter="20" class="card-grid-row">
              <el-col :span="12" v-for="item in indicatorStats" :key="item.indicator" class="indicator-col">
                <el-card shadow="hover" class="indicator-card">
                  <template #header>
                    <div class="indicator-header">
                      <span class="indicator-name">{{ item.label }}</span>
                      <div>
                        <el-tag size="small" :type="item.anomaly_count > 0 ? 'danger' : 'success'" style="margin-right:6px">
                          {{ item.anomaly_count > 0 ? `异常 ${item.anomaly_count} 个` : '正常' }}
                        </el-tag>
                        <el-button size="small" text type="primary" @click="showHistogram(item)">分布图</el-button>
                      </div>
                    </div>
                  </template>
                  <el-row :gutter="16">
                    <el-col :span="6"><div class="stat-item"><span class="stat-lbl">均值</span><span class="stat-num">{{ item.mean ?? '-' }}</span></div></el-col>
                    <el-col :span="6"><div class="stat-item"><span class="stat-lbl">标准差</span><span class="stat-num">{{ item.std ?? '-' }}</span></div></el-col>
                    <el-col :span="6"><div class="stat-item"><span class="stat-lbl">最小值</span><span class="stat-num">{{ item.min ?? '-' }}</span></div></el-col>
                    <el-col :span="6"><div class="stat-item"><span class="stat-lbl">最大值</span><span class="stat-num">{{ item.max ?? '-' }}</span></div></el-col>
                  </el-row>
                  <div class="indicator-footer">
                    <span>有效数据 {{ item.count }} 条</span>
                    <span v-if="item.anomaly_rate != null"> · 异常率 <span :class="item.anomaly_rate > 0 ? 'text-danger' : ''">{{ item.anomaly_rate }}%</span></span>
                    <span v-if="item.unit"> · 单位: {{ item.unit }}</span>
                  </div>
                </el-card>
              </el-col>
            </el-row>

            <el-dialog v-model="histoVisible" :title="histoTitle" width="700px" destroy-on-close>
              <v-chart v-if="histoOption" :option="histoOption" autoresize style="height:360px" />
              <div v-if="histoStats" class="histo-summary">
                <el-tag size="small">均值 {{ histoStats.mean }}</el-tag>
                <el-tag size="small" type="warning">中位数 {{ histoStats.median }}</el-tag>
                <el-tag size="small" type="success">P25 {{ histoStats.p25 }}</el-tag>
                <el-tag size="small" type="success">P75 {{ histoStats.p75 }}</el-tag>
                <el-tag size="small" type="danger">异常率 {{ histoStats.anomaly_rate }}%</el-tag>
              </div>
            </el-dialog>
          </div>
        </el-tab-pane>

        <el-tab-pane label="采样点" name="map" lazy>
          <SampleMap :data-points="dataPoints" :depths="depths" />
        </el-tab-pane>

        <el-tab-pane label="2D 等值线" name="contour" lazy>
          <ContourPanel :task-id="taskId" :depths="depths" />
        </el-tab-pane>

        <el-tab-pane label="3D 体渲染" name="volume" lazy>
          <PointCloudFrame :task-id="taskId" />
        </el-tab-pane>

        <el-tab-pane label="深度剖面" name="depth" lazy>
          <DepthProfilePanel :task-id="taskId" />
        </el-tab-pane>

        <el-tab-pane label="原始数据" name="raw">
          <div class="tab-content">
            <div class="raw-toolbar">
              <el-input v-model="rawSearch" placeholder="搜索数据..." clearable style="width:240px" size="small" />
              <el-checkbox v-model="rawSuspiciousOnly" @change="loadRawData">仅显示可疑数据</el-checkbox>
              <el-button size="small" @click="rawColVisible = !rawColVisible">
                <el-icon><Operation /></el-icon> 列设置
              </el-button>
              <el-popover v-model="rawColVisible" trigger="click" placement="bottom-start" :width="260">
                <el-checkbox-group v-model="rawHiddenCols" style="display:flex;flex-direction:column;gap:6px">
                  <el-checkbox v-for="(label, idx) in rawFieldLabels" :key="rawFields[idx]"
                    :label="rawFields[idx]" :value="rawFields[idx]">
                    {{ label }}
                  </el-checkbox>
                </el-checkbox-group>
              </el-popover>
            </div>
            <el-table :data="filteredRawRows" stripe v-loading="rawLoading" max-height="500" size="small">
              <el-table-column v-for="(label, idx) in rawFieldLabels" :key="rawFields[idx]"
                v-show="!rawHiddenCols.includes(rawFields[idx])"
                :prop="rawFields[idx]" :label="label" min-width="100" show-overflow-tooltip>
                <template #default="{ row }">
                  <span :class="{ 'suspicious-cell': row.suspicious && rawFields[idx] !== 'depth_m' }">
                    {{ row[rawFields[idx]] ?? '-' }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
            <el-pagination
              v-if="rawTotal > rawPageSize"
              style="margin-top:12px; justify-content:flex-end"
              layout="total, prev, pager, next"
              :total="rawTotal" :page-size="rawPageSize"
              v-model:current-page="rawPage"
              @current-change="loadRawData"
            />
          </div>
        </el-tab-pane>

      </el-tabs>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { Edit, Loading, Document, Download, Operation } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import { useTaskStore } from '../stores/task'
import { useIndicator } from '../composables/useIndicator'
import { useStatus } from '../composables/useStatus'
import { usePolling } from '../composables/usePolling'
import ContourPanel from '../components/visualization/ContourPanel.vue'
import PointCloudFrame from '../components/visualization/PointCloudFrame.vue'
import DepthProfilePanel from '../components/visualization/DepthProfilePanel.vue'
import SampleMap from '../components/map/SampleMap.vue'

use([BarChart, TitleComponent, TooltipComponent, GridComponent, CanvasRenderer])

const route = useRoute()
const taskId = computed(() => route.params.id)
const taskStore = useTaskStore()
const { INDICATOR_OPTIONS } = useIndicator()
const { statusLabel, statusType } = useStatus()

// ---- Task info ----
const task = computed(() => taskStore.currentTask)
const progress = computed(() => taskStore.currentStatus?.progress ?? 0)

const editingReservoir = ref(false)
const editReservoirName = ref('')

async function saveReservoirName() {
  try {
    await taskStore.updateTask(task.value.task_id, { reservoir_name: editReservoirName.value || '' })
    task.value.reservoir_name = editReservoirName.value
    ElMessage.success('水库名称已更新')
  } catch { ElMessage.error('更新失败') }
  finally { editingReservoir.value = false }
}

// ---- Tabs ----
const activeTab = ref('stats')

// ---- Shared data for child components ----
const depths = ref([])
const dataPoints = ref([])

async function loadDepths() {
  try {
    await taskStore.fetchVisualization(taskId.value, 'chlorophyll', 1)
    depths.value = taskStore.visualization?.depths || []
  } catch { /* ignore */ }
}

async function loadDataPoints() {
  try {
    await taskStore.fetchRawData(taskId.value, 1, 9999)
    dataPoints.value = (taskStore.rawData.items || []).filter(p => p.lon != null && p.lat != null)
  } catch { /* ignore */ }
}

// ---- Polling ----
const { start: startPolling, stop: stopPolling } = usePolling(async () => {
  const done = await taskStore.pollTaskStatus(taskId.value)
  if (done) {
    await Promise.all([
      taskStore.fetchTaskDetail(taskId.value),
      loadDepths(),
      loadDataPoints(),
    ])
    return true
  }
  return false
}, 2000)

// ---- Statistics ----
const indicatorStats = ref([])
const statsLoading = computed(() => taskStore.loading.stats)

async function loadStatistics() {
  await taskStore.fetchStatistics(taskId.value)
  const stats = taskStore.statistics
  indicatorStats.value = stats?.indicators ? Object.values(stats.indicators) : []
}

// ---- Histogram ----
const histoVisible = ref(false)
const histoTitle = ref('')
const histoOption = ref(null)
const histoStats = ref(null)

async function showHistogram(item) {
  histoTitle.value = `${item.label} 分布直方图`
  histoVisible.value = true
  histoOption.value = null
  try {
    await taskStore.fetchDistribution(taskId.value, item.indicator, 30)
    const res = taskStore.distribution
    if (!res) return
    const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
    const color = colors[Math.floor(Math.random() * colors.length)]
    histoOption.value = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: p => `范围: ${p[0].name}<br/>频次: ${p[0].value}`,
      },
      grid: { left: 50, right: 20, top: 10, bottom: 40 },
      xAxis: {
        type: 'category',
        data: res.bins.map(b => String(b)),
        axisLabel: { rotate: 45, fontSize: 10 },
      },
      yAxis: { type: 'value', name: '频次' },
      series: [{
        type: 'bar',
        data: res.counts,
        itemStyle: { color, borderRadius: [4, 4, 0, 0] },
      }],
    }
    const flat = []
    res.bins.forEach((b, i) => {
      for (let j = 0; j < (res.counts[i] || 0); j++) flat.push(Number(b))
    })
    flat.sort((a, b) => a - b)
    const percentile = (arr, q) => arr.length ? arr[Math.floor(q * (arr.length - 1))].toFixed(4) : '-'
    const anom = indicatorStats.value.find(s => s.indicator === item.indicator)
    histoStats.value = {
      mean: flat.length ? (flat.reduce((a, b) => a + b, 0) / flat.length).toFixed(4) : '-',
      median: percentile(flat, 0.5),
      p25: percentile(flat, 0.25),
      p75: percentile(flat, 0.75),
      anomaly_rate: anom?.anomaly_rate ?? 0,
    }
  } catch { /* ignore */ }
}

// ---- Raw data ----
const rawRows = ref([])
const rawFields = ref([])
const rawFieldLabels = ref([])
const rawTotal = ref(0)
const rawPage = ref(1)
const rawPageSize = ref(50)
const rawLoading = computed(() => taskStore.loading.rawData)
const rawSearch = ref('')
const rawSuspiciousOnly = ref(false)
const rawHiddenCols = ref([])
const rawColVisible = ref(false)

const filteredRawRows = computed(() => {
  let rows = rawRows.value
  if (rawSuspiciousOnly.value) rows = rows.filter(r => r.suspicious)
  if (rawSearch.value) {
    const q = rawSearch.value.toLowerCase()
    rows = rows.filter(r => Object.values(r).some(v => String(v ?? '').toLowerCase().includes(q)))
  }
  return rows
})

async function loadRawData() {
  await taskStore.fetchRawData(taskId.value, rawPage.value, rawPageSize.value)
  const rd = taskStore.rawData
  rawRows.value = rd.items || []
  rawFields.value = rd.fields || []
  rawFieldLabels.value = rd.field_labels || []
  rawTotal.value = rd.total || 0
}

// ---- Tab change handler ----
function onTabChange(name) {
  if (name === 'stats') loadStatistics()
  else if (name === 'map') loadDataPoints()
  else if (name === 'raw') loadRawData()
}

// ---- Lifecycle ----
onMounted(async () => {
  await taskStore.fetchTaskDetail(taskId.value)
  if (task.value?.status === 'processing') {
    startPolling()
  } else if (task.value?.status === 'success') {
    loadStatistics() // 加载统计数据
    await Promise.all([
      loadDepths(),
      loadDataPoints(),
    ])
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.task-detail { max-width: 1400px; margin: 0 auto; }

/* ── 玻璃信息卡片 ── */
.glass-info-card {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur-sm));
  -webkit-backdrop-filter: blur(var(--glass-blur-sm));
  border: var(--glass-border-light);
  border-radius: var(--glass-radius-sm);
  padding: 20px 24px;
  box-shadow: var(--glass-shadow);
  margin-bottom: var(--section-gap);
  animation: glassFadeInUp 0.3s ease;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
}

.info-label {
  color: var(--text-secondary);
  min-width: 100px;
  flex-shrink: 0;
  font-weight: 500;
}

.info-value {
  color: var(--text-primary);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.info-value.mono {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 12px;
  word-break: break-all;
}

.text-danger { color: #f56c6c; font-weight: 600; }

.info-actions-col {
  text-align: right;
  white-space: nowrap;
}
.info-actions-col :deep(.el-button) {
  white-space: nowrap;
}

.info-progress {
  margin-top: 16px;
}

/* ── 处理中状态 ── */
.processing-state {
  text-align: center;
  margin: 80px 0;
  animation: glassFadeInUp 0.4s ease;
}

.processing-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(12px);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}

.processing-text {
  font-size: 16px;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.processing-sub {
  font-size: 24px;
  font-weight: 700;
  color: var(--primary);
}

/* ── 毛玻璃标签页 ── */
.glass-tabs {
  margin-top: 16px;
}

.glass-tabs :deep(.el-tabs__header) {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur-sm));
  -webkit-backdrop-filter: blur(var(--glass-blur-sm));
  border: var(--glass-border-light);
  border-radius: var(--glass-radius-sm) var(--glass-radius-sm) 0 0;
  padding: 8px 16px 0;
  margin-bottom: 0;
  box-shadow: var(--glass-shadow);
}

.glass-tabs :deep(.el-tabs__content) {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur-sm));
  -webkit-backdrop-filter: blur(var(--glass-blur-sm));
  border: var(--glass-border-light);
  border-top: none;
  border-radius: 0 0 var(--glass-radius-sm) var(--glass-radius-sm);
  padding: 20px;
  box-shadow: var(--glass-shadow);
}

.glass-tabs :deep(.el-tabs__item) {
  font-size: 13px;
  padding: 0 16px;
  height: 40px;
  line-height: 40px;
  border-radius: 12px 12px 0 0;
  transition: var(--transition-fast);
}

.glass-tabs :deep(.el-tabs__item.is-active) {
  color: var(--primary);
  background: rgba(255, 255, 255, 0.5);
}

.glass-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 2px;
  background: var(--primary);
}

.glass-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

/* ── 统计数据 ── */
.tab-content { padding: 4px 0; }

.indicator-col { margin-bottom: 0; }
.indicator-card { margin-bottom: 4px; }
.indicator-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.indicator-name { font-weight: 600; font-size: 15px; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.stat-item { text-align: center; padding: 8px 4px; min-width: 0; }
.stat-lbl { display: block; font-size: 11px; color: var(--text-secondary); }
.stat-num { display: block; font-size: 18px; font-weight: 700; color: var(--text-primary); margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.indicator-footer { margin-top: 8px; font-size: 12px; color: var(--text-secondary); padding-top: 8px; border-top: 1px solid rgba(0,0,0,0.04); }

.histo-summary { display: flex; gap: 8px; margin-top: 12px; justify-content: center; flex-wrap: wrap; }

/* ── 原始数据 ── */
.raw-toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.raw-toolbar .el-checkbox { white-space: nowrap; }
.suspicious-cell { color: #f56c6c; font-weight: 600; }

@media (max-width: 900px) {
  .indicator-col { width: 100%; }
  .info-actions-col { width: 100%; text-align: left; margin-top: 8px; }
  .glass-info-card .el-row { flex-direction: column; }
}
</style>
