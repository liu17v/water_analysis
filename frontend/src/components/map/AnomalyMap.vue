<template>
  <div class="anomaly-map">
    <div class="map-mode-bar">
      <el-radio-group v-model="mapMode" size="small" @change="switchLayer">
        <el-radio-button value="road">街道</el-radio-button>
        <el-radio-button value="satellite">卫星</el-radio-button>
      </el-radio-group>
    </div>
    <div ref="mapContainer" class="map-container" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { createAmapLayers } from '../../utils/amap'

const props = defineProps({
  anomalies: { type: Array, default: () => [] },
})

const mapContainer = ref(null)
const mapMode = ref('road')
let map = null
let markers = []
let layers = null
let currentLayer = null

function getColor(value) {
  return value > 50 ? '#f56c6c' : value > 20 ? '#e6a23c' : '#67c23a'
}

function updateMarkers() {
  if (!map) return
  markers.forEach(m => map.removeLayer(m))
  markers = []

  if (!props.anomalies?.length) return

  props.anomalies.forEach(a => {
    if (a.lat == null || a.lon == null) return
    const marker = L.circleMarker([a.lat, a.lon], {
      radius: 8,
      fillColor: getColor(a.value),
      color: '#fff',
      weight: 1.5,
      fillOpacity: 0.85,
    })
    marker.bindTooltip(
      `指标: ${a.indicator}<br>值: ${(a.value ?? '-').toFixed(4)}<br>深度: ${a.depth ?? '-'}m`,
      { direction: 'top', offset: [0, -8] }
    )
    marker.addTo(map)
    markers.push(marker)
  })

  if (markers.length) {
    const group = L.featureGroup(markers)
    map.fitBounds(group.getBounds().pad(0.15))
  }
}

function switchLayer(mode) {
  mapMode.value = mode
  if (!map || !layers) return
  if (currentLayer) map.removeLayer(currentLayer)
  currentLayer = layers[mode]
  currentLayer.addTo(map)
}

onMounted(async () => {
  if (!mapContainer.value) return
  map = L.map(mapContainer.value, {
    center: [30.5, 114.3],
    zoom: 10,
    zoomControl: false,
  })
  L.control.zoom({ position: 'bottomright' }).addTo(map)

  layers = createAmapLayers(L)
  currentLayer = layers.road
  currentLayer.addTo(map)

  await nextTick()
  map.invalidateSize()

  updateMarkers()
})

onUnmounted(() => { map?.remove() })

watch(() => props.anomalies, () => updateMarkers(), { deep: true })
</script>

<style scoped>
.anomaly-map {
  position: relative;
  width: 100%;
  border-radius: 16px;
  overflow: hidden;
}

.map-container {
  width: 100%;
  height: 420px;
  border-radius: 16px;
  overflow: hidden;
}

.map-mode-bar {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 1000;
}

.map-mode-bar :deep(.el-radio-button__inner) {
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(12px);
  border-color: rgba(255, 255, 255, 0.3);
  padding: 6px 16px;
  font-size: 12px;
  border-radius: 0;
}

.map-mode-bar :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 16px 0 0 16px;
}

.map-mode-bar :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 16px 16px 0;
}

.map-mode-bar :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #409eff;
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}
</style>
