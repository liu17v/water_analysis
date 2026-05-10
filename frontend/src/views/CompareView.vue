<template>
  <div class="compare-view">
    <el-page-header @back="$router.push('/tasks')" content="数据对比分析" style="margin-bottom:16px" />

    <!-- Task selectors -->
    <el-card class="section-gap">
      <el-row :gutter="16" align="middle">
        <el-col :span="10">
          <div class="select-label">任务 A</div>
          <el-select v-model="taskAId" filterable placeholder="选择已完成的任务" style="width:100%"
            @change="onTaskAChange" clearable>
            <el-option v-for="t in taskOptions" :key="t.task_id" :value="t.task_id" :disabled="t.task_id === taskBId">
              <div style="display:flex;align-items:center;gap:6px">
                <StatusTag :status="t.status" />
                <span>{{ t.reservoir_name || '未知' }}</span>
                <span style="color:#909399;font-size:12px;margin-left:auto">({{ t.task_id?.substring(0,8) }}...)</span>
              </div>
            </el-option>
          </el-select>
        </el-col>
        <el-col :span="4" style="text-align:center">
          <span class="vs-text">VS</span>
        </el-col>
        <el-col :span="10">
          <div class="select-label">任务 B</div>
          <el-select v-model="taskBId" filterable placeholder="选择已完成的任务" style="width:100%"
            @change="onTaskBChange" clearable>
            <el-option v-for="t in taskOptions" :key="t.task_id" :value="t.task_id" :disabled="t.task_id === taskAId">
              <div style="display:flex;align-items:center;gap:6px">
                <StatusTag :status="t.status" />
                <span>{{ t.reservoir_name || '未知' }}</span>
                <span style="color:#909399;font-size:12px;margin-left:auto">({{ t.task_id?.substring(0,8) }}...)</span>
              </div>
            </el-option>
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <el-empty v-if="!taskAId || !taskBId" description="请选择两个已完成分析的任务进行对比" :image-size="80" />

    <template v-else>
      <!-- Summary cards -->
      <el-row :gutter="20" class="card-grid-row">
        <el-col :span="8" v-for="c in summaryCards" :key="c.label">
          <el-card shadow="hover" class="summary-card">
            <div class="sc-name">{{ c.label }}</div>
            <el-row :gutter="8">
              <el-col :span="10">
                <div class="sc-val" :style="{color:c.colorA}">{{ c.valA }}</div>
                <div class="sc-tag">A</div>
              </el-col>
              <el-col :span="4" style="text-align:center">
                <div class="sc-diff" :style="{color:c.diffColor}">{{ c.diff }}</div>
              </el-col>
              <el-col :span="10">
                <div class="sc-val" :style="{color:c.colorB}">{{ c.valB }}</div>
                <div class="sc-tag" style="text-align:right">B</div>
              </el-col>
            </el-row>
          </el-card>
        </el-col>
      </el-row>

      <!-- Indicator stat comparison -->
      <el-card header="指标统计对比" class="section-gap">
        <el-table :data="indicatorCompare" stripe border size="small">
          <el-table-column prop="label" label="指标" width="120" />
          <el-table-column label="均值 (A)" width="120">
            <template #default="{ row }">{{ row.mean_a ?? '-' }}</template>
          </el-table-column>
          <el-table-column label="均值 (B)" width="120">
            <template #default="{ row }">{{ row.mean_b ?? '-' }}</template>
          </el-table-column>
          <el-table-column label="差异" width="100">
            <template #default="{ row }">
              <span :style="{ color: row.diff_color }">{{ row.diff_pct }}</span>
            </template>
          </el-table-column>
          <el-table-column label="标准差 (A)" width="110">
            <template #default="{ row }">{{ row.std_a ?? '-' }}</template>
          </el-table-column>
          <el-table-column label="标准差 (B)" width="110">
            <template #default="{ row }">{{ row.std_b ?? '-' }}</template>
          </el-table-column>
          <el-table-column label="异常率 (A)" width="100">
            <template #default="{ row }">{{ row.anomaly_a }}%</template>
          </el-table-column>
          <el-table-column label="异常率 (B)" width="100">
            <template #default="{ row }">{{ row.anomaly_b }}%</template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- Charts row -->
      <el-row :gutter="20" class="card-grid-row">
        <el-col :span="12">
          <el-card header="异常点数量对比">
            <v-chart v-if="anomalyBarOption" :option="anomalyBarOption" autoresize style="height:280px" />
            <el-empty v-else description="无异常数据" :image-size="60" />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card header="数据量对比">
            <v-chart v-if="dataBarOption" :option="dataBarOption" autoresize style="height:280px" />
          </el-card>
        </el-col>
      </el-row>

      <!-- Depth profile comparison -->
      <el-card header="深度剖面对比" class="section-gap">
        <div class="viz-controls" style="margin-bottom:12px">
          <span class="ctrl-label">指标</span>
          <el-select v-model="profileIndicator" @change="loadProfileComparison" style="width:180px">
            <el-option v-for="o in INDICATOR_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </div>
        <v-chart v-if="profileOption" :option="profileOption" autoresize style="height:400px" />
        <el-empty v-else description="加载深度剖面数据..." :image-size="60" />
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useTaskStore } from '../stores/task'
import { useIndicator } from '../composables/useIndicator'
import StatusTag from '../components/common/StatusTag.vue'

use([BarChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

const taskStore = useTaskStore()
const { shortLabel, INDICATOR_OPTIONS } = useIndicator()

const taskAId = ref('')
const taskBId = ref('')
const statsA = ref(null)
const statsB = ref(null)
const profileIndicator = ref(INDICATOR_OPTIONS[0].value)

const taskOptions = computed(() =>
  (taskStore.taskList || []).filter(t => t.status === 'success')
)

async function loadTaskList() {
  try {
    await taskStore.fetchTasks(1, 100)
  } catch {}
}

async function onTaskAChange() {
  if (!taskAId.value) { statsA.value = null; return }
  await taskStore.fetchStatistics(taskAId.value)
  statsA.value = taskStore.statistics
  await loadProfileComparison()
}

async function onTaskBChange() {
  if (!taskBId.value) { statsB.value = null; return }
  await taskStore.fetchStatistics(taskBId.value)
  statsB.value = taskStore.statistics
  await loadProfileComparison()
}

const summaryCards = computed(() => {
  const a = statsA.value?.indicators ? Object.values(statsA.value.indicators) : []
  const b = statsB.value?.indicators ? Object.values(statsB.value.indicators) : []
  const ta = statsA.value?.total_anomalies || 0
  const tb = statsB.value?.total_anomalies || 0
  const pa = statsA.value?.total_points || 0
  const pb = statsB.value?.total_points || 0

  const fmtPct = (a, b) => {
    if (b === 0) return a === 0 ? '持平' : '↑100%'
    const d = ((a - b) / b * 100)
    return d > 0 ? `↑${d.toFixed(1)}%` : d < 0 ? `↓${Math.abs(d).toFixed(1)}%` : '持平'
  }
  const diffColor = (a, b) => a > b ? '#f56c6c' : a < b ? '#67c23a' : '#909399'

  return [
    { label: '总异常数', valA: ta, valB: tb, diff: fmtPct(ta, tb),
      colorA: '#f56c6c', colorB: '#f56c6c', diffColor: diffColor(ta, tb) },
    { label: '采样点数', valA: pa, valB: pb, diff: fmtPct(pa, pb),
      colorA: '#409eff', colorB: '#409eff', diffColor: diffColor(pa, pb) },
    { label: '叶绿素均值', valA: a.find(s => s.indicator === 'chlorophyll')?.mean ?? '-',
      valB: b.find(s => s.indicator === 'chlorophyll')?.mean ?? '-',
      diff: fmtPct(a.find(s => s.indicator === 'chlorophyll')?.mean ?? 0, b.find(s => s.indicator === 'chlorophyll')?.mean ?? 0),
      colorA: '#67c23a', colorB: '#67c23a', diffColor: '#e6a23c' },
  ]
})

const indicatorCompare = computed(() => {
  const aInd = statsA.value?.indicators || {}
  const bInd = statsB.value?.indicators || {}
  const keys = [...new Set([...Object.keys(aInd), ...Object.keys(bInd)])]
  return keys.map(k => {
    const ai = aInd[k] || {}
    const bi = bInd[k] || {}
    const diff = (ai.mean != null && bi.mean != null) ? ((ai.mean - bi.mean) / (Math.abs(bi.mean) || 1) * 100) : null
    return {
      label: shortLabel(k),
      mean_a: ai.mean, mean_b: bi.mean,
      std_a: ai.std, std_b: bi.std,
      anomaly_a: ai.anomaly_rate ?? 0, anomaly_b: bi.anomaly_rate ?? 0,
      diff_pct: diff != null ? (diff > 0 ? `↑${diff.toFixed(1)}%` : `↓${Math.abs(diff).toFixed(1)}%`) : '-',
      diff_color: diff != null ? (Math.abs(diff) > 20 ? '#f56c6c' : Math.abs(diff) > 10 ? '#e6a23c' : '#67c23a') : '#909399',
    }
  })
})

const anomalyBarOption = computed(() => {
  const aInd = statsA.value?.indicators || {}
  const bInd = statsB.value?.indicators || {}
  const keys = Object.keys({ ...aInd, ...bInd })
  if (!keys.length) return null
  const colors = ['#409eff', '#67c23a']
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['任务A', '任务B'], bottom: 0 },
    grid: { left: 60, right: 20, top: 10, bottom: 30 },
    xAxis: { type: 'category', data: keys },
    yAxis: { type: 'value', name: '异常数' },
    series: [
      { name: '任务A', type: 'bar', data: keys.map(k => (aInd[k]?.anomaly_count || 0)), itemStyle: { color: colors[0], borderRadius: [4, 4, 0, 0] } },
      { name: '任务B', type: 'bar', data: keys.map(k => (bInd[k]?.anomaly_count || 0)), itemStyle: { color: colors[1], borderRadius: [4, 4, 0, 0] } },
    ],
  }
})

const dataBarOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['任务A', '任务B'], bottom: 0 },
  grid: { left: 60, right: 20, top: 10, bottom: 30 },
  xAxis: { type: 'category', data: ['采样点', '异常点'] },
  yAxis: { type: 'value' },
  series: [
    { name: '任务A', type: 'bar', data: [statsA.value?.total_points || 0, statsA.value?.total_anomalies || 0], itemStyle: { color: '#409eff', borderRadius: [4, 4, 0, 0] } },
    { name: '任务B', type: 'bar', data: [statsB.value?.total_points || 0, statsB.value?.total_anomalies || 0], itemStyle: { color: '#67c23a', borderRadius: [4, 4, 0, 0] } },
  ],
}))

const profileOption = ref(null)

async function loadProfileComparison() {
  if (!taskAId.value || !taskBId.value) return
  try {
    await taskStore.fetchDepthProfile(taskAId.value, profileIndicator.value)
    const pa = taskStore.depthProfile
    await taskStore.fetchDepthProfile(taskBId.value, profileIndicator.value)
    const pb = taskStore.depthProfile
    const depths = [...new Set([...(pa.profile || []).map(p => p.depth), ...(pb.profile || []).map(p => p.depth)])].sort((a, b) => a - b)
    const getMean = (prof, d) => { const p = (prof.profile || []).find(x => x.depth === d); return p?.mean ?? null }
    profileOption.value = {
      tooltip: { trigger: 'axis' },
      legend: {
        data: ['任务A', '任务B'],
        orient: 'horizontal',
        left: 'center',
        top: 'auto',
        bottom: 0,
        icon: 'roundRect',
        itemWidth: 16,
        itemHeight: 4,
      },
      grid: { left: 60, right: 30, top: 20, bottom: 40 },
      xAxis: { type: 'value', name: shortLabel(profileIndicator.value) },
      yAxis: { type: 'category', data: depths, name: '深度(m)', inverse: true },
      series: [
        { name: '任务A', type: 'line', data: depths.map(d => getMean(pa, d)), smooth: true, lineStyle: { color: '#409eff', width: 2 }, itemStyle: { color: '#409eff' } },
        { name: '任务B', type: 'line', data: depths.map(d => getMean(pb, d)), smooth: true, lineStyle: { color: '#67c23a', width: 2 }, itemStyle: { color: '#67c23a' } },
      ],
    }
  } catch {}
}

onMounted(() => {
  loadTaskList()
})
</script>

<style scoped>
.compare-view { max-width: 1500px; margin: 0 auto; }
.select-label { font-size: 13px; color: var(--text-secondary); margin-bottom: 4px; }
.vs-text { font-size: 28px; font-weight: 700; color: var(--text-muted); }

.summary-card { text-align: center; }
.summary-card :deep(.el-card__body) { padding: 16px 12px; }
.sc-name { font-size: 13px; color: var(--text-secondary); margin-bottom: 10px; }
.sc-val { font-size: 22px; font-weight: 700; }
.sc-tag { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.sc-diff { font-size: 14px; font-weight: 600; padding-top: 12px; }

.ctrl-label { font-size: 13px; color: var(--text-primary); font-weight: 500; }
.viz-controls { display: flex; align-items: center; gap: 10px; }

@media (max-width: 900px) {
  .compare-view :deep(.el-col-8) { width: 100%; margin-bottom: 8px; }
}
</style>
