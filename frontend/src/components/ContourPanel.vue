<template>
  <div class="contour-panel">
    <div class="controls-bar">
      <div class="controls-left">
        <span class="control-label">指标</span>
        <el-select v-model="selectedIndicator" placeholder="选择指标" @change="updateSrc">
          <el-option label="叶绿素 (Chl)" value="chlorophyll" />
          <el-option label="溶解氧 (DO)" value="dissolved_oxygen" />
          <el-option label="水温 (Temp)" value="temperature" />
          <el-option label="pH" value="ph" />
          <el-option label="浊度 (Turb)" value="turbidity" />
        </el-select>
        <span class="control-label" style="margin-left:12px">深度</span>
        <el-select v-model="selectedDepth" placeholder="选择深度" @change="updateSrc">
          <el-option
            v-for="d in depths"
            :key="d"
            :label="d + 'm'"
            :value="d"
          />
        </el-select>
      </div>
      <div class="controls-right">
        <el-tag size="small" effect="plain" v-if="contourUrl">
          <el-icon><Link /></el-icon> 等值线图
        </el-tag>
      </div>
    </div>
    <div v-if="contourUrl" class="iframe-wrap" :key="iframeKey">
      <iframe
        :src="contourUrl"
        frameborder="0"
        sandbox="allow-scripts allow-same-origin"
        class="contour-iframe"
      />
    </div>
    <div v-else-if="loading" class="loading-wrap">
      <el-icon :size="32" class="is-loading"><Loading /></el-icon>
    </div>
    <el-empty v-else description="请选择指标和深度以查看等值线图" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Loading, Link } from '@element-plus/icons-vue'
import api from '../api'

const props = defineProps({
  taskId: { type: String, required: true },
  depths: { type: Array, default: () => [] },
})

const selectedIndicator = ref('chlorophyll')
const selectedDepth = ref(props.depths[0] || 1)
const loading = ref(false)
const iframeKey = ref(0)

watch(() => props.depths, (newDepths) => {
  if (newDepths.length && !selectedDepth.value) {
    selectedDepth.value = newDepths[0]
  }
})

const contourUrl = computed(() => {
  if (!props.taskId || !selectedIndicator.value) return ''
  const d = selectedDepth.value || 1
  return `/api/task/${props.taskId}/contour_html?indicator=${selectedIndicator.value}&depth=${d}`
})

function updateSrc() {
  iframeKey.value++
}

defineExpose({ updateSrc })
</script>

<style scoped>
.contour-panel { background: #fff; border-radius: 8px; overflow: hidden; }
.controls-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; background: #fafafa; border-bottom: 1px solid #ebeef5;
  flex-wrap: wrap; gap: 8px;
}
.controls-left { display: flex; align-items: center; gap: 8px; }
.control-label { font-size: 13px; color: #606266; font-weight: 500; }
.controls-right { display: flex; align-items: center; gap: 8px; }
.iframe-wrap { width: 100%; height: 600px; }
.contour-iframe { width: 100%; height: 100%; border: none; }
.loading-wrap { text-align: center; padding: 80px 0; }
</style>
