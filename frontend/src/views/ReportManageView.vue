<template>
  <div class="report-manage">
    <el-page-header @back="$router.push('/')" content="智能报告" style="margin-bottom:16px" />

    <!-- 生成新报告 -->
    <el-card header="生成新报告" style="margin-bottom:16px">
      <el-row :gutter="16" align="middle">
        <el-col :span="10">
          <el-select
            v-model="selectedTaskId"
            filterable
            placeholder="选择已完成分析的任务..."
            :loading="taskStore.loading.list"
            style="width:100%"
            @change="onTaskSelect"
          >
            <el-option
              v-for="t in reportableTasks"
              :key="t.task_id"
              :label="`${t.reservoir_name || '未知水库'} (${t.total_points}点/${t.anomaly_count}异常)`"
              :value="t.task_id"
            />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-button
            type="primary"
            :disabled="!selectedTaskId || generating"
            :loading="generating"
            @click="doGenerate"
          >
            <el-icon><Document /></el-icon>
            {{ generating ? '正在生成...' : '生成分析报告' }}
          </el-button>
          <el-button
            v-if="selectedTaskId"
            size="small"
            text
            type="primary"
            @click="$router.push(`/task/${selectedTaskId}`)"
          >
            查看任务详情 →
          </el-button>
        </el-col>
      </el-row>

      <!-- 选中任务详情 -->
      <transition name="fade">
        <div v-if="selectedTask" class="task-detail-card">
          <el-descriptions :column="4" border size="small">
            <el-descriptions-item label="水库名称">{{ selectedTask.reservoir_name || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="采样点数">{{ selectedTask.total_points }}</el-descriptions-item>
            <el-descriptions-item label="异常点数">{{ selectedTask.anomaly_count }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ selectedTask.created_at }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </transition>

      <!-- 生成进度 / 结果 -->
      <div v-if="generating || genResult" style="margin-top:16px">
        <el-progress v-if="generating" :percentage="+genProgress.toFixed(2)" :stroke-width="12" style="margin-bottom:8px" />
        <p v-if="generating" style="color:#606266;font-size:13px">
          <el-icon class="is-loading"><Loading /></el-icon> {{ genPhase }}
        </p>
        <el-result
          v-if="genResult === 'ok'"
          icon="success" title="报告生成成功"
          sub-title="报告已保存，可在线预览或下载"
        >
          <template #extra>
            <el-button type="primary" @click="previewGenerated">在线预览</el-button>
            <el-button type="success" @click="downloadGenerated">下载 DOCX</el-button>
          </template>
        </el-result>
        <el-alert v-if="genResult === 'fail'" :title="genError" type="error" show-icon :closable="false" />
      </div>
    </el-card>

    <!-- 已生成报告列表 -->
    <el-card header="已生成报告列表">
      <template #extra>
        <el-button size="small" text @click="loadReports">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </template>

      <el-table :data="rows" v-loading="reportStore.loading.list" stripe border size="small" max-height="500">
        <el-table-column prop="task_id" label="任务ID" min-width="200" show-overflow-tooltip />
        <el-table-column prop="reservoir_name" label="水库名称" width="140" />
        <el-table-column prop="total_points" label="采样点" width="80" />
        <el-table-column prop="anomaly_count" label="异常点" width="80" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <StatusTag :status="row.report_path ? 'success' : 'pending'" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" text @click="$router.push(`/task/${row.task_id}`)">
              <el-icon><View /></el-icon> 任务详情
            </el-button>
            <el-button size="small" type="success" text @click="previewReport(row)">
              <el-icon><View /></el-icon> 预览
            </el-button>
            <el-button size="small" type="warning" text @click="openReport(row)">
              <el-icon><Download /></el-icon> 下载
            </el-button>
            <el-button size="small" type="danger" text @click="handleDelete(row.task_id)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > pageSize"
        style="margin-top:16px; justify-content:flex-end"
        layout="total, prev, pager, next"
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        @current-change="loadReports"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useReportStore } from '../stores/report'
import { useTaskStore } from '../stores/task'
import { usePolling } from '../composables/usePolling'
import { useStatus } from '../composables/useStatus'
import { ElMessage, ElMessageBox } from 'element-plus'
import StatusTag from '../components/common/StatusTag.vue'
import { View, Download, Delete, Document, Loading, Refresh } from '@element-plus/icons-vue'

const reportStore = useReportStore()
const taskStore = useTaskStore()
const { statusLabel, statusType } = useStatus()

// ── Report list ──
const page = ref(1)
const pageSize = ref(20)

const rows = computed(() => reportStore.reportList || [])
const total = computed(() => reportStore.reportTotal)

async function loadReports() {
  await reportStore.fetchReports(page.value, pageSize.value)
}

function triggerDownload(url, filename) {
  const a = document.createElement('a')
  a.href = url
  if (filename) a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

function openReport(row) {
  if (!row.report_path) return
  triggerDownload(row.report_path, `${row.task_id}.docx`)
}

function previewReport(row) {
  if (!row.task_id) return
  window.open(`/reports/${row.task_id}.docx`, '_blank')
}

async function handleDelete(taskId) {
  try {
    await ElMessageBox.confirm('确定删除该报告?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return // user cancelled
  }
  try {
    await reportStore.deleteReport(taskId)
    ElMessage.success('报告已删除')
    await loadReports()
    await loadReportableTasks()
  } catch {
    ElMessage.error('删除失败')
  }
}

// ── 生成新报告 ──
const reportableTasks = ref([])
const selectedTaskId = ref('')
const selectedTask = ref(null)
const generating = ref(false)
const genProgress = ref(0)
const genPhase = ref('')
const genResult = ref('')
const genError = ref('')

const { start: startPolling, stop: stopPolling } = usePolling(async () => {
  const status = await reportStore.fetchReportStatus(selectedTaskId.value)
  genProgress.value = status?.progress || 0
  genPhase.value = status?.phase || ''

  if (!status || status.progress === -1) {
    genResult.value = 'fail'
    genError.value = status?.phase || '报告生成失败'
    generating.value = false
    return true
  }
  if (status.progress >= 100 || (!status.generating && status.has_report)) {
    genProgress.value = 100
    genPhase.value = ''
    genResult.value = 'ok'
    generating.value = false
    ElMessage.success('报告生成成功')
    await loadReports()
    await loadReportableTasks()
    return true
  }
  return false
}, 2000, 600000)

async function loadReportableTasks() {
  try {
    await taskStore.fetchTasks(1, 50, { status: 'success' })
    const successTasks = [...(taskStore.taskList || [])]

    const savedPage = page.value
    const savedPageSize = pageSize.value
    const res = await reportStore.fetchReports(1, 999)
    const reportedIds = new Set((res.items || []).map(r => r.task_id))
    reportableTasks.value = successTasks.filter(t => !reportedIds.has(t.task_id))
    await reportStore.fetchReports(savedPage, savedPageSize)
  } catch (e) {
    console.error('加载可报告任务失败', e)
  }
}

function onTaskSelect(taskId) {
  selectedTask.value = reportableTasks.value.find(t => t.task_id === taskId) || null
  genResult.value = ''
}

async function doGenerate() {
  if (!selectedTaskId.value) return
  stopPolling()
  generating.value = true
  genResult.value = ''
  genError.value = ''
  genProgress.value = 0
  genPhase.value = '正在启动...'

  try {
    await reportStore.generateReport(selectedTaskId.value)
    genPhase.value = '报告生成中...'
    startPolling()
  } catch (e) {
    genResult.value = 'fail'
    genError.value = e.response?.data?.messages || e.message || '报告生成失败'
    generating.value = false
  }
}

function previewGenerated() {
  window.open(`/reports/${selectedTaskId.value}.docx`, '_blank')
}
function downloadGenerated() {
  triggerDownload(`/reports/${selectedTaskId.value}.docx`, `${selectedTaskId.value}.docx`)
}

onMounted(async () => {
  await loadReports()
  await loadReportableTasks()
})
</script>

<style scoped>
.report-manage { max-width: 1500px; margin: 0 auto; }
.task-detail-card {
  margin-top: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
