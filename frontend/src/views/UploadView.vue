<template>
  <div class="upload-view">
    <el-row :gutter="24">
      <el-col :span="16">
        <FileDrop @uploaded="onFileUploaded" />
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

    <el-card header="最近任务" style="margin-top:24px">
      <template #extra>
        <el-button text type="primary" @click="$router.push('/tasks')">查看全部</el-button>
      </template>
      <el-table :data="tasks" stripe v-loading="tableLoading" empty-text="暂无任务">
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
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'success' ? 'success' : row.status === 'failed' ? 'danger' : row.status === 'processing' ? 'warning' : 'info'"
              size="small"
            >{{ statusLabel(row.status) }}</el-tag>
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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit } from '@element-plus/icons-vue'
import FileDrop from '../components/FileDrop.vue'
import api from '../api'
import { useTask } from '../composables/useTask'

const { statusLabel } = useTask()

const tasks = ref([])
const tableLoading = ref(false)

const editingId = ref('')
const editingName = ref('')
function startEdit(task) {
  editingId.value = task.task_id
  editingName.value = task.reservoir_name || ''
}
async function saveEdit(task) {
  try {
    await api.updateTask(task.task_id, { reservoir_name: editingName.value || '' })
    task.reservoir_name = editingName.value
    ElMessage.success('水库名称已更新')
  } catch { ElMessage.error('更新失败') }
  finally { editingId.value = '' }
}
function cancelEdit() { editingId.value = '' }

async function refreshTasks() {
  tableLoading.value = true
  try {
    const res = await api.getTasks(1, 10)
    tasks.value = res.items || []
  } finally {
    tableLoading.value = false
  }
}

async function onDelete(taskId) {
  try { await api.deleteTask(taskId); ElMessage.success('任务已删除'); refreshTasks() }
  catch { ElMessage.error('删除失败，请稍后重试') }
}

async function onProcess(taskId) {
  try {
    await api.processTask(taskId)
    ElMessage.success('任务处理已启动')
    const poll = setInterval(async () => {
      try {
        const res = await api.getTaskStatus(taskId)
        if (res.status === 'success' || res.status === 'failed') {
          clearInterval(poll)
          if (res.status === 'success') ElMessage.success('任务处理完成')
          else ElMessage.error('任务处理失败')
          refreshTasks()
        }
      } catch {}
    }, 2000)
    setTimeout(() => clearInterval(poll), 120000)
  } catch { ElMessage.error('启动处理失败') }
}

function onFileUploaded() { refreshTasks() }
onMounted(refreshTasks)
</script>

<style scoped>
.upload-view { max-width: 1400px; margin: 0 auto; }
</style>
