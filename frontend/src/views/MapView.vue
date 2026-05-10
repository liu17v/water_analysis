<template>
  <div class="map-view">
    <!-- 搜索区域 -->
    <div class="map-search-area">
      <div class="search-wrapper" ref="searchWrapper">
        <el-input
          v-model="searchQuery"
          placeholder="搜索地点..."
          clearable
          :prefix-icon="SearchIcon"
          class="search-input"
          @keyup.enter="handleSearch"
          @clear="clearSearch"
        />
        <el-button type="primary" :icon="SearchIcon" class="search-btn" @click="handleSearch" />
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
      <el-radio-group :model-value="currentMode" size="small" @change="onModeChange" class="mode-switch">
        <el-radio-button value="street">街道</el-radio-button>
        <el-radio-button value="satellite">卫星</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 右下缩放由 Leaflet zoomControl 渲染 -->

    <!-- 右侧毛玻璃信息面板 -->
    <div class="map-glass-panel">
      <!-- 当前位置 -->
      <div class="panel-section">
        <div class="panel-section-header">
          <el-icon :size="14" color="#409eff"><Location /></el-icon>
          <span>当前位置</span>
        </div>
        <p class="panel-address">{{ locationName || '正在获取位置...' }}</p>
      </div>

      <div class="panel-divider" />

      <!-- 坐标 -->
      <div class="panel-section">
        <div class="panel-section-header">
          <span>地图坐标</span>
        </div>
        <div class="coord-grid">
          <div class="coord-cell">
            <span class="coord-label">经度</span>
            <span class="coord-value">{{ formatPos(position.lng) }}</span>
          </div>
          <div class="coord-cell">
            <span class="coord-label">纬度</span>
            <span class="coord-value">{{ formatPos(position.lat) }}</span>
          </div>
          <div class="coord-cell">
            <span class="coord-label">缩放</span>
            <span class="coord-value">{{ position.zoom }}</span>
          </div>
        </div>
      </div>

      <div class="panel-divider" />

      <!-- 天气 -->
      <div class="panel-section">
        <div class="panel-section-header">
          <span>实时天气</span>
        </div>
        <div v-if="weatherLoading" class="panel-status">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>获取天气中...</span>
        </div>
        <div v-else-if="weatherError" class="panel-status panel-status--warn">
          <span>{{ weatherError }}</span>
        </div>
        <div v-else-if="weather" class="weather-glow-card">
          <div class="weather-glow-top">
            <span class="weather-glow-temp">{{ weather.temperature }}<span class="weather-glow-unit">°C</span></span>
            <div class="weather-glow-info">
              <span class="weather-glow-desc">{{ weather.weather }}</span>
              <span class="weather-glow-sub">湿度 {{ weather.humidity }}%</span>
            </div>
          </div>
          <div class="weather-glow-bottom">
            <span>风向 {{ weather.winddirection || '-' }}</span>
            <span>风力 {{ weather.windpower ? weather.windpower + '级' : '-' }}</span>
          </div>
        </div>
        <div v-else class="panel-status">
          <span>暂无天气数据</span>
        </div>
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
import { Location, Search as SearchIcon, Loading } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const { weather, loading: weatherLoading, error: weatherError, fetchWeather } = useWeather()

const mapContainer = ref(null)
const searchWrapper = ref(null)
const position = reactive({ lat: 22.476, lng: 113.911, zoom: 16 })
const locationName = ref('')

const searchQuery = ref('')
const searchResults = ref([])

let map = null
let layers = null
let currentLayer = null
let lastFetchCenter = null
let zoomControl = null

const currentMode = ref('street')

function formatPos(v) {
  return v.toFixed(4)
}

function initMap() {
  if (!mapContainer.value) return
  map = L.map(mapContainer.value, {
    center: [22.476, 113.911],
    zoom: 16,
    zoomControl: false,
  })
  zoomControl = L.control.zoom({ position: 'bottomright' })
  zoomControl.addTo(map)

  layers = createAmapLayers(L)

  const mode = route.path === '/map/satellite' ? 'satellite' : 'street'
  currentMode.value = mode
  currentLayer = markRaw(layers[mode])
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
  currentLayer = markRaw(layers[mode])
  currentLayer.addTo(map)
})

onMounted(initMap)
onUnmounted(() => {
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

/* ── 搜索区域 ── */
.map-search-area {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 12px;
}
.search-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}
.search-input {
  width: 260px;
}
.search-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(12px);
  border-radius: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.25s ease;
}
.search-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.15);
  border-color: rgba(64, 158, 255, 0.3);
}
.search-input :deep(.el-input__inner) {
  font-size: 14px;
  height: 40px;
}
.search-btn {
  border-radius: 24px;
  height: 40px;
  width: 40px;
  padding: 0;
  font-size: 16px;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.25);
  transition: all 0.25s ease;
}
.search-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.35);
}

/* 模式切换 */
.mode-switch :deep(.el-radio-button__inner) {
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(12px);
  border-color: rgba(255, 255, 255, 0.3);
  padding: 8px 18px;
  font-size: 13px;
  transition: all 0.2s ease;
}
.mode-switch :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 20px 0 0 20px;
}
.mode-switch :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 20px 20px 0;
}
.mode-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #409eff;
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.3);
}

/* 搜索结果 */
.search-results {
  position: absolute;
  top: calc(100% + 6px);
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

/* ── 右侧毛玻璃面板 ── */
.map-glass-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 228px;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-radius: 28px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.4);
  animation: panelFadeIn 0.4s ease;
}

@keyframes panelFadeIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.panel-section {
  margin-bottom: 2px;
}
.panel-section:last-child {
  margin-bottom: 0;
}
.panel-section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #909399;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}
.panel-address {
  font-size: 13px;
  line-height: 1.5;
  color: #1d2129;
  word-break: break-all;
  margin: 0;
}
.panel-divider {
  height: 1px;
  background: linear-gradient(to right, rgba(0,0,0,0.04), rgba(0,0,0,0.08), rgba(0,0,0,0.04));
  margin: 14px 0;
}

/* 坐标网格 */
.coord-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 4px;
}
.coord-cell {
  text-align: center;
  padding: 6px 4px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 12px;
}
.coord-label {
  display: block;
  font-size: 10px;
  color: #909399;
  margin-bottom: 2px;
}
.coord-value {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #1d2129;
}

/* 状态信息 */
.panel-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #909399;
  padding: 10px 0;
}
.panel-status--warn {
  color: #e6a23c;
}

/* 天气发光卡片 */
.weather-glow-card {
  background: linear-gradient(135deg, #409eff 0%, #1a6bc4 100%);
  border-radius: 18px;
  padding: 16px;
  color: #fff;
  box-shadow: 0 4px 24px rgba(64, 158, 255, 0.3);
  transition: all 0.3s ease;
}
.weather-glow-card:hover {
  box-shadow: 0 6px 32px rgba(64, 158, 255, 0.4);
  transform: translateY(-1px);
}
.weather-glow-top {
  display: flex;
  align-items: center;
  gap: 16px;
}
.weather-glow-temp {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
  flex-shrink: 0;
}
.weather-glow-unit {
  font-size: 16px;
  font-weight: 400;
  opacity: 0.8;
}
.weather-glow-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.weather-glow-desc {
  font-size: 15px;
  font-weight: 500;
}
.weather-glow-sub {
  font-size: 11px;
  opacity: 0.85;
}
.weather-glow-bottom {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 11px;
  opacity: 0.8;
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
</style>
