<template>
  <div class="pointcloud-panel">
    <div class="panel-header">
      <IndicatorSelect v-model="indicator" size="small" />
      <el-button size="small" @click="refresh"><el-icon><Refresh /></el-icon></el-button>
      <el-button size="small" @click="isFullscreen = !isFullscreen"><el-icon><FullScreen /></el-icon></el-button>
    </div>
    <div ref="containerRef" class="viz-frame" :class="{ fullscreen: isFullscreen }">
      <iframe :key="iframeUrl" :src="iframeUrl" frameborder="0" @load="onLoad" />
      <LoadingOverlay :visible="loading" text="加载 3D 渲染..." />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import IndicatorSelect from '../common/IndicatorSelect.vue'
import LoadingOverlay from '../common/LoadingOverlay.vue'

const props = defineProps({
  taskId: { type: String, required: true },
  defaultIndicator: { type: String, default: 'chlorophyll' },
})

const indicator = ref(props.defaultIndicator)
const isFullscreen = ref(false)
const loading = ref(true)
const containerRef = ref(null)

const iframeUrl = computed(() => `/3d/${props.taskId}_${indicator.value}.html`)

watch(indicator, () => { loading.value = true })

function onLoad() { loading.value = false }

function refresh() {
  loading.value = true
  const iframe = containerRef.value?.querySelector('iframe')
  if (iframe) iframe.src = iframe.src
}
</script>

<style scoped>
.pointcloud-panel { display: flex; flex-direction: column; gap: 8px; }
.panel-header { display: flex; gap: 8px; align-items: center; }
.viz-frame { position: relative; width: 100%; height: calc(100vh - 320px); min-height: 400px; max-height: 800px; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04); background: var(--glass-bg); }
.viz-frame.fullscreen { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 9999; background: #fff; }
.viz-frame iframe { width: 100%; height: 100%; }
.viz-frame :deep(.loading-overlay) { position: absolute; inset: 0; z-index: 2; }
</style>
