<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom:20px">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" @click="$router.push('/tasks')">
          <div class="stat-icon" style="background:#ecf5ff"><el-icon :size="28" color="#409eff"><List /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalTasks }}</div>
            <div class="stat-label">总任务数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background:#f0f9eb"><el-icon :size="28" color="#67c23a"><CircleCheck /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.successTasks }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background:#fdf6ec"><el-icon :size="28" color="#e6a23c"><Loading /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.processingTasks }}</div>
            <div class="stat-label">处理中</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background:#fef0f0"><el-icon :size="28" color="#f56c6c"><WarningFilled /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalAnomalies }}</div>
            <div class="stat-label">累计异常点</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="20" style="margin-bottom:20px">
      <el-col :span="8">
        <el-card header="任务状态分布">
          <div class="chart-wrap">
            <div class="donut-chart" :style="donutStyle"></div>
            <div class="donut-legend">
              <div v-for="item in donutItems" :key="item.label" class="donut-legend-item">
                <span class="legend-dot" :style="{background:item.color}"></span>
                <span>{{ item.label }} ({{ item.value }})</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="异常指标分布">
          <div class="bar-chart" v-if="anomalyBars.length">
            <div v-for="bar in anomalyBars" :key="bar.label" class="bar-row">
              <span class="bar-label">{{ bar.label }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{width:bar.pct+'%', background:bar.color}"></div>
              </div>
              <span class="bar-val">{{ bar.value }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无异常数据" :image-size="60" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="处理成功率">
          <div class="gauge-wrap">
            <div class="gauge-circle" :style="gaugeStyle">
              <div class="gauge-inner">
                <div class="gauge-rate">{{ successRate }}%</div>
                <div class="gauge-sub">成功率</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近任务 -->
    <el-card header="最近任务">
      <template #extra>
        <el-button text type="primary" @click="$router.push('/tasks')">查看全部</el-button>
      </template>
      <el-table :data="recentTasks" stripe v-loading="loading" empty-text="暂无任务，请先上传数据">
        <el-table-column prop="task_id" label="任务ID" min-width="200" show-overflow-tooltip />
        <el-table-column prop="reservoir_name" label="水库名称" min-width="120" />
        <el-table-column prop="original_filename" label="原始文件" min-width="160" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_points" label="采样点" width="90" />
        <el-table-column prop="anomaly_count" label="异常点" width="90" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'success'">
              <el-button type="primary" size="small" link @click="$router.push(`/task/${row.task_id}`)">详情</el-button>
              <el-button type="success" size="small" link @click="$router.push(`/task/${row.task_id}/anomalies`)">异常</el-button>
              <el-button type="info" size="small" link @click="$router.push(`/task/${row.task_id}/report`)">报告</el-button>
            </template>
            <el-button v-else-if="row.status === 'processing'" type="warning" size="small" link @click="$router.push(`/task/${row.task_id}`)">进度</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { List, CircleCheck, Loading, WarningFilled } from '@element-plus/icons-vue'
import api from '../api'

const loading = ref(false)
const recentTasks = ref([])
const stats = reactive({
  totalTasks: 0, successTasks: 0, processingTasks: 0, totalAnomalies: 0,
  pendingTasks: 0, failedTasks: 0,
})

const anomalyBars = ref([])
const barColors = ['#f56c6c', '#e6a23c', '#409eff', '#67c23a', '#909399']

function statusLabel(s) {
  const map = { pending: '待处理', processing: '处理中', success: '已完成', failed: '失败' }
  return map[s] || s
}
function statusType(s) {
  const map = { success: 'success', processing: 'warning', failed: 'danger', pending: 'info' }
  return map[s] || 'info'
}

const donutItems = computed(() => [
  { label: '已完成', value: stats.successTasks, color: '#67c23a' },
  { label: '处理中', value: stats.processingTasks, color: '#e6a23c' },
  { label: '待处理', value: stats.pendingTasks, color: '#909399' },
  { label: '失败', value: stats.failedTasks, color: '#f56c6c' },
])

const donutTotal = computed(() => donutItems.value.reduce((s, i) => s + i.value, 0) || 1)

const donutStyle = computed(() => {
  const items = donutItems.value
  let acc = 0
  const segs = items.map(item => {
    const pct = (item.value / donutTotal.value) * 100
    const seg = `${item.color} ${acc}% ${acc + pct}%`
    acc += pct
    return seg
  })
  return { background: `conic-gradient(${segs.join(',')})` }
})

const successRate = computed(() => {
  const finished = stats.successTasks + stats.failedTasks
  if (!finished) return 0
  return Math.round((stats.successTasks / finished) * 100)
})

const gaugeStyle = computed(() => ({
  background: `conic-gradient(#67c23a 0% ${successRate.value}%, #ebeef5 ${successRate.value}% 100%)`,
}))

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.getDashboardStats()
    const items = res.items || []
    stats.totalTasks = res.total || items.length
    stats.successTasks = items.filter(t => t.status === 'success').length
    stats.processingTasks = items.filter(t => t.status === 'processing').length
    stats.pendingTasks = items.filter(t => t.status === 'pending').length
    stats.failedTasks = items.filter(t => t.status === 'failed').length
    stats.totalAnomalies = items.reduce((s, t) => s + (t.anomaly_count || 0), 0)
    recentTasks.value = items.slice(0, 10)

    // Aggregate anomaly counts by indicator across recent successful tasks
    const anomalyMap = {}
    for (const t of items) {
      if (t.status === 'success' && t.anomaly_count > 0) {
        try {
          const statsRes = await api.getStatistics(t.task_id)
          const indicators = statsRes.indicators || {}
          for (const [key, val] of Object.entries(indicators)) {
            if (val.anomaly_count > 0) {
              anomalyMap[key] = (anomalyMap[key] || 0) + val.anomaly_count
            }
          }
        } catch {}
      }
    }
    const labelMap = { chlorophyll: '叶绿素', dissolved_oxygen: '溶解氧', temperature: '水温', ph: 'pH', turbidity: '浊度' }
    const totalAnom = Object.values(anomalyMap).reduce((s, v) => s + v, 0) || 1
    anomalyBars.value = Object.entries(anomalyMap)
      .map(([key, val], idx) => ({
        label: labelMap[key] || key,
        value: val,
        pct: Math.round((val / totalAnom) * 100),
        color: barColors[idx % barColors.length],
      }))
      .sort((a, b) => b.value - a.value)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dashboard { max-width: 1400px; margin: 0 auto; }
.stat-card { cursor: pointer; }
.stat-card :deep(.el-card__body) {
  display: flex; align-items: center; gap: 16px; width: 100%;
}
.stat-icon {
  width: 56px; height: 56px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.stat-value { font-size: 28px; font-weight: 700; color: #303133; line-height: 1.2; }
.stat-label { font-size: 13px; color: #909399; margin-top: 2px; }

/* Donut chart */
.chart-wrap { display: flex; align-items: center; gap: 24px; padding: 8px 0; }
.donut-chart {
  width: 110px; height: 110px; border-radius: 50%; flex-shrink: 0;
  position: relative;
}
.donut-chart::after {
  content: ''; position: absolute; top: 28px; left: 28px;
  width: 54px; height: 54px; border-radius: 50%; background: #fff;
}
.donut-legend { display: flex; flex-direction: column; gap: 8px; }
.donut-legend-item { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #606266; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }

/* Bar chart */
.bar-chart { display: flex; flex-direction: column; gap: 12px; padding: 8px 0; }
.bar-row { display: flex; align-items: center; gap: 8px; }
.bar-label { width: 52px; font-size: 12px; color: #606266; text-align: right; flex-shrink: 0; }
.bar-track { flex: 1; height: 18px; background: #f0f2f5; border-radius: 9px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 9px; transition: width 0.6s; min-width: 4px; }
.bar-val { width: 30px; font-size: 12px; color: #909399; text-align: right; flex-shrink: 0; }

/* Gauge */
.gauge-wrap { display: flex; justify-content: center; padding: 8px 0; }
.gauge-circle {
  width: 130px; height: 130px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  position: relative;
}
.gauge-circle::after {
  content: ''; position: absolute; top: 16px; left: 16px;
  width: 98px; height: 98px; border-radius: 50%; background: #fff;
}
.gauge-inner { z-index: 1; text-align: center; }
.gauge-rate { font-size: 32px; font-weight: 700; color: #67c23a; }
.gauge-sub { font-size: 12px; color: #909399; }
</style>
