<template>
  <div class="map-view">
    <!-- 浮动信息栏 -->
    <div class="map-info-bar">
      <div class="info-left">
        <span class="info-item">
          <el-icon><Location /></el-icon>
          位置: {{ formatPos(position.lat) }}, {{ formatPos(position.lng) }}
        </span>
        <span class="info-divider" />
        <span class="info-item">
          <el-icon><ZoomOut /></el-icon>
          缩放: {{ position.zoom }}
        </span>
        <span class="info-divider" />
        <span v-if="weather" class="info-item">
          <el-icon><Sunny /></el-icon>
          {{ weather.temperature }}°C
        </span>
        <span v-if="weather" class="info-item">
          湿度: {{ weather.humidity }}%
        </span>
        <span v-if="weather" class="info-item weather-condition">
          {{ weather.weather }}
        </span>
        <span v-if="weatherLoading" class="info-item">
          <el-icon class="is-loading"><Loading /></el-icon>
          获取天气中...
        </span>
        <span v-if="locationName" class="info-divider" />
        <span v-if="locationName" class="info-item location-name">{{ locationName }}</span>
      </div>
      <div class="info-right">
        <el-radio-group :model-value="currentMode" size="small" @change="onModeChange">
          <el-radio-button value="street">街道地图</el-radio-button>
          <el-radio-button value="satellite">卫星地图</el-radio-button>
        </el-radio-group>
      </div>
    </div>
    <div ref="mapContainer" class="map-container" />
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { createAmapLayers, amapRegeo } from '../utils/amap'
import { useWeather } from '../composables/useWeather'
import { Location, ZoomOut, Sunny, Loading } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const { weather, loading: weatherLoading, fetchWeather } = useWeather()

const mapContainer = ref(null)
const position = reactive({ lat: 30.5, lng: 114.3, zoom: 10 })
const locationName = ref('')
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
  currentLayer = layers[mode]
  currentLayer.addTo(map)

  map.on('moveend', onMapMove)

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

  // 移动足够远才重新获取天气
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

function onModeChange(mode) {
  router.push(`/map/${mode}`)
}

watch(() => route.path, (path) => {
  if (!map || !layers) return
  const mode = path === '/map/satellite' ? 'satellite' : 'street'
  currentMode.value = mode

  if (currentLayer) map.removeLayer(currentLayer)
  currentLayer = layers[mode]
  currentLayer.addTo(map)
})

onMounted(initMap)
onUnmounted(() => {
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
  gap: 4px;
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
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.weather-condition {
  color: #409eff;
  font-weight: 500;
}
</style>
