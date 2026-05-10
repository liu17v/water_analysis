<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-skeleton :loading="loading" animated>
      <template #template>
        <el-row :gutter="24" class="card-grid-row">
          <el-col :span="6" v-for="i in 4" :key="i">
            <el-card shadow="hover"><el-skeleton-item variant="text" style="width:60%;height:28px" /><el-skeleton-item variant="text" style="width:30%;height:20px;margin-top:8px" /></el-card>
          </el-col>
        </el-row>
      </template>
      <el-row :gutter="24" class="card-grid-row">
        <el-col :span="6" v-for="card in statCards" :key="card.label">
          <el-card shadow="hover" class="stat-card glass-fade-in" @click="card.onClick">
            <div class="stat-icon" :style="{background:card.bg + '88'}">
              <el-icon :size="28" :color="card.color"><component :is="card.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value" :style="{color:card.color}">{{ card.value }}</div>
              <div class="stat-label">{{ card.label }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-skeleton>

    <!-- 图表区 -->
    <el-skeleton :loading="loading" animated class="section-gap">
      <template #template>
        <el-row :gutter="24" class="card-grid-row">
          <el-col :span="8" v-for="i in 3" :key="i">
            <el-card><el-skeleton-item variant="rect" style="height:260px" /></el-card>
          </el-col>
        </el-row>
      </template>
      <el-row :gutter="24" class="card-grid-row">
        <el-col :span="8">
          <el-card header="任务状态分布" shadow="hover">
            <v-chart :option="statusPieOption" autoresize style="height:260px" />
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card header="异常指标分布" shadow="hover">
            <v-chart v-if="anomalyBarOption" :option="anomalyBarOption" autoresize style="height:260px" />
            <el-empty v-else description="暂无异常数据" :image-size="60" />
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card header="任务处理趋势" shadow="hover">
            <v-chart :option="trendLineOption" autoresize style="height:260px" />
          </el-card>
        </el-col>
      </el-row>
    </el-skeleton>

    <!-- 第二行 -->
    <el-skeleton :loading="loading" animated class="section-gap">
      <template #template>
        <el-row :gutter="24" class="card-grid-row">
          <el-col :span="12" v-for="i in 2" :key="i">
            <el-card><el-skeleton-item variant="rect" style="height:240px" /></el-card>
          </el-col>
        </el-row>
      </template>
      <el-row :gutter="24" class="card-grid-row">
        <el-col :span="12">
          <el-card header="成功/异常对比" shadow="hover">
            <v-chart :option="successCompareOption" autoresize style="height:240px" />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card header="近期异常预警" shadow="hover">
            <div v-if="(stats.recent_anomalies || []).length" class="anomaly-feed">
              <div v-for="(a, i) in stats.recent_anomalies" :key="i" class="anomaly-item">
                <el-tag :type="a.method === 'threshold' ? 'danger' : 'warning'" size="small" effect="dark">
                  {{ a.method === 'threshold' ? '阈值' : '森林' }}
                </el-tag>
                <span class="anomaly-ind">{{ shortLabel(a.indicator) }}</span>
                <span class="anomaly-val">值: {{ a.value }}</span>
                <span class="anomaly-depth">深度: {{ a.depth }}m</span>
                <el-button size="small" text type="primary" @click="$router.push(`/task/${a.task_id}`)">
                  {{ a.task_id?.substring(0, 8) }}...
                </el-button>
              </div>
            </div>
            <el-empty v-else description="暂无异常" :image-size="60" />
          </el-card>
        </el-col>
      </el-row>
    </el-skeleton>

    <!-- 最近任务 -->
    <el-skeleton :loading="loading" animated>
      <template #template>
        <el-card>
          <el-skeleton-item variant="text" style="width:30%;height:24px;margin-bottom:12px" />
          <el-skeleton-item v-for="i in 5" :key="i" variant="text" style="height:20px;margin-bottom:8px" />
        </el-card>
      </template>
      <el-card header="最近任务" shadow="hover">
        <template #extra>
          <el-button text type="primary" @click="$router.push('/tasks')">查看全部 →</el-button>
        </template>
        <el-table :data="taskStore.taskList" stripe size="small" empty-text="暂无任务，请先上传数据">
        <el-table-column prop="task_id" label="任务ID" min-width="200" show-overflow-tooltip />
        <el-table-column prop="reservoir_name" label="水库名称" min-width="120" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <StatusTag :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="total_points" label="采样点" width="80" sortable />
        <el-table-column prop="anomaly_count" label="异常点" width="80" sortable />
        <el-table-column prop="created_at" label="创建时间" width="170" sortable />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'success'">
              <el-button size="small" link type="primary" @click="$router.push(`/task/${row.task_id}`)">详情</el-button>
              <el-button size="small" link type="warning" @click="$router.push(`/task/${row.task_id}/anomalies`)">异常</el-button>
              <el-button size="small" link type="info" @click="$router.push(`/task/${row.task_id}/report`)">报告</el-button>
            </template>
            <el-button v-else-if="row.status === 'processing'" size="small" link type="warning"
              @click="$router.push(`/task/${row.task_id}`)">查看进度</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    </el-skeleton>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { List, CircleCheck, Loading, WarningFilled, TrendCharts } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart, BarChart, LineChart, GaugeChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([PieChart, BarChart, LineChart, GaugeChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

import { useDashboardStore } from '../stores/dashboard'
import { useTaskStore } from '../stores/task'
import { useIndicator } from '../composables/useIndicator'
import StatusTag from '../components/common/StatusTag.vue'

const dashboardStore = useDashboardStore()
const taskStore = useTaskStore()
const router = useRouter()

const { shortLabel } = useIndicator()

const loading = computed(() => dashboardStore.loading)
const stats = computed(() => dashboardStore.stats || {})

let pollTimer = null

const statCards = computed(() => [
  { label: '总任务数', value: stats.value.total_tasks || 0, icon: List, color: '#409eff', bg: '#ecf5ff',
    onClick: () => router.push('/tasks') },
  { label: '已完成', value: (stats.value.status_counts?.success) || 0, icon: CircleCheck, color: '#67c23a', bg: '#f0f9eb',
    onClick: () => router.push('/tasks') },
  { label: '处理中', value: (stats.value.status_counts?.processing) || 0, icon: Loading, color: '#e6a23c', bg: '#fdf6ec',
    onClick: () => router.push('/tasks') },
  { label: '累计异常点', value: stats.value.total_anomalies || 0, icon: WarningFilled, color: '#f56c6c', bg: '#fef0f0',
    onClick: () => router.push('/anomalies') },
])

const statusPieOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { bottom: 0, textStyle: { fontSize: 12 } },
  series: [{
    type: 'pie', radius: ['50%', '75%'], center: ['50%', '45%'],
    label: { show: false }, emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
    data: [
      { value: stats.value.status_counts?.success || 0, name: '已完成', itemStyle: { color: '#67c23a' } },
      { value: stats.value.status_counts?.processing || 0, name: '处理中', itemStyle: { color: '#e6a23c' } },
      { value: stats.value.status_counts?.pending || 0, name: '待处理', itemStyle: { color: '#909399' } },
      { value: stats.value.status_counts?.failed || 0, name: '失败', itemStyle: { color: '#f56c6c' } },
    ],
  }],
}))

const anomalyBarOption = computed(() => {
  const entries = Object.entries(stats.value.anomaly_by_indicator || {}).filter(([, v]) => v > 0)
  if (!entries.length) return null
  const colors = ['#f56c6c', '#e6a23c', '#409eff', '#67c23a', '#909399']
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 60, right: 30, top: 10, bottom: 20 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: entries.map(([k]) => k), axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar', data: entries.map(([, v], i) => ({ value: v, itemStyle: { color: colors[i % colors.length], borderRadius: [0, 4, 4, 0] } })),
      label: { show: true, position: 'right', fontSize: 11 },
    }],
  }
})

const trendLineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 10, bottom: 20 },
  xAxis: { type: 'category', data: (stats.value.trend_data || []).map(t => t.date), axisLabel: { fontSize: 10, rotate: 30 } },
  yAxis: { type: 'value', minInterval: 1 },
  series: [{
    type: 'line', data: (stats.value.trend_data || []).map(t => t.count),
    smooth: true, lineStyle: { color: '#409eff', width: 2 },
    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
      colorStops: [{ offset: 0, color: 'rgba(64,158,255,0.25)' }, { offset: 1, color: 'rgba(64,158,255,0.02)' }] } },
    itemStyle: { color: '#409eff' },
  }],
}))

const successCompareOption = computed(() => {
  const sc = stats.value.status_counts?.success || 0
  const fc = stats.value.status_counts?.failed || 0
  const total = (sc + fc) || 1
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 20, bottom: 10 },
    xAxis: { type: 'category', data: ['成功', '失败'] },
    yAxis: { type: 'value' },
    series: [
      { type: 'bar', name: '数量', data: [
        { value: sc, itemStyle: { color: '#67c23a', borderRadius: [4, 4, 0, 0] } },
        { value: fc, itemStyle: { color: '#f56c6c', borderRadius: [4, 4, 0, 0] } },
      ], barWidth: '50%' },
    ],
  }
})

async function loadData() {
  try {
    await dashboardStore.fetchStats()
    const s = dashboardStore.stats
    if (s && (!s.trend_data || !s.trend_data.length)) {
      await taskStore.fetchTasks(1, 100)
      if (!s.total_tasks) {
        const items = taskStore.taskList || []
        const counts = { success: 0, processing: 0, pending: 0, failed: 0 }
        items.forEach(t => { if (counts[t.status] !== undefined) counts[t.status]++ })
        s.total_tasks = items.length
        s.status_counts = counts
        s.total_anomalies = items.reduce((sum, t) => sum + (t.anomaly_count || 0), 0)
        s.success_rate = s.total_tasks ? Math.round(counts.success / s.total_tasks * 100) : 0
      }
    }
  } catch { /* ignore */ }
}

let visibilityHandler = null
onMounted(() => {
  loadData()
  pollTimer = setInterval(loadData, 30000)
  visibilityHandler = () => {
    if (document.hidden) {
      clearInterval(pollTimer)
      pollTimer = null
    } else if (!pollTimer) {
      loadData()
      pollTimer = setInterval(loadData, 30000)
    }
  }
  document.addEventListener('visibilitychange', visibilityHandler)
})
onUnmounted(() => {
  clearInterval(pollTimer)
  if (visibilityHandler) document.removeEventListener('visibilitychange', visibilityHandler)
})
</script>

<style scoped>
.dashboard { max-width: 1500px; margin: 0 auto; padding: 0; }

.stat-card { cursor: pointer; transition: transform 0.25s ease, box-shadow 0.25s ease; }
.stat-card:active { transform: translateY(-1px); }
.stat-card :deep(.el-card__body) {
  display: flex; align-items: center; gap: 16px; padding: 18px var(--card-padding) !important;
}
.stat-icon {
  width: 52px; height: 52px; border-radius: 16px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.stat-value { font-size: 26px; font-weight: 700; line-height: 1.2; }
.stat-label { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }

.anomaly-feed { display: flex; flex-direction: column; gap: 8px; max-height: 220px; overflow-y: auto; }
.anomaly-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 14px;
  background: rgba(255, 255, 255, 0.4); border-radius: 12px; font-size: 13px;
  transition: background 0.2s;
}
.anomaly-item:hover { background: rgba(255, 255, 255, 0.6); }
.anomaly-ind { font-weight: 600; color: var(--text-primary); min-width: 48px; }
.anomaly-val { color: #f56c6c; }
.anomaly-depth { color: var(--text-secondary); }

@media (max-width: 1200px) {
  .dashboard :deep(.el-col-6) { width: 50%; margin-bottom: 8px; }
}
@media (max-width: 768px) {
  .dashboard :deep(.el-col-6) { width: 100%; }
  .dashboard :deep(.el-col-8) { width: 100%; }
  .dashboard :deep(.el-col-12) { width: 100%; }
}
</style>
