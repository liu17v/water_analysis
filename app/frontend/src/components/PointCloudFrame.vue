<template>
  <div class="volume-frame">
    <div class="controls-bar">
      <div class="controls-left">
        <span class="control-label">指标</span>
        <el-select v-model="selectedIndicator" placeholder="选择指标" @change="updateUrl">
          <el-option label="叶绿素 (Chl)" value="chlorophyll" />
          <el-option label="溶解氧 (DO)" value="dissolved_oxygen" />
          <el-option label="水温 (Temp)" value="temperature" />
          <el-option label="pH" value="ph" />
          <el-option label="浊度 (Turb)" value="turbidity" />
        </el-select>
      </div>
      <div class="controls-right">
        <el-tag size="small" effect="plain" type="info">
          <el-icon><Link /></el-icon> 3D 体渲染
        </el-tag>
      </div>
    </div>
    <div v-if="iframeSrc" class="iframe-wrap" :key="iframeKey">
      <iframe
        :src="iframeSrc"
        frameborder="0"
        sandbox="allow-scripts allow-same-origin"
        class="volume-iframe"
      />
    </div>
    <el-empty v-else description="选择指标以查看 3D 体渲染" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Link } from '@element-plus/icons-vue'

const props = defineProps({
  taskId: { type: String, required: true },
})

const selectedIndicator = ref('chlorophyll')
const iframeKey = ref(0)

const iframeSrc = computed(() => {
  if (!props.taskId || !selectedIndicator.value) return ''
  return `/3d/${props.taskId}_${selectedIndicator.value}.html`
})

function updateUrl() {
  iframeKey.value++
}
</script>

<style scoped>
.volume-frame { background: #fff; border-radius: 8px; overflow: hidden; }
.controls-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; background: #fafafa; border-bottom: 1px solid #ebeef5;
  flex-wrap: wrap; gap: 8px;
}
.controls-left { display: flex; align-items: center; gap: 8px; }
.control-label { font-size: 13px; color: #606266; font-weight: 500; }
.controls-right { display: flex; align-items: center; gap: 8px; }
.iframe-wrap { width: 100%; height: 700px; }
.volume-iframe { width: 100%; height: 100%; border: none; }
</style>
