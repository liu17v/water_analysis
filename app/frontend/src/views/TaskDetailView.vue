<template>
  <div class="task-detail">
    <el-page-header @back="$router.back()" content="任务详情" style="margin-bottom:16px" />

    <el-card v-if="task" class="info-card">
      <el-row :gutter="16" align="middle">
        <el-col :span="16">
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item label="任务ID" :span="2">{{ task.task_id }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusTagType(task.status)" size="small">{{ statusLabel(task.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="采样点数">{{ task.total_points }}</el-descriptions-item>
            <el-descriptions-item label="异常点数">{{ task.anomaly_count }}</el-descriptions-item>
            <el-descriptions-item label="进度">{{ task.progress }}%</el-descriptions-item>
          </el-descriptions>
        </el-col>
        <el-col :span="8" style="text-align:right">
          <el-button-group v-if="task.status === 'success'">
            <el-button size="small" @click="activeTab='anomalies'">
              <el-icon><WarningFilled /></el-icon> 查看异常
            </el-button>
            <el-button size="small" type="success" @click="$router.push(`/task/${task.task_id}/report`)">
              <el-icon><Document /></el-icon> 生成报告
            </el-button>
            <el-button size="small" type="info" @click="$router.push(`/task/${task.task_id}/anomalies`)">
              <el-icon><Download /></el-icon> 导出
            </el-button>
          </el-button-group>
        </el-col>
      </el-row>
      <el-progress v-if="task.status === 'processing'" :percentage="task.progress" :stroke-width="8" style="margin-top:16px" />
    </el-card>

    <div v-if="task?.status === 'processing'" style="text-align:center;margin:60px 0">
      <el-icon :size="48" class="is-loading"><Loading /></el-icon>
      <p style="margin-top:16px;color:#909399">任务处理中，请稍候... ({{ task.progress }}%)</p>
    </div>

    <template v-if="task?.status === 'success'">
      <el-tabs v-model="activeTab" type="border-card" style="margin-top:16px" @tab-change="onTabChange">
        <!-- 数据统计 -->
        <el-tab-pane label="数据统计" name="statistics">
          <div v-loading="statsLoading" class="tab-content">
            <el-row :gutter="16">
              <el-col :span="12" v-for="item in indicatorStats" :key="item.indicator" style="margin-bottom:12px">
                <el-card shadow="hover" class="indicator-card">
                  <template #header>
                    <div class="indicator-header">
                      <span class="indicator-name">{{ item.label }}</span>
                      <el-tag size="small" :type="item.anomaly_count > 0 ? 'danger' : 'success'">
                        {{ item.anomaly_count > 0 ? `异常 ${item.anomaly_count} 个` : '正常' }}
                      </el-tag>
                    </div>
                  </template>
                  <el-row :gutter="12">
                    <el-col :span="6"><div class="stat-item"><span class="stat-lbl">均值</span><span class="stat-num">{{ item.mean ?? '-' }}</span></div></el-col>
                    <el-col :span="6"><div class="stat-item"><span class="stat-lbl">标准差</span><span class="stat-num">{{ item.std ?? '-' }}</span></div></el-col>
                    <el-col :span="6"><div class="stat-item"><span class="stat-lbl">最小值</span><span class="stat-num">{{ item.min ?? '-' }}</span></div></el-col>
                    <el-col :span="6"><div class="stat-item"><span class="stat-lbl">最大值</span><span class="stat-num">{{ item.max ?? '-' }}</span></div></el-col>
                  </el-row>
                  <div class="indicator-footer">
                    <span>有效数据 {{ item.count }} 条</span>
                    <span> | 异常率 {{ item.anomaly_rate }}%</span>
                    <span v-if="item.unit"> | 单位: {{ item.unit }}</span>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 2D 等值线图 -->
        <el-tab-pane label="2D 等值线图" name="2d">
          <div class="viz-tab">
            <div class="viz-controls">
              <span class="ctrl-label">指标</span>
              <el-select v-model="contourIndicator" @change="reloadContour">
                <el-option v-for="o in indicatorOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
              <span class="ctrl-label">深度</span>
              <el-select v-model="contourDepth" @change="reloadContour">
                <el-option v-for="d in depthList" :key="d" :label="d + 'm'" :value="d" />
              </el-select>
              <el-tag size="small" effect="plain" style="margin-left:8px">Plotly 等值线</el-tag>
            </div>
            <div class="iframe-wrap">
              <iframe v-if="contourSrc" :key="contourKey" :src="contourSrc"
                frameborder="0" sandbox="allow-scripts allow-same-origin" class="viz-iframe" />
              <el-empty v-else description="加载中等值线图..." :image-size="60" />
            </div>
          </div>
        </el-tab-pane>

        <!-- 3D 体渲染 -->
        <el-tab-pane label="3D 体渲染" name="3d">
          <div class="viz-tab">
            <div class="viz-controls">
              <span class="ctrl-label">指标</span>
              <el-select v-model="volumeIndicator" @change="reloadVolume">
                <el-option v-for="o in indicatorOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
              <el-tag size="small" effect="plain" type="info" style="margin-left:8px">Plotly 3D Volume</el-tag>
            </div>
            <div class="iframe-wrap">
              <iframe v-if="volumeSrc" :key="volumeKey" :src="volumeSrc"
                frameborder="0" sandbox="allow-scripts allow-same-origin" class="viz-iframe" />
              <el-empty v-else description="加载中3D渲染..." :image-size="60" />
            </div>
          </div>
        </el-tab-pane>

        <!-- 深度剖面 -->
        <el-tab-pane label="深度剖面" name="depth">
          <div class="viz-tab">
            <div class="viz-controls">
              <span class="ctrl-label">指标</span>
              <el-select v-model="profileIndicator" @change="reloadProfile">
                <el-option v-for="o in indicatorOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
              <el-tag size="small" effect="plain" type="success" style="margin-left:8px">深度剖面分析</el-tag>
            </div>
            <div class="iframe-wrap">
              <iframe v-if="profileSrc" :key="profileKey" :src="profileSrc"
                frameborder="0" sandbox="allow-scripts allow-same-origin" class="viz-iframe" />
              <el-empty v-else description="加载中深度剖面..." :image-size="60" />
            </div>
          </div>
        </el-tab-pane>

        <!-- 原始数据 -->
        <el-tab-pane label="原始数据" name="raw">
          <div class="tab-content">
            <el-table :data="rawRows" stripe v-loading="rawLoading" max-height="500" border size="small">
              <el-table-column v-for="(label, idx) in rawFieldLabels" :key="rawFields[idx]"
                :prop="rawFields[idx]" :label="label" min-width="100" show-overflow-tooltip>
                <template #default="{ row }">
                  <span :class="{ 'suspicious-cell': row.suspicious && rawFields[idx] !== 'depth_m' }">
                    {{ row[rawFields[idx]] ?? '-' }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
            <el-pagination
              v-if="rawTotal > rawPageSize"
              style="margin-top:12px; justify-content:flex-end"
              layout="total, prev, pager, next"
              :total="rawTotal" :page-size="rawPageSize"
              v-model:current-page="rawPage"
              @current-change="loadRawData"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { Loading, WarningFilled, Document, Download } from '@element-plus/icons-vue'
import api from '../api'

const route = useRoute()
const task = ref(null)
const activeTab = ref('statistics')
const depthList = ref([])
let pollTimer = null

// Indicator options
const indicatorOptions = [
  { label: '叶绿素 (Chl)', value: 'chlorophyll' },
  { label: '溶解氧 (DO)', value: 'dissolved_oxygen' },
  { label: '水温 (Temp)', value: 'temperature' },
  { label: 'pH', value: 'ph' },
  { label: '浊度 (Turb)', value: 'turbidity' },
]

// 2D Contour
const contourIndicator = ref('chlorophyll')
const contourDepth = ref(1)
const contourKey = ref(0)
const contourSrc = computed(() => {
  if (!task.value?.task_id) return ''
  return `/api/task/${task.value.task_id}/contour_html?indicator=${contourIndicator.value}&depth=${contourDepth.value}`
})
function reloadContour() { contourKey.value++ }

// 3D Volume
const volumeIndicator = ref('chlorophyll')
const volumeKey = ref(0)
const volumeSrc = computed(() => {
  if (!task.value?.task_id) return ''
  return `/3d/${task.value.task_id}_${volumeIndicator.value}.html`
})
function reloadVolume() { volumeKey.value++ }

// Depth Profile
const profileIndicator = ref('chlorophyll')
const profileKey = ref(0)
const profileSrc = computed(() => {
  if (!task.value?.task_id) return ''
  return `/api/task/${task.value.task_id}/depth_profile_html?indicator=${profileIndicator.value}`
})
function reloadProfile() { profileKey.value++ }

// Statistics
const statsLoading = ref(false)
const indicatorStats = ref([])

// Raw data
const rawRows = ref([])
const rawFields = ref([])
const rawFieldLabels = ref([])
const rawTotal = ref(0)
const rawPage = ref(1)
const rawPageSize = ref(50)
const rawLoading = ref(false)

function statusLabel(s) {
  const map = { pending: '待处理', processing: '处理中', success: '已完成', failed: '失败' }
  return map[s] || s
}
function statusTagType(s) {
  const map = { success: 'success', processing: 'warning', failed: 'danger', pending: 'info' }
  return map[s] || 'info'
}

async function pollStatus() {
  try {
    const res = await api.getTaskStatus(route.params.id)
    task.value = res
    if (res.status === 'processing') {
      pollTimer = setTimeout(pollStatus, 2000)
    } else {
      clearTimeout(pollTimer)
      if (res.status === 'success') {
        loadDepths()
      }
    }
  } catch { clearTimeout(pollTimer) }
}

async function loadDepths() {
  try {
    const res = await api.getVisualization(route.params.id, 'chlorophyll', 1)
    depthList.value = res.depths || []
    if (depthList.value.length) {
      contourDepth.value = depthList.value[0]
    }
  } catch {}
}

// Statistics
async function loadStatistics() {
  if (indicatorStats.value.length) return
  statsLoading.value = true
  try {
    const res = await api.getStatistics(route.params.id)
    const indicators = res.indicators || {}
    indicatorStats.value = Object.values(indicators)
  } finally { statsLoading.value = false }
}

// Raw data
async function loadRawData() {
  rawLoading.value = true
  try {
    const res = await api.getRawData(route.params.id, rawPage.value, rawPageSize.value)
    rawRows.value = res.items || []
    rawFields.value = res.fields || []
    rawFieldLabels.value = res.field_labels || []
    rawTotal.value = res.total || 0
  } finally { rawLoading.value = false }
}

// Tab switching
function onTabChange(name) {
  if (name === 'statistics') loadStatistics()
  else if (name === 'raw') loadRawData()
}

onMounted(() => pollStatus())
onUnmounted(() => clearTimeout(pollTimer))
</script>

<style scoped>
.task-detail { max-width: 1400px; margin: 0 auto; padding: 16px; }
.info-card { margin-bottom: 16px; }
.tab-content { padding: 8px 0; }

/* Viz tabs - consistent layout */
.viz-tab { background: #fff; border-radius: 8px; overflow: hidden; }
.viz-controls {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px; background: #fafafa; border-bottom: 1px solid #ebeef5;
}
.ctrl-label { font-size: 13px; color: #606266; font-weight: 500; }
.iframe-wrap { width: 100%; height: 650px; }
.viz-iframe { width: 100%; height: 100%; border: none; }

/* Indicator cards */
.indicator-card { margin-bottom: 4px; }
.indicator-header { display: flex; justify-content: space-between; align-items: center; }
.indicator-name { font-weight: 600; font-size: 15px; }
.stat-item { text-align: center; padding: 4px 0; }
.stat-lbl { display: block; font-size: 12px; color: #909399; }
.stat-num { display: block; font-size: 16px; font-weight: 600; color: #303133; margin-top: 2px; }
.indicator-footer { margin-top: 10px; font-size: 12px; color: #909399; }

/* Raw data */
.suspicious-cell { color: #f56c6c; font-weight: 600; }
</style>
