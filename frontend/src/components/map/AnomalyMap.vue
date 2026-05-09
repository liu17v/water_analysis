<template>
  <div class="anomaly-map">
    <div ref="mapContainer" class="map-container" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { createAmapLayers } from '../../utils/amap'

const props = defineProps({
  anomalies: { type: Array, default: () => [] },
})

const mapContainer = ref(null)
let map = null
let markers = []
let layers = null

function getColor(value) {
  return value > 50 ? '#f56c6c' : value > 20 ? '#e6a23c' : '#67c23a'
}

function updateMarkers() {
  if (!map) return
  markers.forEach(m => map.removeLayer(m))
  markers = []

  props.anomalies.forEach(a => {
    const marker = L.circleMarker([a.lat, a.lon], {
      radius: 8, fillColor: getColor(a.value), color: '#fff', weight: 1, fillOpacity: 0.8,
    })
    marker.bindTooltip(`指标: ${a.indicator}<br>值: ${a.value.toFixed(2)}<br>方法: ${a.method}`)
    marker.addTo(map)
    markers.push(marker)
  })
}

onMounted(() => {
  if (!mapContainer.value) return
  map = L.map(mapContainer.value).setView([30.5, 114.3], 10)
  layers = createAmapLayers(L)
  layers.road.addTo(map)
  updateMarkers()
})

onUnmounted(() => { map?.remove() })

watch(() => props.anomalies, () => updateMarkers(), { deep: true })
</script>

<style scoped>
.anomaly-map { width: 100%; }
.map-container { width: 100%; height: 400px; border: 1px solid #ebeef5; border-radius: 4px; }
</style>
