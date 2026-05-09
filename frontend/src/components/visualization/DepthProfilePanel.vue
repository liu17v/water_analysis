<template>
  <div class="depth-profile-panel">
    <div class="panel-header">
      <IndicatorSelect v-model="indicator" size="small" />
      <el-button size="small" @click="refresh"><el-icon><Refresh /></el-icon></el-button>
      <el-button size="small" @click="isFullscreen = !isFullscreen"><el-icon><FullScreen /></el-icon></el-button>
    </div>
    <div ref="containerRef" class="iframe-container" :class="{ fullscreen: isFullscreen }">
      <LoadingOverlay v-if="loading" :visible="true" text="加载深度剖面..." />
      <iframe v-show="!loading" :src="iframeUrl" frameborder="0" @load="loading = false" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
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

const iframeUrl = computed(() => `/api/task/${props.taskId}/depth_profile_html?indicator=${indicator.value}`)

function refresh() {
  loading.value = true
  const iframe = containerRef.value?.querySelector('iframe')
  if (iframe) iframe.src = iframe.src
}
</script>

<style scoped>
.depth-profile-panel { display: flex; flex-direction: column; gap: 8px; }
.panel-header { display: flex; gap: 8px; align-items: center; }
.iframe-container { position: relative; width: 100%; height: 500px; border: 1px solid #ebeef5; border-radius: 4px; overflow: hidden; }
.iframe-container.fullscreen { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 9999; background: #fff; }
.iframe-container iframe { width: 100%; height: 100%; }
</style>
