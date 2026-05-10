<template>
  <div class="sample-map">
    <div class="map-controls">
      <IndicatorSelect v-model="indicator" size="small" />
      <el-select v-model="layerType" size="small" style="width:120px">
        <el-option label="街道图" value="road" />
        <el-option label="卫星图" value="satellite" />
        <el-option label="混合图" value="hybrid" />
      </el-select>
      <el-input-number v-if="depths?.length" v-model="depthFilter" :min="minDepth" :max="maxDepth" :step="1" size="small" placeholder="深度过滤" />
      <span class="point-count" v-if="dataPoints.length">共 {{ visibleCount }} 个采样点</span>
    </div>
    <div ref="mapContainer" class="map-container" />
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue'
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

const minDepth = computed(() => props.depths.length ? Math.min(...props.depths) : 0)
const maxDepth = computed(() => props.depths.length ? Math.max(...props.depths) : 0)

let map = null
let markerLayer = null
let layers = null
let resizeObserver = null
let needsFitBounds = true
let updateTimer = null

const filteredPoints = computed(() => {
  if (depthFilter.value != null) {
    return props.dataPoints.filter(p => Math.abs(p.depth_m - depthFilter.value) < 0.5)
  }
  return props.dataPoints
})

const visibleCount = computed(() => filteredPoints.value.length)

function initMap() {
  if (!mapContainer.value) return
  map = L.map(mapContainer.value, {
    center: [30.5, 114.3],
    zoom: 10,
    zoomControl: false,
    preferCanvas: true,  // Canvas 渲染器，大量标记时性能远优于 SVG
  })
  L.control.zoom({ position: 'bottomright' }).addTo(map)
  layers = createAmapLayers(L)
  layers.road.addTo(map)
  markerLayer = L.layerGroup().addTo(map)
  nextTick(() => map.invalidateSize())
  scheduleUpdateMarkers()
}

function onContainerResize() {
  if (map && mapContainer.value?.offsetHeight > 0) {
    map.invalidateSize()
  }
}

function scheduleUpdateMarkers() {
  clearTimeout(updateTimer)
  updateTimer = setTimeout(updateMarkers, 80)
}

function updateMarkers() {
  if (!map || !markerLayer) return
  markerLayer.clearLayers()

  const pts = filteredPoints.value
  if (!pts.length) return

  const color = indicatorColor(indicator.value)
  const key = indicator.value
  const large = pts.length > 800
  const r = large ? 4 : 7

  // 批量构建所有标记，一次性加入 layerGroup
  const items = pts.map(p => {
    const value = p[key] ?? 0
    const m = L.circleMarker([p.lat, p.lon], {
      radius: r,
      fillColor: color,
      color: '#fff',
      weight: large ? 0.5 : 1.5,
      fillOpacity: large ? 0.65 : 0.8,
    })
    // 大量点时跳过 tooltip 以减少内存
    if (!large) {
      m.bindTooltip(
        `${key}: ${Number(value).toFixed(4)}<br>深度: ${p.depth_m}m<br>坐标: ${p.lat?.toFixed(4)}, ${p.lon?.toFixed(4)}`,
        { direction: 'top', offset: [0, -8] }
      )
    }
    return m
  })

  // 只做一次 DOM 操作：通过 layerGroup 批量添加
  items.forEach(m => markerLayer.addLayer(m))

  // fitBounds 仅首次加载时执行，过滤切换不触发
  if (needsFitBounds && pts.length) {
    const group = L.featureGroup(items)
    map.fitBounds(group.getBounds().pad(0.1), { maxZoom: 14 })
    needsFitBounds = false
  }
}

// 初始化数据时重置 fitBounds 标记
watch(() => props.dataPoints, (pts) => {
  if (pts?.length) {
    needsFitBounds = true
    scheduleUpdateMarkers()
  }
})

// 指标或深度改变时防抖更新（不触发 fitBounds）
watch([indicator, depthFilter], () => scheduleUpdateMarkers())

watch(layerType, (val) => {
  if (!map || !layers) return
  Object.values(layers).forEach(l => map.removeLayer(l))
  layers[val]?.addTo(map)
  // 保持 markerLayer 在最上层
  if (markerLayer) markerLayer.addTo(map)
})

onMounted(() => {
  initMap()
  if (mapContainer.value) {
    resizeObserver = new ResizeObserver(() => onContainerResize())
    resizeObserver.observe(mapContainer.value)
  }
})

onUnmounted(() => {
  clearTimeout(updateTimer)
  resizeObserver?.disconnect()
  map?.remove()
  map = null
})
</script>

<style scoped>
.sample-map {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.map-controls {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.point-count {
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: auto;
}

.map-container {
  width: 100%;
  height: calc(100vh - 300px);
  min-height: 400px;
  max-height: 800px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}
</style>
