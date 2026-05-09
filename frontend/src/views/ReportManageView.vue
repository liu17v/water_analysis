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
            :loading="tasksLoading"
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
            <el-button type="primary" @click="previewGenerated">预览 PDF</el-button>
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

      <el-table :data="rows" v-loading="loading" stripe border size="small" max-height="500">
        <el-table-column prop="task_id" label="任务ID" min-width="200" show-overflow-tooltip />
        <el-table-column prop="reservoir_name" label="水库名称" width="140" />
        <el-table-column prop="total_points" label="采样点" width="80" />
        <el-table-column prop="anomaly_count" label="异常点" width="80" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
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
            <el-popconfirm title="确定删除该报告?" @confirm="handleDelete(row.task_id)">
              <template #reference>
                <el-button size="small" type="danger" text>
                  <el-icon><Delete /></el-icon> 删除
                </el-button>
              </template>
            </el-popconfirm>
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
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { View, Download, Delete, Document, Loading, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const router = useRouter()

// ── 报告列表 ──
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

async function loadReports() {
  loading.value = true
  try {
    const res = await api.getReports(page.value, pageSize.value)
    rows.value = res.items || []
    total.value = res.total || 0
  } finally { loading.value = false }
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
  window.open(`/reports/${row.task_id}.pdf`, '_blank')
}

async function handleDelete(taskId) {
  try {
    await api.deleteReport(taskId)
    ElMessage.success('报告已删除')
    loadReports()
    loadReportableTasks()
  } catch { ElMessage.error('删除失败') }
}

// ── 生成新报告 ──
const reportableTasks = ref([])
const tasksLoading = ref(false)
const selectedTaskId = ref('')
const selectedTask = ref(null)
const generating = ref(false)
const genProgress = ref(0)
const genPhase = ref('')
const genResult = ref('')
const genError = ref('')
let genProgressTimer = null
let genPollCount = 0
const GEN_MAX_POLLS = 300  // 10 minutes at 2s interval

async function loadReportableTasks() {
  tasksLoading.value = true
  try {
    // 获取已成功的任务
    const res = await api.getTasks(1, 50, { status: 'success' })
    const successTasks = res.items || []
    // 获取已有报告的任务ID
    const reportRes = await api.getReports(1, 50)
    const reportedIds = new Set((reportRes.items || []).map(r => r.task_id))
    // 排除已有报告的任务
    reportableTasks.value = successTasks.filter(t => !reportedIds.has(t.task_id))
  } finally { tasksLoading.value = false }
}

function onTaskSelect(taskId) {
  selectedTask.value = reportableTasks.value.find(t => t.task_id === taskId) || null
  genResult.value = ''
}

async function doGenerate() {
  if (!selectedTaskId.value) return
  generating.value = true
  genResult.value = ''
  genError.value = ''
  genProgress.value = 0
  genPhase.value = '正在启动...'

  try {
    // 触发后台生成（立即返回）
    const res = await api.generateReport(selectedTaskId.value)
    if (res.status !== 'started') {
      throw new Error('生成启动失败')
    }
    // 轮询真实进度
    genPollCount = 0
    genProgressTimer = setInterval(pollProgress, 2000)
  } catch (e) {
    genResult.value = 'fail'
    genError.value = e.response?.data?.messages || e.message || '报告生成失败'
    generating.value = false
  }
}

async function pollProgress() {
  genPollCount++
  if (genPollCount > GEN_MAX_POLLS) {
    clearInterval(genProgressTimer)
    genResult.value = 'fail'
    genError.value = '报告生成超时，请检查服务器状态后重试'
    generating.value = false
    return
  }
  try {
    const status = await api.getReportStatus(selectedTaskId.value)
    genProgress.value = status.progress || 0
    genPhase.value = status.phase || ''

    if (status.progress === -1) {
      clearInterval(genProgressTimer)
      genResult.value = 'fail'
      genError.value = status.phase || '报告生成失败'
      generating.value = false
      return
    }
    if (status.progress >= 100) {
      clearInterval(genProgressTimer)
      genProgress.value = 100
      genPhase.value = ''
      genResult.value = 'ok'
      generating.value = false
      ElMessage.success('报告生成成功')
      loadReports()
      loadReportableTasks()
    }
  } catch (e) {
    clearInterval(genProgressTimer)
    genResult.value = 'fail'
    genError.value = e.response?.data?.messages || e.message || '查询进度失败'
    generating.value = false
  }
}

function previewGenerated() {
  window.open(`/reports/${selectedTaskId.value}.pdf`, '_blank')
}
function downloadGenerated() {
  triggerDownload(`/reports/${selectedTaskId.value}.docx`, `${selectedTaskId.value}.docx`)
}

onMounted(() => {
  loadReports()
  loadReportableTasks()
})
onUnmounted(() => {
  clearInterval(genProgressTimer)
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
