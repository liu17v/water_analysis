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

        <el-tab-pane label="2D 等值线图" name="2d">
          <ContourPanel :taskId="task.task_id" :depths="depthList" ref="contourRef" />
        </el-tab-pane>

        <el-tab-pane label="3D 体渲染" name="3d">
          <PointCloudFrame :taskId="task.task_id" />
        </el-tab-pane>

        <el-tab-pane label="深度剖面" name="depth">
          <div class="tab-content">
            <div class="controls-row">
              <el-select v-model="profileIndicator" @change="loadDepthProfile">
                <el-option label="叶绿素" value="chlorophyll" />
                <el-option label="溶解氧" value="dissolved_oxygen" />
                <el-option label="水温" value="temperature" />
                <el-option label="pH" value="ph" />
                <el-option label="浊度" value="turbidity" />
              </el-select>
              <span class="profile-title">{{ profileLabel }}</span>
            </div>
            <div v-if="profileData.length" class="profile-chart">
              <div class="profile-y"><span v-for="d in profileData" :key="d.depth">{{ d.depth }}m</span></div>
              <div class="profile-area">
                <div v-for="(d, i) in profileData" :key="d.depth" class="profile-row" :style="{left: depthPos(i)}">
                  <div class="profile-boxplot">
                    <div class="bp-bar" :style="{height: barHeight(d), marginTop: barMarginTop(d)}"></div>
                    <div class="bp-range" :style="{height: rangeHeight(d), top: rangeTop(d)}"></div>
                    <div class="bp-mean" :style="{bottom: meanPos(d)}"></div>
                  </div>
                  <span class="bp-val">{{ d.mean?.toFixed(2) }}</span>
                </div>
                <div class="profile-axis">
                  <span v-for="tick in yTicks" :key="tick" :style="{bottom: tickPos(tick)+'%'}">{{ tick }}</span>
                </div>
              </div>
            </div>
            <el-empty v-else description="选择指标查看深度剖面" :image-size="80" />
          </div>
        </el-tab-pane>

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
              :total="rawTotal"
              :page-size="rawPageSize"
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
import ContourPanel from '../components/ContourPanel.vue'
import PointCloudFrame from '../components/PointCloudFrame.vue'
import api from '../api'

const route = useRoute()
const task = ref(null)
const activeTab = ref('statistics')
const depthList = ref([])
const contourRef = ref(null)
let pollTimer = null

// Statistics
const statsLoading = ref(false)
const indicatorStats = ref([])

// Depth profile
const profileIndicator = ref('chlorophyll')
const profileData = ref([])
const profileLabel = ref('')

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
    depthList.value = res.depths || (res.data?.depths || [])
  } catch {}
}

// ----- Statistics -----
async function loadStatistics() {
  if (indicatorStats.value.length) return
  statsLoading.value = true
  try {
    const res = await api.getStatistics(route.params.id)
    const indicators = res.indicators || res.data?.indicators || {}
    indicatorStats.value = Object.values(indicators)
  } finally { statsLoading.value = false }
}

// ----- Depth profile -----
async function loadDepthProfile() {
  try {
    const res = await api.getDepthProfile(route.params.id, profileIndicator.value)
    const data = res.data || res
    profileData.value = data.profile || []
    profileLabel.value = data.label ? `${data.label}${data.unit ? ' (' + data.unit + ')' : ''}` : ''
  } catch { profileData.value = [] }
}

const yTicks = computed(() => {
  if (!profileData.value.length) return []
  const allVals = profileData.value.flatMap(d => [d.min, d.max, d.mean])
  const lo = Math.min(...allVals), hi = Math.max(...allVals)
  const step = (hi - lo) / 5
  return Array.from({ length: 6 }, (_, i) => +(lo + step * i).toFixed(2))
})

function depthPos(i) { return ((i + 0.5) / profileData.value.length * 100) + '%' }
function tickPos(v) {
  const allVals = profileData.value.flatMap(d => [d.min, d.max])
  const lo = Math.min(...allVals), hi = Math.max(...allVals)
  if (hi === lo) return 0
  return ((v - lo) / (hi - lo) * 100)
}
function barHeight(d) {
  const allVals = profileData.value.flatMap(d => [d.min, d.max])
  const lo = Math.min(...allVals), hi = Math.max(...allVals)
  if (hi === lo) return '20px'
  return ((d.mean - lo) / (hi - lo) * 100) + '%'
}
function barMarginTop(d) {
  const allVals = profileData.value.flatMap(d => [d.min, d.max])
  const lo = Math.min(...allVals), hi = Math.max(...allVals)
  if (hi === lo) return '0'
  return ((hi - d.mean) / (hi - lo) * 100) + '%'
}
function rangeHeight(d) {
  const allVals = profileData.value.flatMap(d => [d.min, d.max])
  const lo = Math.min(...allVals), hi = Math.max(...allVals)
  if (hi === lo) return '20px'
  return ((d.max - d.min) / (hi - lo) * 100) + '%'
}
function rangeTop(d) {
  const allVals = profileData.value.flatMap(d => [d.min, d.max])
  const lo = Math.min(...allVals), hi = Math.max(...allVals)
  if (hi === lo) return '0'
  return ((hi - d.max) / (hi - lo) * 100) + '%'
}
function meanPos(d) {
  const allVals = profileData.value.flatMap(d => [d.min, d.max])
  const lo = Math.min(...allVals), hi = Math.max(...allVals)
  if (hi === lo) return '50%'
  return ((d.mean - lo) / (hi - lo) * 100) + '%'
}

// ----- Raw data -----
async function loadRawData() {
  rawLoading.value = true
  try {
    const res = await api.getRawData(route.params.id, rawPage.value, rawPageSize.value)
    rawRows.value = res.items || res.data?.items || []
    rawFields.value = res.fields || res.data?.fields || []
    rawFieldLabels.value = res.field_labels || res.data?.field_labels || []
    rawTotal.value = res.total || res.data?.total || 0
  } finally { rawLoading.value = false }
}

// ----- Tab switching -----
function onTabChange(name) {
  if (name === 'statistics') loadStatistics()
  else if (name === 'depth') loadDepthProfile()
  else if (name === 'raw') loadRawData()
}

onMounted(() => pollStatus())
onUnmounted(() => clearTimeout(pollTimer))
</script>

<style scoped>
.task-detail { max-width: 1400px; margin: 0 auto; padding: 16px; }
.info-card { margin-bottom: 16px; }
.tab-content { padding: 8px 0; }

/* Indicator cards */
.indicator-card { margin-bottom: 4px; }
.indicator-header { display: flex; justify-content: space-between; align-items: center; }
.indicator-name { font-weight: 600; font-size: 15px; }
.stat-item { text-align: center; padding: 4px 0; }
.stat-lbl { display: block; font-size: 12px; color: #909399; }
.stat-num { display: block; font-size: 16px; font-weight: 600; color: #303133; margin-top: 2px; }
.indicator-footer { margin-top: 10px; font-size: 12px; color: #909399; }

/* Depth profile chart */
.controls-row { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.profile-title { font-size: 14px; color: #606266; font-weight: 600; }
.profile-chart { display: flex; height: 350px; position: relative; }
.profile-y { display: flex; flex-direction: column; justify-content: space-around; width: 48px; font-size: 11px; color: #909399; }
.profile-area { flex: 1; position: relative; border-left: 2px solid #dcdfe6; border-bottom: 2px solid #dcdfe6; margin-left: 8px; margin-bottom: 24px; }
.profile-row { position: absolute; bottom: 0; width: 40px; text-align: center; transform: translateX(-50%); }
.profile-boxplot { position: absolute; bottom: 0; width: 100%; height: 100%; }
.bp-bar { width: 12px; background: #409eff; border-radius: 3px; margin: 0 auto; }
.bp-range { width: 3px; background: #909399; position: absolute; left: 50%; transform: translateX(-50%); border-radius: 2px; }
.bp-mean { width: 8px; height: 3px; background: #f56c6c; position: absolute; left: 50%; transform: translateX(-50%); }
.bp-val { display: block; font-size: 10px; color: #606266; margin-top: 4px; }
.profile-axis { position: absolute; right: 0; top: 0; bottom: 0; width: 52px; }
.profile-axis span { position: absolute; right: 0; font-size: 11px; color: #909399; transform: translateY(50%); }

/* Raw data */
.suspicious-cell { color: #f56c6c; }
</style>
