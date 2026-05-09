<template>
  <div v-if="visible" class="loading-overlay">
    <el-icon class="loading-icon" :size="32"><Loading /></el-icon>
    <p v-if="text" class="loading-text">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({ visible: Boolean, text: { type: String, default: '' } })
</script>

<style scoped>
.loading-overlay { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 0; }
.loading-icon { animation: rotating 1.5s linear infinite; color: #409eff; }
.loading-text { margin-top: 12px; color: #909399; font-size: 14px; }
@keyframes rotating { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
