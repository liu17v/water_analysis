<template>
  <div class="empty-state">
    <el-icon :size="48" color="#dcdfe6"><FolderDelete /></el-icon>
    <p>{{ text || '暂无数据' }}</p>
  </div>
</template>

<script setup>
defineProps({ text: { type: String, default: '' } })
</script>

<style scoped>
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 0; color: #909399; font-size: 14px; gap: 12px; }
</style>
