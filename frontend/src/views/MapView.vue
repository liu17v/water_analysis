<template>
  <div class="map-view">
    <!-- 浮动信息栏 -->
    <div class="map-info-bar">
      <div class="info-left">
        <!-- 搜索框 -->
        <div class="search-wrapper" ref="searchWrapper">
          <el-input
            v-model="searchQuery"
            placeholder="搜索地点..."
            size="small"
            clearable
            :prefix-icon="SearchIcon"
            @keyup.enter="handleSearch"
            @clear="clearSearch"
          />
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

        <span class="info-divider" />
        <span class="info-item">
          <el-icon><Location /></el-icon>
          {{ formatPos(position.lat) }}, {{ formatPos(position.lng) }}
        </span>
        <span class="info-divider" />
        <span class="info-item">
          <el-icon><ZoomOut /></el-icon>
          {{ position.zoom }}
        </span>
        <span class="info-divider" />
        <span v-if="weather" class="info-item">
          <el-icon><Sunny /></el-icon>
          {{ weather.temperature }}°C
        </span>
        <span v-if="weather" class="info-item">
          {{ weather.humidity }}%
        </span>
        <span v-if="weather" class="info-item weather-condition">
          {{ weather.weather }}
        </span>
        <span v-if="weatherLoading" class="info-item">
          <el-icon class="is-loading"><Loading /></el-icon>
          加载天气...
        </span>
        <span v-if="weatherError" class="info-item weather-error">
          {{ weatherError }}
        </span>
        <span v-if="locationName" class="info-divider" />
        <span v-if="locationName" class="info-item location-name">{{ locationName }}</span>
      </div>
      <div class="info-right">
        <el-radio-group :model-value="currentMode" size="small" @change="onModeChange">
          <el-radio-button value="street">街道</el-radio-button>
          <el-radio-button value="satellite">卫星</el-radio-button>
        </el-radio-group>
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
import { Location, ZoomOut, Sunny, Search as SearchIcon, Loading } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const { weather, loading: weatherLoading, error: weatherError, fetchWeather } = useWeather()

const mapContainer = ref(null)
const searchWrapper = ref(null)
const position = reactive({ lat: 30.5, lng: 114.3, zoom: 10 })
const locationName = ref('')

// Search state
const searchQuery = ref('')
const searchResults = ref([])
const searchLoading = ref(false)

let map = null
let layers = null
let currentLayer = null
let lastFetchCenter = null

const currentMode = ref('street')

function formatPos(v) {
  return v.toFixed(4)
}

function initMap() {
  if (!mapContainer.value) return
  map = L.map(mapContainer.value, {
    center: [30.5, 114.3],
    zoom: 10,
    zoomControl: true,
  })
  layers = createAmapLayers(L)

  const mode = route.path === '/map/satellite' ? 'satellite' : 'street'
  currentMode.value = mode
  currentLayer = markRaw(layers[mode])
  currentLayer.addTo(map)

  map.on('moveend', onMapMove)

  // 处理搜索框外点击关闭
  document.addEventListener('click', onDocClick)

  nextTick(() => {
    map.invalidateSize()
  })

  // 初始获取位置信息和天气
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
    // 静默处理
  }
}

// ── 搜索功能 ──

async function handleSearch() {
  const q = searchQuery.value.trim()
  if (!q) return
  searchLoading.value = true
  try {
    const results = await amapGeocode(q)
    searchResults.value = results || []
  } finally {
    searchLoading.value = false
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
  map?.remove()
  map = null
})
</script>

<style scoped>
.map-view {
  position: relative;
  height: 100%;
  width: 100%;
}
.map-container {
  width: 100%;
  height: 100%;
  border-radius: 4px;
}
.map-info-bar {
  position: absolute;
  top: 12px;
  left: 12px;
  right: 12px;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  padding: 8px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  backdrop-filter: blur(4px);
  flex-wrap: wrap;
  gap: 8px;
}
.info-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.info-right {
  flex-shrink: 0;
}
.info-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #303133;
  white-space: nowrap;
}
.info-divider {
  width: 1px;
  height: 16px;
  background: #dcdfe6;
}
.location-name {
  color: #606266;
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.weather-condition {
  color: #409eff;
  font-weight: 500;
}
.weather-error {
  color: #e6a23c;
  font-size: 12px;
}

/* 搜索 */
.search-wrapper {
  position: relative;
  width: 200px;
}
.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  max-height: 260px;
  overflow-y: auto;
  z-index: 1001;
}
.search-result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  color: #303133;
  transition: background 0.15s;
}
.search-result-item:hover {
  background: #f0f5ff;
}
.search-result-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
