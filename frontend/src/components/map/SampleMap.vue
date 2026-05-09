<template>
  <div class="sample-map">
    <div class="map-controls">
      <IndicatorSelect v-model="indicator" size="small" />
      <el-select v-model="layerType" size="small" style="width:120px">
        <el-option label="街道图" value="road" />
        <el-option label="卫星图" value="satellite" />
        <el-option label="混合图" value="hybrid" />
      </el-select>
      <el-input-number v-if="depths?.length" v-model="depthFilter" :min="Math.min(...depths)" :max="Math.max(...depths)" :step="1" size="small" placeholder="深度过滤" />
    </div>
    <div ref="mapContainer" class="map-container" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { createAmapLayers } from '../../utils/amap'
import { useIndicator } from '../../composables/useIndicator'
import IndicatorSelect from '../common/IndicatorSelect.vue'

const props = defineProps({
  dataPoints: { type: Array, default: () => [] },
  depths: { type: Array, default: () => [] },
})

const { indicatorColor } = useIndicator()
const indicator = ref('chlorophyll')
const layerType = ref('road')
const depthFilter = ref(null)
const mapContainer = ref(null)

let map = null
let markers = []
let layers = null

function initMap() {
  if (!mapContainer.value) return
  map = L.map(mapContainer.value).setView([30.5, 114.3], 10)
  layers = createAmapLayers(L)
  layers.road.addTo(map)
  updateMarkers()
}

function updateMarkers() {
  if (!map) return
  markers.forEach(m => map.removeLayer(m))
  markers = []

  const filtered = depthFilter.value != null
    ? props.dataPoints.filter(p => Math.abs(p.depth_m - depthFilter.value) < 0.5)
    : props.dataPoints

  filtered.forEach(p => {
    const value = p[indicator.value] ?? 0
    const color = indicatorColor(indicator.value)
    const marker = L.circleMarker([p.lat, p.lon], {
      radius: 6, fillColor: color, color: '#fff', weight: 1, fillOpacity: 0.7,
    })
    marker.bindTooltip(`${indicator.value}: ${value.toFixed(2)}<br>深度: ${p.depth_m}m`)
    marker.addTo(map)
    markers.push(marker)
  })
}

watch([indicator, depthFilter], () => updateMarkers())
watch(layerType, (val) => {
  if (!map || !layers) return
  Object.values(layers).forEach(l => map.removeLayer(l))
  layers[val]?.addTo(map)
})

onMounted(initMap)
onUnmounted(() => { map?.remove() })
</script>

<style scoped>
.sample-map { display: flex; flex-direction: column; gap: 8px; }
.map-controls { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.map-container { width: 100%; height: 500px; border: 1px solid #ebeef5; border-radius: 4px; }
</style>
