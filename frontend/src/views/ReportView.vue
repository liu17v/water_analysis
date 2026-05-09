<template>
  <div class="report-page">
    <!-- 左侧边栏 -->
    <div class="report-sidebar">
      <div class="sidebar-section">
        <h4><el-icon><InfoFilled /></el-icon> 任务信息</h4>
        <div class="info-item" v-if="taskStore.currentStatus">
          <span class="info-label">任务ID</span>
          <span class="info-value" :title="taskStore.currentStatus.task_id">{{ taskStore.currentStatus.task_id?.substring(0, 8) }}...</span>
        </div>
        <div class="info-item" v-if="taskStore.currentStatus">
          <span class="info-label">水库名称</span>
          <span class="info-value">{{ taskStore.currentStatus.reservoir_name || '未知' }}</span>
        </div>
        <div class="info-item" v-if="taskStore.currentStatus">
          <span class="info-label">采样点数</span>
          <span class="info-value">{{ taskStore.currentStatus.total_points }}</span>
        </div>
        <div class="info-item" v-if="taskStore.currentStatus">
          <span class="info-label">异常点数</span>
          <span class="info-value">{{ taskStore.currentStatus.anomaly_count }}</span>
        </div>
      </div>

      <div class="sidebar-section">
        <h4><el-icon><FolderOpened /></el-icon> 报告存储</h4>
        <div class="storage-info">
          <div class="storage-item">
            <el-tag size="small" type="success">本地文件</el-tag>
            <span class="storage-path">app/data/reports/</span>
          </div>
          <div class="storage-item">
            <el-tag size="small" type="warning">Milvus</el-tag>
            <span class="storage-desc">特征向量检索</span>
          </div>
        </div>
        <div class="storage-note">
          <p>报告文件以 <b>.docx</b> 格式存储在本地磁盘</p>
          <p>Milvus 存储 <b>13维特征向量</b> 用于相似案例检索，不存储报告文件</p>
        </div>
        <div v-if="generated" class="file-info">
          <el-divider style="margin:12px 0" />
          <p class="file-path">{{ reportUrl }}</p>
        </div>
      </div>

      <div class="sidebar-section">
        <h4><el-icon><Connection /></el-icon> 快捷操作</h4>
        <el-button size="small" style="width:100%" @click="$router.push(`/task/${taskId}`)">
          查看任务详情
        </el-button>
        <el-button size="small" style="width:100%;margin-top:8px" @click="$router.push(`/task/${taskId}/anomalies`)">
          查看异常列表
        </el-button>
        <el-button size="small" style="width:100%;margin-top:8px" @click="searchSimilar" :loading="reportStore.loading.similar">
          刷新相似案例
        </el-button>
      </div>
    </div>

    <!-- 主内容 -->
    <div class="report-main">
      <el-page-header @back="$router.back()" content="智能报告生成" style="margin-bottom:16px" />

      <!-- 生成流程 -->
      <el-card header="报告生成流程" style="margin-bottom:16px">
        <el-steps :active="generated ? 4 : generating ? 3 : reportProgress > 0 ? 1 : 0" align-center>
          <el-step title="数据统计" description="提取水质指标统计特征">
            <template #icon><el-icon><DataAnalysis /></el-icon></template>
          </el-step>
          <el-step title="异常检测" description="统计阈值 + 孤立森林">
            <template #icon><el-icon><WarningFilled /></el-icon></template>
          </el-step>
          <el-step title="大模型生成" description="调用 DeepSeek 生成专业报告">
            <template #icon><el-icon><Document /></el-icon></template>
          </el-step>
          <el-step title="报告存储" description="保存至本地文件系统">
            <template #icon><el-icon><FolderChecked /></el-icon></template>
          </el-step>
        </el-steps>
      </el-card>

      <!-- 生成区域 -->
      <el-card header="生成分析报告" style="margin-bottom:16px">
        <div style="text-align:center;padding:16px 0">
          <div style="margin-bottom:16px">
            <span style="margin-right:12px;font-size:14px;color:#606266">报告模板:</span>
            <el-radio-group v-model="reportTemplate" :disabled="generating || generated">
              <el-radio label="standard">标准版 - 完整统计 + 异常分析</el-radio>
              <el-radio label="brief">简洁版 - 关键指标汇总</el-radio>
            </el-radio-group>
          </div>
          <el-button
            type="primary" size="large" @click="generateReport"
            :loading="generating" :disabled="generated"
          >
            <el-icon><Document /></el-icon>
            {{ generated ? '报告已生成' : generating ? '正在生成...' : '生成分析报告' }}
          </el-button>
        </div>

        <div v-if="generating" style="margin-top:16px">
          <el-progress :percentage="+reportProgress.toFixed(2)" :stroke-width="14" :text-inside="true" />
          <p style="text-align:center;margin-top:8px;color:#606266;font-size:13px">
            <el-icon class="is-loading"><Loading /></el-icon>
            {{ progressPhase }}
            <span v-if="elapsedSeconds > 0" style="color:#909399;margin-left:4px">({{ elapsedSeconds }}s)</span>
          </p>
        </div>

        <div v-if="generated" style="margin-top:20px">
          <el-result icon="success" title="报告生成成功" sub-title="报告已保存，可选择预览或下载">
            <template #extra>
              <el-button type="success" @click="downloadDoc">
                <el-icon><Download /></el-icon> 下载 DOCX
              </el-button>
            </template>
          </el-result>
        </div>

        <div v-if="error" style="margin-top:16px">
          <el-alert :title="error" type="error" show-icon :closable="false" />
        </div>
      </el-card>

      <!-- 相似案例 -->
      <el-card header="相似历史案例 (Milvus 检索)">
        <template #extra>
          <el-button size="small" @click="searchSimilar" :loading="reportStore.loading.similar" text type="primary">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </template>

        <div v-if="reportStore.loading.similar" style="text-align:center;padding:40px">
          <el-icon :size="28" class="is-loading"><Loading /></el-icon>
          <p style="margin-top:8px;color:#909399">正在 Milvus 向量检索...</p>
        </div>

        <div v-else-if="similarTaskList.length === 0">
          <el-empty description="暂无相似历史案例" :image-size="80">
            <template #description>
              <span>Milvus 向量库中暂未检索到相似案例</span>
              <br /><small style="color:#c0c4cc">上传更多数据并完成分析后，系统将自动建立案例特征库</small>
            </template>
          </el-empty>
        </div>

        <div v-else class="similar-list">
          <div v-for="(item, idx) in similarTaskList" :key="idx" class="similar-card">
            <div class="similar-rank" :style="{background: simColor(item.similarity)}">#{{ idx + 1 }}</div>
            <div class="similar-body">
              <div class="similar-top">
                <span class="similar-name">{{ item.reservoir || '未知水库' }}</span>
                <el-tag size="small" :type="simType(item.similarity)">
                  {{ (item.similarity * 100).toFixed(1) }}%
                </el-tag>
              </div>
              <div class="similar-bar">
                <div class="similar-bar-fill" :style="{width:(item.similarity*100)+'%', background:simColor(item.similarity)}"></div>
              </div>
              <div class="similar-meta">
                <span v-if="item.task_id">任务: {{ item.task_id?.substring(0, 8) }}...</span>
                <span v-if="item.date">日期: {{ item.date }}</span>
              </div>
              <el-button
                v-if="item.task_id"
                size="small" text type="primary"
                @click="$router.push(`/task/${item.task_id}`)"
              >查看详情 →</el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTaskStore } from '../stores/task'
import { useReportStore } from '../stores/report'
import { usePolling } from '../composables/usePolling'
import { useStatus } from '../composables/useStatus'
import { ElMessage } from 'element-plus'
import {
  Document, Loading, Refresh, InfoFilled, FolderOpened,
  Connection, DataAnalysis, WarningFilled, FolderChecked, Download,
} from '@element-plus/icons-vue'

const route = useRoute()
const taskId = route.params.id
const taskStore = useTaskStore()
const reportStore = useReportStore()
const { statusLabel } = useStatus()

// State
const generating = ref(false)
const generated = ref(false)
const reportProgress = ref(0)
const progressPhase = ref('')
const error = ref('')
const reportTemplate = ref('standard')

// Computed
const reportUrl = computed(() => `/reports/${taskId}.docx`)

// Normalize similar tasks from store response
const similarTaskList = computed(() => {
  const raw = reportStore.similarTasks
  if (!raw) return []
  if (Array.isArray(raw)) return raw
  if (raw.similar_tasks) return raw.similar_tasks
  if (raw.data?.similar_tasks) return raw.data?.similar_tasks
  return []
})

// Helper functions for similarity display
function simType(v) {
  if (v >= 0.8) return 'danger'
  if (v >= 0.6) return 'warning'
  return 'success'
}
function simColor(v) {
  if (v >= 0.8) return '#f56c6c'
  if (v >= 0.6) return '#e6a23c'
  return '#67c23a'
}

// Task status polling - fetches task info, auto-stops when no longer processing
const taskPolling = usePolling(
  () => taskStore.pollTaskStatus(taskId),
  2000
)

// Report generation polling
const reportPolling = usePolling(
  async () => {
    const status = await reportStore.fetchReportStatus(taskId)
    if (!status) return false

    reportProgress.value = status.progress || 0
    progressPhase.value = status.phase || ''

    if (status.progress === -1) {
      error.value = status.phase || '报告生成失败'
      generating.value = false
      return true
    }

    if (status.progress >= 100 || (!status.generating && status.has_report)) {
      reportProgress.value = 100
      progressPhase.value = '报告生成完成！'
      generated.value = true
      generating.value = false
      return true
    }

    if (!status.generating && !status.has_report && reportPolling.elapsed.value > 8000) {
      error.value = '报告生成失败，请查看服务器日志后重试'
      generating.value = false
      return true
    }

    return false
  },
  2000,
  600000 // 10 min max
)

const elapsedSeconds = computed(() => Math.floor(reportPolling.elapsed.value / 1000))

async function loadTaskInfo() {
  await taskStore.pollTaskStatus(taskId)
}

async function searchSimilar() {
  try {
    await reportStore.searchSimilar(taskId)
  } catch {
    // error handled by store
  }
}

async function generateReport() {
  generating.value = true
  error.value = ''
  reportProgress.value = 0
  progressPhase.value = '正在启动...'

  try {
    await reportStore.generateReport(taskId)
    reportPolling.start()
  } catch (e) {
    error.value = reportStore.error.generate || e.message || '报告生成失败'
    generating.value = false
  }
}

function triggerDownload(url, filename) {
  const a = document.createElement('a')
  a.href = url
  if (filename) a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

function downloadDoc() {
  triggerDownload(reportUrl.value, `${taskId}.docx`)
}

onMounted(() => {
  taskPolling.start()
  loadTaskInfo()
  searchSimilar()
})

onUnmounted(() => {
  taskPolling.stop()
  reportPolling.stop()
})
</script>

<style scoped>
.report-page { display: flex; gap: 16px; max-width: 1500px; margin: 0 auto; padding: 16px; }

/* Left sidebar */
.report-sidebar {
  width: 260px; flex-shrink: 0;
  display: flex; flex-direction: column; gap: 16px;
}
.sidebar-section {
  background: #fff; border-radius: 8px; padding: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.sidebar-section h4 {
  font-size: 14px; color: #303133; margin-bottom: 12px;
  display: flex; align-items: center; gap: 6px;
  padding-bottom: 8px; border-bottom: 1px solid #ebeef5;
}
.info-item { display: flex; justify-content: space-between; padding: 4px 0; font-size: 13px; }
.info-label { color: #909399; }
.info-value { color: #303133; font-weight: 500; }
.storage-info { display: flex; flex-direction: column; gap: 8px; }
.storage-item { display: flex; align-items: center; gap: 8px; }
.storage-path { font-size: 12px; color: #606266; font-family: monospace; }
.storage-desc { font-size: 12px; color: #909399; }
.storage-note { margin-top: 8px; padding: 8px; background: #f5f7fa; border-radius: 6px; }
.storage-note p { font-size: 12px; color: #606266; line-height: 1.6; margin: 0; }
.file-info { margin-top: 4px; }
.file-path { font-size: 12px; color: #409eff; word-break: break-all; margin: 0; }

/* Main content */
.report-main { flex: 1; min-width: 0; }

.progress-text { font-size: 12px; }

/* Similar cases */
.similar-list { display: flex; flex-direction: column; }
.similar-card {
  display: flex; gap: 12px; padding: 14px 12px;
  border-bottom: 1px solid #ebeef5; align-items: flex-start;
}
.similar-card:last-child { border-bottom: none; }
.similar-rank {
  width: 28px; height: 28px; border-radius: 50%;
  color: #fff; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.similar-body { flex: 1; }
.similar-top { display: flex; justify-content: space-between; align-items: center; }
.similar-name { font-weight: 600; font-size: 15px; }
.similar-bar { height: 6px; background: #ebeef5; border-radius: 3px; margin-top: 6px; overflow: hidden; }
.similar-bar-fill { height: 100%; border-radius: 3px; transition: width 0.6s; }
.similar-meta { margin-top: 6px; font-size: 12px; color: #909399; display: flex; gap: 12px; }

@media (max-width: 900px) {
  .report-page { flex-direction: column; }
  .report-sidebar { width: 100%; flex-direction: row; flex-wrap: wrap; }
  .sidebar-section { flex: 1; min-width: 200px; }
}
</style>
