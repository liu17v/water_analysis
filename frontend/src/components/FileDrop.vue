<template>
  <div
    class="file-drop"
    :class="{ 'is-dragover': isDragover }"
    @dragover.prevent="isDragover = true"
    @dragleave.prevent="isDragover = false"
    @drop.prevent="onDrop"
  >
    <div class="drop-header">
      <div class="reservoir-input">
        <label class="input-label">水库名称</label>
        <el-input v-model="reservoirName" placeholder="请输入水库名称（选填）" clearable style="width:280px" />
      </div>
    </div>
    <input
      ref="inputRef"
      type="file"
      accept=".csv"
      multiple
      style="display:none"
      @change="onFileChange"
    />
    <el-icon :size="64" color="#409eff"><UploadFilled /></el-icon>
    <p class="drop-text">拖拽 CSV 文件到此处，或点击选择文件</p>
    <p class="drop-hint">支持 UTF-8 / GBK 编码，可批量上传</p>
    <el-button type="primary" size="large" @click="inputRef.click()" style="margin-top:16px">
      选择文件
    </el-button>

    <div v-if="files.length" class="file-list">
      <el-tag
        v-for="(f, i) in files"
        :key="i"
        closable
        :type="f.status === 'uploading' ? 'warning' : f.status === 'done' ? 'success' : f.status === 'error' ? 'danger' : 'info'"
        @close="removeFile(i)"
        style="margin:4px"
      >
        {{ f.name }}
        <template v-if="f.status === 'uploading'">(上传中...)</template>
        <template v-else-if="f.status === 'done'">(完成)</template>
        <template v-else-if="f.status === 'error'">(失败)</template>
      </el-tag>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '../api'

const emit = defineEmits(['uploaded'])
const isDragover = ref(false)
const reservoirName = ref('')
const files = ref([])
const inputRef = ref(null)

function onDrop(e) {
  isDragover.value = false
  const dropped = [...e.dataTransfer.files].filter(f => f.name.endsWith('.csv'))
  processFiles(dropped)
}

function onFileChange(e) {
  processFiles([...e.target.files])
  e.target.value = ''
}

function removeFile(idx) {
  files.value.splice(idx, 1)
}

async function processFiles(fileList) {
  for (const file of fileList) {
    const entry = { name: file.name, status: 'uploading' }
    files.value.push(entry)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('reservoir_name', reservoirName.value || file.name.replace(/\.csv$/i, ''))
      const res = await api.upload(formData)
      entry.status = 'done'
      entry.taskId = res.task_id
      ElMessage.success(`${file.name} 上传成功`)
      emit('uploaded', res.task_id)
    } catch {
      entry.status = 'error'
      ElMessage.error(`${file.name} 上传失败`)
    }
  }
}
</script>

<style scoped>
.drop-header {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}
.reservoir-input {
  display: flex;
  align-items: center;
  gap: 8px;
}
.input-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
  font-weight: 500;
}
.file-drop {
  border: 2px dashed #d9d9d9;
  border-radius: 12px;
  padding: 24px 40px 40px;
  text-align: center;
  transition: all 0.3s;
  cursor: pointer;
  background: #fafafa;
}
.file-drop.is-dragover {
  border-color: #409eff;
  background: #ecf5ff;
}
.drop-text { font-size: 16px; color: #606266; margin: 16px 0 8px; }
.drop-hint { font-size: 13px; color: #c0c4cc; }
.file-list { margin-top: 20px; }
</style>
