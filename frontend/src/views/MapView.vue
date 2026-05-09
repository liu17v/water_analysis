<template>
  <div class="map-view">
    <!-- Left sidebar -->
    <div class="map-sidebar">
      <div class="sidebar-header">
        <h3><el-icon><MapLocation /></el-icon> 空间数据地图</h3>
      </div>

      <div class="sidebar-body">
        <el-select v-model="selTaskId" filterable clearable placeholder="全部任务" style="width:100%;margin-bottom:10px" @change="loadData">
          <el-option v-for="t in taskOptions" :key="t.task_id" :label="t.reservoir_name || t.task_id?.substring(0,12)" :value="t.task_id" />
        </el-select>

        <el-select v-model="selIndicator" placeholder="全部指标" clearable style="width:100%;margin-bottom:10px" @change="loadData">
          <el-option v-for="o in indicatorOpts" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>

        <el-radio-group v-model="amapLayer" size="small" @change="switchAmapLayer" style="width:100%;margin-bottom:10px">
          <el-radio-button value="road">街道</el-radio-button>
          <el-radio-button value="satellite">卫星</el-radio-button>
          <el-radio-button value="hybrid">混合</el-radio-button>
        </el-radio-group>

        <div class="sidebar-stats">
          <el-tag type="primary" size="small">采样点 {{ samplePoints.length }}</el-tag>
          <el-tag size="small" type="success">任务 {{ taskOptions.length }}</el-tag>
        </div>

        <el-divider style="margin:10px 0" />

        <div class="sidebar-list">
          <div v-for="(p, i) in displayedPoints.slice(0, 50)" :key="i" class="point-item"
            @click="flyToPoint(p)">
            <el-tag size="small" effect="dark">采样</el-tag>
            <span class="point-name">{{ shortLabel(p.indicator) }}</span>
            <span class="point-val">{{ p.value?.toFixed(2) }}</span>
          </div>
          <el-empty v-if="!displayedPoints.length" description="暂无数据" :image-size="40" />
        </div>
      </div>
    </div>

    <!-- Map area -->
    <div class="map-main" v-loading="mapLoading">
      <div id="map-2d" class="map-container"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { MapLocation } from '@element-plus/icons-vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { createAmapLayers } from '../utils/amap'
import api from '../api'

const indicatorOpts = [
  { label: '叶绿素 (chl)', value: 'chl' },
  { label: '溶解氧 (odo)', value: 'odo' },
  { label: '水温 (temp)', value: 'temp' },
  { label: 'pH', value: 'ph' },
  { label: '浊度 (turb)', value: 'turb' },
]

const labelMap = { chl: '叶绿素', odo: '溶解氧', temp: '水温', ph: 'pH', turb: '浊度' }
function shortLabel(code) { return labelMap[code] || code }

const shortToField = { chl: 'chlorophyll', odo: 'dissolved_oxygen', temp: 'temperature', ph: 'ph', turb: 'turbidity' }

const taskOptions = ref([])
const selTaskId = ref('')
const selIndicator = ref('')
const amapLayer = ref('road')
const anomalyPoints = ref([])
const samplePoints = ref([])
const mapLoading = ref(false)

let leafletMap = null
let amapLayers = null
let currentTileLayer = null
let markersLayer = null

const displayedPoints = computed(() => {
  const pts = [...anomalyPoints.value, ...samplePoints.value]
  if (!selIndicator.value) return pts
  return pts.filter(p => p.indicator === selIndicator.value)
})

async function loadTaskOptions() {
  try {
    const res = await api.getTasks(1, 100)
    taskOptions.value = res.items || []
  } catch {}
}

async function loadData() {
  anomalyPoints.value = []
  samplePoints.value = []
  mapLoading.value = true

  try {
    if (selTaskId.value) {
      const rawData = await api.getRawData(selTaskId.value, 1, 20000)
      const field = shortToField[selIndicator.value] || 'chlorophyll'
      samplePoints.value = (rawData.items || [])
        .filter(r => r.lat != null && r.lon != null)
        .map(r => ({
          lat: r.lat, lon: r.lon, depth: r.depth_m || 0, indicator: selIndicator.value || 'chl',
          value: r[field] ?? 0, _type: 'sample',
        }))
    }
  } catch {} finally {
    mapLoading.value = false
  }

  nextTick(() => renderMap())
}

function switchAmapLayer() {
  if (!leafletMap || !amapLayers) return
  if (currentTileLayer) leafletMap.removeLayer(currentTileLayer)
  currentTileLayer = amapLayers[amapLayer.value]
  currentTileLayer.addTo(leafletMap)
}

function renderMap() {
  const el = document.getElementById('map-2d')
  if (!el) return

  if (!leafletMap) {
    leafletMap = L.map(el, { preferCanvas: true }).setView([32, 115], 5)
    amapLayers = createAmapLayers(L)
    currentTileLayer = amapLayers[amapLayer.value]
    currentTileLayer.addTo(leafletMap)
  } else {
    if (markersLayer) leafletMap.removeLayer(markersLayer)
    leafletMap.invalidateSize()
  }

  const pts = displayedPoints.value.filter(p => p.lat != null && p.lon != null)
  if (pts.length > 3000) { pts.length = 3000 }

  const markers = pts.map(p => {
    return L.circleMarker([p.lat, p.lon], {
      radius: 4,
      fillColor: '#409eff',
      color: '#fff',
      weight: 1,
      fillOpacity: 0.7,
    }).bindPopup(`
      <b>${shortLabel(p.indicator)}</b>: ${p.value?.toFixed(4) ?? '-'}<br>
      深度: ${p.depth ?? '-'}m
    `)
  })

  markersLayer = L.layerGroup(markers).addTo(leafletMap)
  if (markers.length) {
    leafletMap.fitBounds(L.latLngBounds(markers.map(m => m.getLatLng())), { padding: [30, 30] })
  }
}

function flyToPoint(p) {
  if (leafletMap) {
    leafletMap.setView([p.lat, p.lon], 14, { animate: true })
  }
}

onMounted(async () => {
  await loadTaskOptions()
  loadData()
  nextTick(() => renderMap())
})

onUnmounted(() => {
  if (leafletMap) { leafletMap.remove(); leafletMap = null }
})
</script>

<style scoped>
.map-view { display: flex; height: calc(100vh - 110px); gap: 0; }

.map-sidebar {
  width: 260px; flex-shrink: 0; background: #fff;
  border-right: 1px solid #ebeef5; display: flex; flex-direction: column;
  overflow: hidden;
}
.sidebar-header {
  padding: 14px 16px; border-bottom: 1px solid #ebeef5;
}
.sidebar-header h3 { margin: 0; font-size: 16px; display: flex; align-items: center; gap: 6px; }
.sidebar-body { padding: 12px; overflow-y: auto; flex: 1; }
.sidebar-stats { display: flex; gap: 6px; flex-wrap: wrap; }
.sidebar-list { max-height: 300px; overflow-y: auto; }
.point-item {
  display: flex; align-items: center; gap: 8px; padding: 6px 8px;
  cursor: pointer; border-radius: 4px; font-size: 13px;
}
.point-item:hover { background: #f5f7fa; }
.point-name { font-weight: 500; color: #303133; min-width: 48px; }
.point-val { color: #f56c6c; font-family: monospace; }

.map-main { flex: 1; position: relative; }
.map-container { width: 100%; height: 100%; }
</style>
