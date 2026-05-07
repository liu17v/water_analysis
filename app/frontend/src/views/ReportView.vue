<template>
  <div class="report-page">
    <!-- 左侧边栏 -->
    <div class="report-sidebar">
      <div class="sidebar-section">
        <h4><el-icon><InfoFilled /></el-icon> 任务信息</h4>
        <div class="info-item" v-if="taskInfo">
          <span class="info-label">任务ID</span>
          <span class="info-value" :title="taskInfo.task_id">{{ taskInfo.task_id?.substring(0, 8) }}...</span>
        </div>
        <div class="info-item" v-if="taskInfo">
          <span class="info-label">水库名称</span>
          <span class="info-value">{{ taskInfo.reservoir_name || '未知' }}</span>
        </div>
        <div class="info-item" v-if="taskInfo">
          <span class="info-label">采样点数</span>
          <span class="info-value">{{ taskInfo.total_points }}</span>
        </div>
        <div class="info-item" v-if="taskInfo">
          <span class="info-label">异常点数</span>
          <span class="info-value">{{ taskInfo.anomaly_count }}</span>
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
          <p>报告文件以 <b>.docx / .pdf</b> 格式存储在本地磁盘</p>
          <p>Milvus 存储 <b>13维特征向量</b> 用于相似案例检索，不存储报告文件</p>
        </div>
        <div v-if="reportUrl" class="file-info">
          <el-divider style="margin:12px 0" />
          <p class="file-path">📄 {{ reportUrl }}</p>
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
        <el-button size="small" style="width:100%;margin-top:8px" @click="searchSimilar" :loading="similarLoading">
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
          <el-button
            type="primary" size="large" @click="generateReport"
            :loading="generating" :disabled="generated"
          >
            <el-icon><Document /></el-icon>
            {{ generated ? '报告已生成' : generating ? '正在生成...' : '生成分析报告' }}
          </el-button>
        </div>

        <div v-if="generating" style="margin-top:16px">
          <el-progress :percentage="reportProgress" :stroke-width="14" :text-inside="true">
            <template #default="{ percentage }">
              <span class="progress-text">{{ percentage }}%</span>
            </template>
          </el-progress>
          <p style="text-align:center;margin-top:8px;color:#909399;font-size:13px">
            <el-icon class="is-loading"><Loading /></el-icon>
            正在生成报告，请稍候...
          </p>
        </div>

        <div v-if="reportUrl" style="margin-top:20px">
          <el-result icon="success" title="报告生成成功" sub-title="报告已保存至本地文件系统">
            <template #extra>
              <el-button type="primary" @click="openReport">预览报告</el-button>
              <el-button @click="downloadReport">下载报告</el-button>
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
          <el-button size="small" @click="searchSimilar" :loading="similarLoading" text type="primary">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </template>

        <div v-if="similarLoading" style="text-align:center;padding:40px">
          <el-icon :size="28" class="is-loading"><Loading /></el-icon>
          <p style="margin-top:8px;color:#909399">正在 Milvus 向量检索...</p>
        </div>

        <div v-else-if="similarTasks.length === 0">
          <el-empty description="暂无相似历史案例" :image-size="80">
            <template #description>
              <span>Milvus 向量库中暂未检索到相似案例</span>
              <br /><small style="color:#c0c4cc">上传更多数据并完成分析后，系统将自动建立案例特征库</small>
            </template>
          </el-empty>
        </div>

        <div v-else class="similar-list">
          <div v-for="(item, idx) in similarTasks" :key="idx" class="similar-card">
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
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  Document, Loading, Refresh, InfoFilled, FolderOpened,
  Connection, DataAnalysis, WarningFilled, FolderChecked,
} from '@element-plus/icons-vue'
import api from '../api'

const route = useRoute()
const taskId = route.params.id
const generating = ref(false)
const generated = ref(false)
const reportUrl = ref('')
const reportProgress = ref(0)
const error = ref('')
const similarTasks = ref([])
const similarLoading = ref(false)
const taskInfo = reactive({})
let progressTimer = null

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

async function loadTaskInfo() {
  try {
    const res = await api.getTaskStatus(taskId)
    Object.assign(taskInfo, res)
  } catch {}
}

async function searchSimilar() {
  similarLoading.value = true
  try {
    const res = await api.searchSimilar(taskId)
    similarTasks.value = res.similar_tasks || res.data?.similar_tasks || []
  } finally {
    similarLoading.value = false
  }
}

async function generateReport() {
  generating.value = true
  error.value = ''
  reportProgress.value = 0
  progressTimer = setInterval(() => {
    if (reportProgress.value < 90) reportProgress.value += Math.random() * 8 + 2
  }, 500)
  try {
    const res = await api.generateReport(taskId)
    reportProgress.value = 100
    reportUrl.value = res.report_url || res.data?.report_url || ''
    generated.value = true
  } catch (e) {
    error.value = e.response?.data?.messages || '报告生成失败，请稍后重试'
  } finally {
    clearInterval(progressTimer)
    generating.value = false
  }
}

function openReport() {
  if (reportUrl.value) window.open(reportUrl.value, '_blank')
}
function downloadReport() {
  if (reportUrl.value) {
    const a = document.createElement('a')
    a.href = reportUrl.value
    a.download = ''
    a.click()
  }
}

onMounted(() => {
  loadTaskInfo()
  searchSimilar()
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
