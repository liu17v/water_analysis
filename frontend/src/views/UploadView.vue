<template>
  <div class="upload-view">
    <el-row :gutter="24" class="card-grid-row">
      <el-col :span="16">
        <div class="upload-zone">
          <div class="reservoir-input-wrapper">
            <label class="input-label">水库名称</label>
            <el-input v-model="reservoirName" placeholder="请输入水库名称（选填）" clearable style="width:280px" />
          </div>
          <el-upload
            ref="uploadRef"
            drag
            multiple
            action="/api/upload"
            :headers="uploadHeaders"
            :data="{ reservoir_name: reservoirName }"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :before-upload="handleBeforeUpload"
            accept=".csv"
          >
            <el-icon :size="64" color="#409eff"><UploadFilled /></el-icon>
            <p class="drop-text">拖拽 CSV 文件到此处，或点击选择文件</p>
            <p class="drop-hint">支持 UTF-8 / GBK 编码，可批量上传</p>
          </el-upload>
        </div>
      </el-col>
      <el-col :span="8">
        <el-card header="上传说明">
          <el-timeline>
            <el-timeline-item timestamp="第 1 步" placement="top">
              拖拽或点击上传 CSV 文件
            </el-timeline-item>
            <el-timeline-item timestamp="第 2 步" placement="top">
              系统自动解析数据，字段智能映射
            </el-timeline-item>
            <el-timeline-item timestamp="第 3 步" placement="top">
              后台异步处理：插值 → 可视化 → 异常检测 → 入库
            </el-timeline-item>
            <el-timeline-item timestamp="第 4 步" placement="top">
              查看 2D/3D 可视化 + 生成分析报告
            </el-timeline-item>
          </el-timeline>
          <el-divider />
          <p style="font-size:13px;color:#909399">
            支持格式：CSV (UTF-8 / GBK)<br />
            必含字段：lon, lat, depth_m<br />
            可选字段：temp, cond, salt, pH, turb, chl, odo
          </p>
        </el-card>
      </el-col>
    </el-row>

    <el-card header="最近任务" class="section-gap-lg">
      <template #extra>
        <el-button text type="primary" @click="$router.push('/tasks')">查看全部</el-button>
      </template>
      <el-table :data="taskStore.taskList" stripe v-loading="taskStore.loading.list" empty-text="暂无任务">
        <el-table-column prop="task_id" label="任务ID" min-width="200" show-overflow-tooltip />
        <el-table-column label="水库名称" min-width="160">
          <template #default="{ row }">
            <template v-if="editingId === row.task_id">
              <el-input v-model="editingName" size="small" style="width:120px"
                @keyup.enter="saveEdit(row)" @keyup.escape="cancelEdit" />
              <el-button size="small" type="primary" link @click="saveEdit(row)">确定</el-button>
              <el-button size="small" link @click="cancelEdit">取消</el-button>
            </template>
            <template v-else>
              {{ row.reservoir_name || '-' }}
              <el-button size="small" link type="primary" @click="startEdit(row)"><el-icon><Edit /></el-icon></el-button>
            </template>
          </template>
        </el-table-column>
        <el-table-column prop="original_filename" label="原始文件" min-width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <StatusTag :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="total_points" label="采样点" width="90" />
        <el-table-column prop="anomaly_count" label="异常点" width="90" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="360" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'success'">
              <el-button type="primary" size="small" link @click="$router.push(`/task/${row.task_id}`)">详情</el-button>
              <el-button type="success" size="small" link @click="$router.push(`/task/${row.task_id}/anomalies`)">异常</el-button>
              <el-button type="info" size="small" link @click="$router.push(`/task/${row.task_id}/report`)">报告</el-button>
            </template>
            <el-button v-else-if="row.status === 'processing'" type="warning" size="small" link @click="$router.push(`/task/${row.task_id}`)">进度</el-button>
            <el-button v-else-if="row.status === 'pending'" type="success" size="small" link @click="onProcess(row.task_id)">处理</el-button>
            <el-popconfirm title="确认删除?" @confirm="onDelete(row.task_id)">
              <template #reference><el-button size="small" link type="danger">删除</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, UploadFilled } from '@element-plus/icons-vue'
import { useTaskStore } from '../stores/task'
import { useStatus } from '../composables/useStatus'
import { usePolling } from '../composables/usePolling'
import StatusTag from '../components/common/StatusTag.vue'

const taskStore = useTaskStore()
const { statusLabel } = useStatus()

const reservoirName = ref('')
const uploading = ref(false)
const uploadRef = ref(null)

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})

function handleBeforeUpload() {
  uploading.value = true
  return true
}

function handleUploadSuccess(res) {
  uploading.value = false
  const taskId = res.task_id || res?.datas?.task_id
  if (taskId) {
    ElMessage.success('上传成功')
    uploadRef.value?.clearFiles()
    taskStore.fetchTasks(1, 10)
  }
}

function handleUploadError() {
  uploading.value = false
  ElMessage.error('上传失败')
}

// --- Inline edit ---
const editingId = ref('')
const editingName = ref('')

function startEdit(task) {
  editingId.value = task.task_id
  editingName.value = task.reservoir_name || ''
}

async function saveEdit(task) {
  try {
    await taskStore.updateTask(task.task_id, { reservoir_name: editingName.value || '' })
    task.reservoir_name = editingName.value
    ElMessage.success('水库名称已更新')
  } catch {
    ElMessage.error('更新失败')
  } finally {
    editingId.value = ''
  }
}

function cancelEdit() {
  editingId.value = ''
}

// --- Delete ---
async function onDelete(taskId) {
  try {
    await taskStore.deleteTask(taskId)
    ElMessage.success('任务已删除')
    taskStore.fetchTasks(1, 10)
  } catch {
    ElMessage.error('删除失败，请稍后重试')
  }
}

// --- Process + polling ---
const pollingTaskId = ref('')

const { start: startPolling } = usePolling(
  async () => {
    await taskStore.pollTaskStatus(pollingTaskId.value)
    const s = taskStore.currentStatus?.status
    if (s === 'success' || s === 'failed') {
      if (s === 'success') {
        ElMessage.success('任务处理完成')
      } else {
        ElMessage.error('任务处理失败')
      }
      taskStore.fetchTasks(1, 10)
      return true
    }
    return false
  },
  2000,
  120000
)

async function onProcess(taskId) {
  try {
    await taskStore.processTask(taskId)
    ElMessage.success('任务处理已启动')
    pollingTaskId.value = taskId
    startPolling()
  } catch {
    ElMessage.error('启动处理失败')
  }
}

onMounted(() => {
  taskStore.fetchTasks(1, 10)
})
</script>

<style scoped>
.upload-view { max-width: 1400px; margin: 0 auto; }
.upload-view :deep(.card-grid-row) { align-items: stretch; }
.upload-zone {
  border: 2px dashed rgba(64, 158, 255, 0.25);
  border-radius: 24px;
  padding: 28px 32px 36px;
  text-align: center;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100%;
}
.upload-zone:hover {
  border-color: rgba(64, 158, 255, 0.5);
  background: rgba(255, 255, 255, 0.55);
  box-shadow: 0 4px 24px rgba(64, 158, 255, 0.08);
}
.reservoir-input-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}
.input-label {
  font-size: 14px;
  color: var(--text-primary);
  white-space: nowrap;
  font-weight: 500;
}
.drop-text { font-size: 16px; color: var(--text-primary); margin: 16px 0 8px; }
.drop-hint { font-size: 13px; color: var(--text-secondary); }

@media (max-width: 900px) {
  .upload-view :deep(.el-col-16),
  .upload-view :deep(.el-col-8) { width: 100%; }
}
</style>
