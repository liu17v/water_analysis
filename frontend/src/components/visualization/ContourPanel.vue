<template>
  <div class="contour-panel">
    <div class="panel-header">
      <IndicatorSelect v-model="indicator" size="small" />
      <el-select v-if="depths?.length" v-model="selectedDepth" size="small" placeholder="选择深度" style="width:140px">
        <el-option v-for="d in depths" :key="d" :label="`${d}m`" :value="d" />
      </el-select>
      <el-button size="small" @click="refresh"><el-icon><Refresh /></el-icon></el-button>
      <el-button size="small" @click="toggleFullscreen"><el-icon><FullScreen /></el-icon></el-button>
    </div>
    <div ref="containerRef" class="viz-frame" :class="{ fullscreen: isFullscreen }">
      <iframe :key="iframeUrl" :src="iframeUrl" frameborder="0" @load="onIframeLoad" />
      <LoadingOverlay :visible="loading" text="加载等值线..." />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import IndicatorSelect from '../common/IndicatorSelect.vue'
import LoadingOverlay from '../common/LoadingOverlay.vue'

const props = defineProps({
  taskId: { type: String, required: true },
  depths: { type: Array, default: () => [] },
  defaultIndicator: { type: String, default: 'chlorophyll' },
})

const indicator = ref(props.defaultIndicator)
const selectedDepth = ref(props.depths?.[0])
const isFullscreen = ref(false)
const loading = ref(true)
const containerRef = ref(null)

const iframeUrl = computed(() => {
  const depth = selectedDepth.value || ''
  return `/api/task/${props.taskId}/contour_html?indicator=${indicator.value}&depth=${depth}`
})

watch([indicator, selectedDepth], () => { loading.value = true })

function onIframeLoad() {
  loading.value = false
}

function refresh() {
  loading.value = true
  const iframe = containerRef.value?.querySelector('iframe')
  if (iframe) iframe.src = iframe.src
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  if (isFullscreen.value) {
    containerRef.value?.requestFullscreen?.()
  } else {
    document.exitFullscreen?.()
  }
}

watch(() => props.depths, (d) => {
  if (d?.length && !selectedDepth.value) selectedDepth.value = d[0]
})

watch(isFullscreen, (val) => {
  if (!val) document.exitFullscreen?.()
})
</script>

<style scoped>
.contour-panel { display: flex; flex-direction: column; gap: 8px; }
.panel-header { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.viz-frame { position: relative; width: 100%; height: calc(100vh - 320px); min-height: 400px; max-height: 800px; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04); background: var(--glass-bg); }
.viz-frame.fullscreen { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 9999; background: #fff; }
.viz-frame iframe { width: 100%; height: 100%; }
.viz-frame :deep(.loading-overlay) { position: absolute; inset: 0; z-index: 2; }
</style>
