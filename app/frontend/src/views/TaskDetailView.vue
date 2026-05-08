<template>
  <div class="task-detail">
    <el-page-header @back="$router.back()" content="任务详情" style="margin-bottom:16px" />

    <el-card v-if="task" class="info-card">
      <el-row :gutter="16" align="middle">
        <el-col :span="16">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="任务ID" :span="2">{{ task.task_id }}</el-descriptions-item>
            <el-descriptions-item label="水库名称">{{ task.reservoir_name || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="原始文件">{{ task.original_filename || '-' }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusType(task.status)" size="small">{{ statusLabel(task.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="采样点 / 异常点">{{ task.total_points }} / {{ task.anomaly_count }}</el-descriptions-item>
          </el-descriptions>
        </el-col>
        <el-col :span="8" style="text-align:right">
          <el-button-group v-if="task.status === 'success'">
            <el-button size="small" @click="activeTab='anomalies'">
              <el-icon><WarningFilled /></el-icon> 查看异常
            </el-button>
            <el-button size="small" type="success" @click="$router.push(`/task/${task.task_id}/report`)">
              <el-icon><Document /></el-icon> 生成报告
            </el-button>
            <el-button size="small" type="info" @click="$router.push(`/task/${task.task_id}/anomalies`)">
              <el-icon><Download /></el-icon> 导出
            </el-button>
          </el-button-group>
        </el-col>
      </el-row>
      <el-progress v-if="task.status === 'processing'" :percentage="task.progress" :stroke-width="8" style="margin-top:16px" />
    </el-card>

    <div v-if="task?.status === 'processing'" style="text-align:center;margin:60px 0">
      <el-icon :size="48" class="is-loading"><Loading /></el-icon>
      <p style="margin-top:16px;color:#909399">任务处理中，请稍候... ({{ task.progress }}%)</p>
    </div>

    <template v-if="task?.status === 'success'">
      <el-tabs v-model="activeTab" type="border-card" style="margin-top:16px" @tab-change="onTabChange">
        <!-- 数据统计 -->
        <el-tab-pane label="数据统计" name="statistics">
          <div v-loading="statsLoading" class="tab-content">
            <el-row :gutter="16">
              <el-col :span="12" v-for="item in indicatorStats" :key="item.indicator" style="margin-bottom:12px">
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
                  <el-row :gutter="12">
                    <el-col :span="6"><div class="stat-item"><span class="stat-lbl">均值</span><span class="stat-num">{{ item.mean ?? '-' }}</span></div></el-col>
                    <el-col :span="6"><div class="stat-item"><span class="stat-lbl">标准差</span><span class="stat-num">{{ item.std ?? '-' }}</span></div></el-col>
                    <el-col :span="6"><div class="stat-item"><span class="stat-lbl">最小值</span><span class="stat-num">{{ item.min ?? '-' }}</span></div></el-col>
                    <el-col :span="6"><div class="stat-item"><span class="stat-lbl">最大值</span><span class="stat-num">{{ item.max ?? '-' }}</span></div></el-col>
                  </el-row>
                  <div class="indicator-footer">
                    <span>有效数据 {{ item.count }} 条</span>
                    <span> | 异常率 {{ item.anomaly_rate }}%</span>
                    <span v-if="item.unit"> | 单位: {{ item.unit }}</span>
                  </div>
                </el-card>
              </el-col>
            </el-row>

            <!-- Distribution histogram dialog -->
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

        <!-- 采样点地图 -->
        <el-tab-pane label="采样点地图" name="map">
          <div class="map-tab">
            <div class="viz-controls">
              <span class="ctrl-label">着色指标</span>
              <el-select v-model="mapIndicator" @change="onMapIndicatorChange" style="width:180px">
                <el-option v-for="o in indicatorOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
              <span class="ctrl-label">深度</span>
              <el-select v-model="mapDepth" @change="onMapDepthChange" style="width:140px">
                <el-option v-for="d in mapDepthList" :key="d" :label="d + 'm'" :value="d" />
              </el-select>
              <el-radio-group v-model="amapLayer" size="small" @change="switchAmapLayer" style="margin-left:8px">
                <el-radio-button value="road">街道</el-radio-button>
                <el-radio-button value="satellite">卫星</el-radio-button>
                <el-radio-button value="hybrid">混合</el-radio-button>
              </el-radio-group>
              <el-tag size="small" effect="plain">{{ filteredMapPoints.length }} 个采样点</el-tag>
            </div>
            <div id="leaflet-map" style="width:100%;height:600px;border-radius:0 0 8px 8px"></div>
          </div>
        </el-tab-pane>

        <!-- 2D 等值线图 -->
        <el-tab-pane label="2D 等值线图" name="2d">
          <div class="viz-tab" :class="{ fullscreen: contourFS }">
            <div class="viz-controls">
              <span class="ctrl-label">指标</span>
              <el-select v-model="contourIndicator" @change="reloadContour" style="width:160px">
                <el-option v-for="o in indicatorOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
              <span class="ctrl-label">深度</span>
              <el-slider v-model="contourDepth" :min="minDepth" :max="maxDepth" :step="depthStep"
                show-input :format-tooltip="v => v + 'm'" style="width:220px"
                @change="reloadContour" />
              <el-button @click="contourFS = !contourFS">
                <el-icon><FullScreen /></el-icon> {{ contourFS ? '退出全屏' : '全屏' }}
              </el-button>
            </div>
            <div class="iframe-wrap" :style="{ height: contourFS ? 'calc(100vh - 100px)' : '650px' }">
              <iframe v-if="contourSrc" :key="contourKey" :src="contourSrc"
                frameborder="0" sandbox="allow-scripts allow-same-origin" class="viz-iframe" />
              <el-empty v-else description="加载中等值线图..." :image-size="60" />
            </div>
          </div>
        </el-tab-pane>

        <!-- 3D 体渲染 -->
        <el-tab-pane label="3D 体渲染" name="3d">
          <div class="viz-tab" :class="{ fullscreen: volumeFS }">
            <div class="viz-controls">
              <span class="ctrl-label">指标</span>
              <el-select v-model="volumeIndicator" @change="reloadVolume" style="width:160px">
                <el-option v-for="o in indicatorOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
              <el-button @click="volumeFS = !volumeFS">
                <el-icon><FullScreen /></el-icon> {{ volumeFS ? '退出全屏' : '全屏' }}
              </el-button>
            </div>
            <div class="iframe-wrap" :style="{ height: volumeFS ? 'calc(100vh - 100px)' : '650px' }">
              <iframe v-if="volumeSrc" :key="volumeKey" :src="volumeSrc"
                frameborder="0" sandbox="allow-scripts allow-same-origin" class="viz-iframe" />
              <el-empty v-else description="加载中3D渲染..." :image-size="60" />
            </div>
          </div>
        </el-tab-pane>

        <!-- 深度剖面 -->
        <el-tab-pane label="深度剖面" name="depth">
          <div class="viz-tab">
            <div class="viz-controls">
              <span class="ctrl-label">指标</span>
              <el-select v-model="profileIndicator" @change="reloadProfile" style="width:160px">
                <el-option v-for="o in indicatorOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </div>
            <div class="iframe-wrap">
              <iframe v-if="profileSrc" :key="profileKey" :src="profileSrc"
                frameborder="0" sandbox="allow-scripts allow-same-origin" class="viz-iframe" />
              <el-empty v-else description="加载中深度剖面..." :image-size="60" />
            </div>
          </div>
        </el-tab-pane>

        <!-- 原始数据 -->
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
            <el-table :data="filteredRawRows" stripe v-loading="rawLoading" max-height="500" border size="small">
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
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Loading, WarningFilled, Document, Download, FullScreen, Operation } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { createAmapLayers } from '../utils/amap'
import api from '../api'
import { useTask } from '../composables/useTask'

const { statusLabel, statusType, INDICATOR_OPTIONS: indicatorOptions } = useTask()

use([BarChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

const route = useRoute()
const task = ref(null)
const activeTab = ref('statistics')
const depthList = ref([])
let pollTimer = null
let leafletMap = null
let leafletLayer = null

// 2D Contour
const contourIndicator = ref('chlorophyll')
const contourDepth = ref(1)
const contourKey = ref(0)
const contourFS = ref(false)
const minDepth = computed(() => { const d = depthList.value; return d.length ? Math.min(...d) : 0 })
const maxDepth = computed(() => { const d = depthList.value; return d.length ? Math.max(...d) : 10 })
const depthStep = computed(() => {
  const d = depthList.value
  if (d.length < 2) return 1
  const steps = [...new Set(d.map(v => d.includes(v + 0.5) ? 0.5 : 1))]
  return steps[0] || 1
})
const contourSrc = computed(() => {
  if (!task.value?.task_id) return ''
  return `/api/task/${task.value.task_id}/contour_html?indicator=${contourIndicator.value}&depth=${contourDepth.value}`
})
function reloadContour() { contourKey.value++ }

// 3D Volume
const volumeIndicator = ref('chlorophyll')
const volumeKey = ref(0)
const volumeFS = ref(false)
const volumeSrc = computed(() => {
  if (!task.value?.task_id) return ''
  return `/3d/${task.value.task_id}_${volumeIndicator.value}.html`
})
function reloadVolume() { volumeKey.value++ }

// Depth Profile
const profileIndicator = ref('chlorophyll')
const profileKey = ref(0)
const profileSrc = computed(() => {
  if (!task.value?.task_id) return ''
  return `/api/task/${task.value.task_id}/depth_profile_html?indicator=${profileIndicator.value}`
})
function reloadProfile() { profileKey.value++ }

// Statistics
const statsLoading = ref(false)
const indicatorStats = ref([])

// Histogram
const histoVisible = ref(false)
const histoTitle = ref('')
const histoOption = ref(null)
const histoStats = ref(null)

// Map
const mapIndicator = ref('chlorophyll')
const mapDepth = ref(1)
const mapPoints = ref([])
const mapDepthList = ref([])

const filteredMapPoints = computed(() => {
  return mapPoints.value.filter(p => p.depth_m === mapDepth.value || mapDepthList.value.length <= 1)
})

const amapLayer = ref('road')
let amapLayers = null
let currentTileLayer = null

function switchAmapLayer() {
  if (!leafletMap || !amapLayers) return
  if (currentTileLayer) leafletMap.removeLayer(currentTileLayer)
  currentTileLayer = amapLayers[amapLayer.value]
  currentTileLayer.addTo(leafletMap)
}

function onMapIndicatorChange() { renderMap() }
function onMapDepthChange() { renderMap() }

// Raw data
const rawRows = ref([])
const rawFields = ref([])
const rawFieldLabels = ref([])
const rawTotal = ref(0)
const rawPage = ref(1)
const rawPageSize = ref(50)
const rawLoading = ref(false)
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

async function pollStatus() {
  try {
    const res = await api.getTaskStatus(route.params.id)
    task.value = res
    if (res.status === 'processing') {
      pollTimer = setTimeout(pollStatus, 2000)
    } else {
      clearTimeout(pollTimer)
      if (res.status === 'success') {
        loadDepths()
      }
    }
  } catch { clearTimeout(pollTimer) }
}

async function loadDepths() {
  try {
    const res = await api.getVisualization(route.params.id, 'chlorophyll', 1)
    depthList.value = res.depths || []
    if (depthList.value.length) {
      contourDepth.value = depthList.value[0]
    }
  } catch {}
}

// Statistics
async function loadStatistics() {
  if (indicatorStats.value.length) return
  statsLoading.value = true
  try {
    const res = await api.getStatistics(route.params.id)
    const indicators = res.indicators || {}
    indicatorStats.value = Object.values(indicators)
  } finally { statsLoading.value = false }
}

// Histogram
async function showHistogram(item) {
  histoTitle.value = `${item.label} 分布直方图`
  histoVisible.value = true
  histoOption.value = null
  try {
    const res = await api.getDistribution(route.params.id, item.indicator, 30)
    const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
    const color = colors[Math.floor(Math.random() * colors.length)]
    histoOption.value = {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
        formatter: p => `范围: ${p[0].name}<br/>频次: ${p[0].value}` },
      grid: { left: 50, right: 20, top: 10, bottom: 40 },
      xAxis: { type: 'category', data: res.bins.map(b => String(b)), axisLabel: { rotate: 45, fontSize: 10 } },
      yAxis: { type: 'value', name: '频次' },
      series: [{
        type: 'bar', data: res.counts,
        itemStyle: { color, borderRadius: [4, 4, 0, 0] },
      }],
    }
    // Compute percentiles from raw bins
    const flat = []
    res.bins.forEach((b, i) => { for (let j = 0; j < (res.counts[i] || 0); j++) flat.push(Number(b)) })
    flat.sort((a, b) => a - b)
    const p = (arr, q) => arr.length ? arr[Math.floor(q * (arr.length - 1))].toFixed(4) : '-'
    const anom = indicatorStats.value.find(s => s.indicator === item.indicator)
    histoStats.value = {
      mean: flat.length ? (flat.reduce((a, b) => a + b, 0) / flat.length).toFixed(4) : '-',
      median: p(flat, 0.5), p25: p(flat, 0.25), p75: p(flat, 0.75),
      anomaly_rate: anom?.anomaly_rate ?? 0,
    }
  } catch {}
}

// Map
async function loadMapPoints() {
  try {
    const res = await api.getRawData(route.params.id, 1, 9999)
    mapPoints.value = (res.items || []).filter(p => p.lon != null && p.lat != null)
    const depths = [...new Set(mapPoints.value.map(p => p.depth_m).filter(d => d != null))].sort((a, b) => a - b)
    mapDepthList.value = depths
    if (depths.length) mapDepth.value = depths[0]
    if (activeTab.value === 'map') nextTick(() => renderMap())
  } catch {}
}

function renderMap() {
  const el = document.getElementById('leaflet-map')
  if (!el) return

  if (!leafletMap) {
    leafletMap = L.map(el, { preferCanvas: true }).setView([30, 110], 5)
    amapLayers = createAmapLayers(L)
    currentTileLayer = amapLayers[amapLayer.value]
    currentTileLayer.addTo(leafletMap)
  } else {
    if (leafletLayer) leafletMap.removeLayer(leafletLayer)
    leafletMap.invalidateSize()
  }

  const shortMap = { chlorophyll: 'chlorophyll', dissolved_oxygen: 'dissolved_oxygen', temperature: 'temperature', ph: 'ph', turbidity: 'turbidity' }
  const short = shortMap[mapIndicator.value] || 'chlorophyll'
  const pts = mapPoints.value.filter(p => p.depth_m === mapDepth.value || mapDepthList.value.length <= 1)
  if (!pts.length) return

  const vals = pts.map(p => p[short]).filter(v => v != null)
  if (!vals.length) return
  const vmin = Math.min(...vals)
  const vmax = Math.max(...vals) || 1

  function color(v) {
    if (v == null) return '#999'
    const t = (v - vmin) / (vmax - vmin)
    const r = Math.round(255 * t)
    const b = Math.round(255 * (1 - t))
    return `rgb(${r},80,${b})`
  }

  const markers = pts.map(p => {
    const v = p[short]
    return L.circleMarker([p.lat, p.lon], {
      radius: 6,
      fillColor: color(v),
      color: '#333',
      weight: 1,
      fillOpacity: 0.8,
    }).bindPopup(`<b>${short}</b>: ${v?.toFixed(4) ?? '-'}<br>深度: ${p.depth_m}m<br>坐标: ${p.lon?.toFixed(4)}, ${p.lat?.toFixed(4)}`)
  })

  leafletLayer = L.layerGroup(markers).addTo(leafletMap)
  const bounds = L.latLngBounds(markers.map(m => m.getLatLng()))
  if (bounds.isValid()) leafletMap.fitBounds(bounds, { padding: [30, 30] })
}

// Raw data
async function loadRawData() {
  rawLoading.value = true
  try {
    const res = await api.getRawData(route.params.id, rawPage.value, rawPageSize.value)
    rawRows.value = res.items || []
    rawFields.value = res.fields || []
    rawFieldLabels.value = res.field_labels || []
    rawTotal.value = res.total || 0
  } finally { rawLoading.value = false }
}

function onTabChange(name) {
  if (name === 'statistics') loadStatistics()
  else if (name === 'raw') loadRawData()
  else if (name === 'map') { loadMapPoints() }
}

onMounted(() => pollStatus())
onUnmounted(() => {
  clearTimeout(pollTimer)
  if (leafletMap) { leafletMap.remove(); leafletMap = null }
})
</script>

<style scoped>
.task-detail { max-width: 1400px; margin: 0 auto; padding: 16px; }
.info-card { margin-bottom: 16px; }
.tab-content { padding: 8px 0; }

/* Viz tabs */
.viz-tab { background: #fff; border-radius: 8px; overflow: hidden; }
.viz-tab.fullscreen { position: fixed; inset: 0; z-index: 2000; background: #fff; border-radius: 0; overflow: auto; }
.viz-controls {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 12px 16px; background: #fafafa; border-bottom: 1px solid #ebeef5;
}
.ctrl-label { font-size: 13px; color: #606266; font-weight: 500; }
.iframe-wrap { width: 100%; height: 650px; }
.viz-iframe { width: 100%; height: 100%; border: none; }

/* Map tab */
.map-tab { background: #fff; border-radius: 8px; overflow: hidden; }

/* Indicator cards */
.indicator-card { margin-bottom: 4px; }
.indicator-header { display: flex; justify-content: space-between; align-items: center; }
.indicator-name { font-weight: 600; font-size: 15px; }
.stat-item { text-align: center; padding: 4px 0; }
.stat-lbl { display: block; font-size: 12px; color: #909399; }
.stat-num { display: block; font-size: 16px; font-weight: 600; color: #303133; margin-top: 2px; }
.indicator-footer { margin-top: 10px; font-size: 12px; color: #909399; }

/* Histogram */
.histo-summary { display: flex; gap: 8px; margin-top: 12px; justify-content: center; }

/* Raw data */
.raw-toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.suspicious-cell { color: #f56c6c; font-weight: 600; }
</style>
