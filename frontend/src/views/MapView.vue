<template>
  <div class="map-view">
    <!-- 左上：搜索 + 模式切换 -->
    <div class="map-top-left">
      <div class="search-wrapper" ref="searchWrapper">
        <el-input
          v-model="searchQuery"
          placeholder="搜索地点..."
          clearable
          class="search-input"
          @keyup.enter="handleSearch"
          @clear="clearSearch"
        />
        <el-button type="primary" class="search-btn" @click="handleSearch">
          <el-icon :size="16"><Search /></el-icon>
        </el-button>
        <el-divider direction="vertical" class="top-divider" />
        <el-radio-group :model-value="currentMode" size="small" @change="onModeChange" class="mode-radio">
          <el-radio-button value="street">街道</el-radio-button>
          <el-radio-button value="satellite">卫星</el-radio-button>
        </el-radio-group>
        <transition name="fade">
          <div v-if="searchResults.length" class="search-results">
            <div
              v-for="(item, i) in searchResults"
              :key="i"
              class="search-result-item"
              @click="flyTo(item)"
            >
              <el-icon><Location /></el-icon>
              <span class="search-result-name">{{ item.name }}</span>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!-- 右上信息面板 -->
    <div class="map-info-panel">
      <div class="panel-card">
        <!-- 日期时间 -->
        <div class="panel-datetime">
          <el-icon :size="13" color="#409eff"><Clock /></el-icon>
          <span>{{ dateTime }}</span>
        </div>
        <!-- 位置 -->
        <div class="panel-location">
          <el-icon :size="16" color="#409eff"><Location /></el-icon>
          <span class="panel-addr">{{ locationName || '获取位置中...' }}</span>
        </div>
        <div class="panel-coords">
          <span>{{ formatPos(position.lng) }}, {{ formatPos(position.lat) }}</span>
          <span class="panel-zoom">层级 {{ position.zoom }}</span>
        </div>
        <!-- 天气 -->
        <div v-if="weather" class="panel-weather">
          <div class="pw-temp">{{ weather.temperature }}<span class="pw-unit">°C</span></div>
          <div class="pw-detail">
            <span>{{ weather.weather }}</span>
            <span>湿度 {{ weather.humidity }}%</span>
            <span>{{ weather.winddirection || '' }} {{ weather.windpower ? weather.windpower + '级' : '' }}</span>
          </div>
        </div>
        <div v-else-if="weatherLoading" class="panel-weather panel-weather--dim">加载天气中...</div>
        <div v-else-if="weatherError" class="panel-weather panel-weather--dim">{{ weatherError }}</div>
        <div v-else class="panel-weather panel-weather--dim">暂无天气数据</div>
      </div>
    </div>

    <div ref="mapContainer" class="map-container" />
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, onUnmounted, nextTick, markRaw } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { createAmapLayers, amapGeocode, amapRegeo } from '../utils/amap'
import { useWeather } from '../composables/useWeather'
import { Location, Search, Clock } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const { weather, loading: weatherLoading, error: weatherError, fetchWeather } = useWeather()

const mapContainer = ref(null)
const searchWrapper = ref(null)
const position = reactive({ lat: 22.635, lng: 114.128, zoom: 15 })
const locationName = ref('深圳市龙岗区联创科技园')
const dateTime = ref('')

let clockTimer = null

function updateClock() {
  const now = new Date()
  const y = now.getFullYear()
  const mo = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  const h = String(now.getHours()).padStart(2, '0')
  const mi = String(now.getMinutes()).padStart(2, '0')
  const s = String(now.getSeconds()).padStart(2, '0')
  const week = ['日','一','二','三','四','五','六'][now.getDay()]
  dateTime.value = `${y}-${mo}-${d} 周${week} ${h}:${mi}:${s}`
}

const searchQuery = ref('')
const searchResults = ref([])

let map = null
let layers = null
let currentLayer = null
let lastFetchCenter = null
let zoomControl = null

const currentMode = ref('street')

// createAmapLayers returns { road, satellite, hybrid } — map mode name to layer key
const MODE_LAYER_MAP = { street: 'road', satellite: 'satellite' }

function formatPos(v) {
  return v.toFixed(4)
}

function initMap() {
  if (!mapContainer.value) return
  map = L.map(mapContainer.value, {
    center: [22.635, 114.128],
    zoom: 15,
    zoomControl: false,
  })
  zoomControl = L.control.zoom({ position: 'bottomright' })
  zoomControl.addTo(map)

  layers = createAmapLayers(L)

  const mode = route.path === '/map/satellite' ? 'satellite' : 'street'
  currentMode.value = mode
  currentLayer = markRaw(layers[MODE_LAYER_MAP[mode]])
  currentLayer.addTo(map)

  map.on('moveend', onMapMove)
  document.addEventListener('click', onDocClick)

  nextTick(() => {
    map.invalidateSize()
  })

  onMapMove()
}

async function onMapMove() {
  if (!map) return
  const center = map.getCenter()
  position.lat = center.lat
  position.lng = center.lng
  position.zoom = map.getZoom()

  if (lastFetchCenter) {
    const dist = center.distanceTo(lastFetchCenter)
    if (dist < 5000) return
  }
  lastFetchCenter = center

  try {
    const regeo = await amapRegeo(center.lng, center.lat)
    if (regeo) {
      locationName.value = regeo.address
      await fetchWeather(regeo.city || regeo.adcode)
    }
  } catch {
    // 静默
  }
}

// ── 搜索 ──

async function handleSearch() {
  const q = searchQuery.value.trim()
  if (!q) return
  try {
    const results = await amapGeocode(q)
    searchResults.value = results || []
  } catch {
    // 静默
  }
}

function flyTo(item) {
  if (!map) return
  map.flyTo([item.lat, item.lon], 14, { duration: 1.5 })
  searchQuery.value = item.name
  searchResults.value = []
}

function clearSearch() {
  searchQuery.value = ''
  searchResults.value = []
}

function onDocClick(e) {
  if (searchWrapper.value && !searchWrapper.value.contains(e.target)) {
    searchResults.value = []
  }
}

function onModeChange(mode) {
  router.push(`/map/${mode}`)
}

watch(() => route.path, (path) => {
  if (!map || !layers) return
  const mode = path === '/map/satellite' ? 'satellite' : 'street'
  currentMode.value = mode
  if (currentLayer) map.removeLayer(currentLayer)
  currentLayer = markRaw(layers[MODE_LAYER_MAP[mode]])
  currentLayer.addTo(map)
})

onMounted(() => {
  initMap()
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
})
onUnmounted(() => {
  clearInterval(clockTimer)
  document.removeEventListener('click', onDocClick)
  if (zoomControl) map?.removeControl(zoomControl)
  map?.remove()
  map = null
})
</script>

<style scoped>
.map-view {
  position: relative;
  height: 100%;
  width: 100%;
  overflow: hidden;
}
.map-container {
  width: 100%;
  height: 100%;
}

/* ── 左上：搜索 + 模式切换 ── */
.map-top-left {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 1000;
}
.search-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: 28px;
  padding: 6px 8px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.35);
}
.search-input {
  width: 230px;
}
.search-input :deep(.el-input__wrapper) {
  background: transparent;
  border-radius: 22px;
  box-shadow: none;
  border: none;
  padding-left: 12px;
}
.search-input :deep(.el-input__wrapper:hover) {
  box-shadow: none;
}
.search-input :deep(.el-input__inner) {
  font-size: 14px;
  height: 38px;
}
.search-btn {
  border-radius: 22px;
  height: 38px;
  width: 38px;
  padding: 0;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
  transition: all 0.25s ease;
}
.search-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.3);
}
.top-divider {
  height: 24px;
  margin: 0 4px;
}
.mode-radio :deep(.el-radio-button__inner) {
  background: transparent;
  border: none;
  padding: 6px 14px;
  font-size: 13px;
  color: #606266;
  border-radius: 0;
  box-shadow: none;
  transition: all 0.2s ease;
}
.mode-radio :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 18px 0 0 18px;
  padding-left: 6px;
}
.mode-radio :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 18px 18px 0;
  padding-right: 6px;
}
.mode-radio :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: rgba(64, 158, 255, 0.12);
  color: #409eff;
  font-weight: 600;
  box-shadow: none;
}

/* 搜索结果 */
.search-results {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(16px);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  max-height: 280px;
  overflow-y: auto;
  z-index: 1001;
  padding: 6px;
}
.search-result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  font-size: 13px;
  color: #303133;
  border-radius: 10px;
  transition: all 0.15s ease;
}
.search-result-item:hover {
  background: rgba(64, 158, 255, 0.08);
}
.search-result-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── 右上信息面板 ── */
.map-info-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 1000;
}
.panel-card {
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-radius: 20px;
  padding: 16px 20px;
  box-shadow: 0 4px 28px rgba(0, 0, 0, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.4);
  min-width: 226px;
  max-width: 300px;
  animation: panelIn 0.4s ease;
}
@keyframes panelIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.panel-datetime {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #606266;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}
.panel-datetime .el-icon { flex-shrink: 0; }

.panel-location {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-bottom: 8px;
}
.panel-location .el-icon {
  flex-shrink: 0;
  margin-top: 1px;
}
.panel-addr {
  font-size: 14px;
  font-weight: 500;
  color: #1d2129;
  line-height: 1.4;
  word-break: break-all;
}

.panel-coords {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}
.panel-zoom {
  font-weight: 500;
  color: #409eff;
}

/* 天气区域 */
.panel-weather {
  display: flex;
  align-items: center;
  gap: 14px;
}
.panel-weather--dim {
  font-size: 12px;
  color: #909399;
  padding: 4px 0;
}
.pw-temp {
  font-size: 32px;
  font-weight: 700;
  color: #409eff;
  line-height: 1;
  flex-shrink: 0;
}
.pw-unit {
  font-size: 14px;
  font-weight: 400;
  opacity: 0.7;
}
.pw-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  color: #606266;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ── 响应式 ── */
@media (max-width: 640px) {
  .map-top-left { top: 10px; left: 10px; }
  .search-input { width: 140px; }
  .map-info-panel { top: 10px; right: 10px; }
  .panel-card { min-width: auto; max-width: 200px; padding: 12px 14px; }
  .pw-temp { font-size: 24px; }
  .panel-addr { font-size: 12px; }
}
</style>
