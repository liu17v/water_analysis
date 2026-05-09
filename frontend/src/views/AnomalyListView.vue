<template>
  <div class="anomaly-list-view">
    <el-page-header @back="$router.back()" :content="isGlobalMode ? '异常点管理' : '任务异常点'" style="margin-bottom:16px" />

    <!-- Filter bar -->
    <el-card class="filter-bar">
      <el-row :gutter="12" align="middle">
        <el-col :span="4">
          <el-input v-model="filterTaskId" :placeholder="isGlobalMode ? '搜索任务ID' : '已筛选当前任务'" clearable
            :disabled="!isGlobalMode" @clear="onFilter" @keyup.enter="onFilter">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-col>
        <el-col :span="3">
          <IndicatorSelect v-model="filterIndicator" placeholder="指标筛选" size="default" />
        </el-col>
        <el-col :span="3">
          <el-select v-model="filterMethod" placeholder="检测方法" clearable @change="onFilter">
            <el-option label="阈值检测" value="threshold" />
            <el-option label="孤立森林" value="isolation_forest" />
          </el-select>
        </el-col>
        <el-col :span="3">
          <el-input v-model="filterDepthMin" placeholder="深度范围" size="small" style="width:48%" />
          <span style="margin:0 2px">-</span>
          <el-input v-model="filterDepthMax" placeholder="" size="small" style="width:44%" @keyup.enter="onFilter" />
        </el-col>
        <el-col :span="3">
          <el-input v-model="filterValueMin" placeholder="数值范围" size="small" style="width:48%" />
          <span style="margin:0 2px">-</span>
          <el-input v-model="filterValueMax" placeholder="" size="small" style="width:44%" @keyup.enter="onFilter" />
        </el-col>
        <el-col :span="3">
          <el-button type="primary" size="small" @click="onFilter"><el-icon><Search /></el-icon> 查询</el-button>
          <el-button size="small" @click="resetFilters"><el-icon><Refresh /></el-icon></el-button>
        </el-col>
        <el-col :span="5" style="text-align:right">
          <el-button size="small" @click="exportCSV"><el-icon><Download /></el-icon> CSV</el-button>
          <el-button size="small" type="success" @click="exportXLSX"><el-icon><Download /></el-icon> XLSX</el-button>
          <el-button size="small" type="warning" @click="toggleMapView">
            <el-icon><MapLocation /></el-icon> {{ showMap ? '隐藏地图' : '异常点地图' }}
          </el-button>
          <el-tag type="danger" size="default" style="margin-left:8px">{{ total }} 条</el-tag>
        </el-col>
      </el-row>
    </el-card>

    <!-- Map -->
    <el-card v-if="showMap" style="margin-top:12px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>异常点地图</span>
        </div>
      </template>
      <AnomalyMap :anomalies="mapAnomalies" />
    </el-card>

    <!-- Table -->
    <el-card style="margin-top:12px">
      <template v-if="rows.length">
        <el-table :data="rows" stripe v-loading="loading" border size="small" max-height="600"
          @row-click="openDrawer" highlight-current-row>
          <el-table-column type="selection" width="40" />
          <el-table-column prop="task_id" label="任务ID" min-width="200" show-overflow-tooltip v-if="isGlobalMode" />
          <el-table-column prop="lon" label="经度" width="110">
            <template #default="{ row }">{{ row.lon?.toFixed(6) }}</template>
          </el-table-column>
          <el-table-column prop="lat" label="纬度" width="110">
            <template #default="{ row }">{{ row.lat?.toFixed(6) }}</template>
          </el-table-column>
          <el-table-column prop="depth" label="深度(m)" width="90" sortable="custom" />
          <el-table-column label="指标" width="100" sortable="custom">
            <template #default="{ row }">
              <el-tag size="small" effect="dark">{{ shortLabel(row.indicator) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="value" label="数值" width="110" sortable="custom">
            <template #default="{ row }">
              <span :style="{ color: row._severity === 'high' ? '#f56c6c' : row._severity === 'medium' ? '#e6a23c' : '#409eff' }">
                {{ row.value?.toFixed(4) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="检测方法" width="120">
            <template #default="{ row }">
              <el-tag :type="row.method === 'threshold' ? 'warning' : 'primary'" size="small">
                {{ row.method === 'threshold' ? '阈值检测' : '孤立森林' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button size="small" text type="primary" @click.stop="openDrawer(row)">详情</el-button>
              <el-button size="small" text type="info" @click.stop="goToTask(row)">查看任务</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-row">
          <span class="total-text" v-if="isGlobalMode" style="margin-right:16px">共 {{ total }} 条，按异常指标+方法+深度筛选</span>
          <el-pagination
            v-if="total > pageSize"
            layout="total, sizes, prev, pager, next, jumper"
            :total="total" :page-size="pageSize" :page-sizes="[20, 50, 100]"
            v-model:current-page="page"
            @size-change="onPageSizeChange"
            @current-change="fetchData"
          />
        </div>
      </template>
      <EmptyState v-else text="暂无异常点数据" />
    </el-card>

    <!-- Detail drawer -->
    <el-drawer v-model="drawerVisible" title="异常点详情" size="400px" destroy-on-close>
      <template v-if="drawerRow">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="任务ID">{{ drawerRow.task_id }}</el-descriptions-item>
          <el-descriptions-item label="坐标">{{ drawerRow.lon?.toFixed(6) }}, {{ drawerRow.lat?.toFixed(6) }}</el-descriptions-item>
          <el-descriptions-item label="深度">{{ drawerRow.depth }}m</el-descriptions-item>
          <el-descriptions-item label="异常指标">
            <el-tag size="small">{{ shortLabel(drawerRow.indicator) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="异常值">
            <span style="color:#f56c6c;font-weight:600">{{ drawerRow.value?.toFixed(4) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="检测方法">
            <el-tag :type="drawerRow.method === 'threshold' ? 'warning' : 'primary'" size="small">
              {{ drawerRow.method === 'threshold' ? '阈值检测' : '孤立森林' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <el-divider />
        <div class="drawer-actions">
          <el-button size="small" type="primary" @click="$router.push(`/task/${drawerRow.task_id}`)">
            查看任务详情
          </el-button>
          <el-button size="small" type="warning" @click="$router.push(`/task/${drawerRow.task_id}/report`)">
            生成报告
          </el-button>
        </div>
      </template>
      <EmptyState v-else text="请选择一条异常记录" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, Refresh, Download, MapLocation } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import AnomalyMap from '../components/map/AnomalyMap.vue'
import IndicatorSelect from '../components/common/IndicatorSelect.vue'
import EmptyState from '../components/common/EmptyState.vue'

import { getAnomalies, getAllAnomalies, exportAnomalies, exportAnomaliesXlsx } from '../api/anomaly'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => route.params.id || null)
const isGlobalMode = computed(() => !taskId.value)

watch(() => route.params.id, (newId) => {
  filterTaskId.value = newId || ''
  page.value = 1
  fetchData()
})

const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

const filterTaskId = ref('')
const filterIndicator = ref('')
const filterMethod = ref('')
const filterDepthMin = ref('')
const filterDepthMax = ref('')
const filterValueMin = ref('')
const filterValueMax = ref('')

const showMap = ref(false)

const drawerVisible = ref(false)
const drawerRow = ref(null)

const labelMap = { chl: '叶绿素', odo: '溶解氧', temp: '水温', ph: 'pH', turb: '浊度' }
function shortLabel(code) { return labelMap[code] || code }

const normalRanges = { chl: [0, 20], odo: [4, 12], temp: [0, 35], ph: [6.5, 8.5], turb: [0, 10] }
function severity(row) {
  const r = normalRanges[row.indicator]
  if (!r) return 'low'
  const dev = Math.abs(row.value - (r[0] + r[1]) / 2) / ((r[1] - r[0]) / 2)
  return dev > 2 ? 'high' : dev > 1.2 ? 'medium' : 'low'
}

const mapAnomalies = computed(() => rows.value.filter(r => r.lat != null && r.lon != null))

async function fetchData() {
  loading.value = true
  try {
    let items = []
    let totalCount = 0
    if (!isGlobalMode.value) {
      const res = await getAnomalies(taskId.value, page.value, pageSize.value)
      items = res.items || []
      totalCount = res.total || 0
    } else {
      const filters = {}
      if (filterTaskId.value) filters.task_id = filterTaskId.value
      if (filterIndicator.value) filters.indicator = filterIndicator.value
      if (filterMethod.value) filters.method = filterMethod.value
      const res = await getAllAnomalies(page.value, pageSize.value, filters)
      items = res.items || []
      totalCount = res.total || 0
    }
    // Frontend filters for depth and value range
    if (filterDepthMin.value) items = items.filter(r => +r.depth >= +filterDepthMin.value)
    if (filterDepthMax.value) items = items.filter(r => +r.depth <= +filterDepthMax.value)
    if (filterValueMin.value) items = items.filter(r => +r.value >= +filterValueMin.value)
    if (filterValueMax.value) items = items.filter(r => +r.value <= +filterValueMax.value)
    rows.value = items.map(r => ({ ...r, _severity: severity(r) }))
    total.value = items.length
  } finally { loading.value = false }
}

function onFilter() { page.value = 1; fetchData() }
function resetFilters() {
  filterIndicator.value = ''; filterMethod.value = ''
  filterDepthMin.value = ''; filterDepthMax.value = ''
  filterValueMin.value = ''; filterValueMax.value = ''
  onFilter()
}
function onPageSizeChange(size) { pageSize.value = size; onFilter() }
function openDrawer(row) { drawerRow.value = row; drawerVisible.value = true }
function goToTask(row) { router.push(`/task/${row.task_id}`) }
function triggerDownload(url) {
  const a = document.createElement('a')
  a.href = url
  a.download = ''
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

function exportCSV() {
  if (!isGlobalMode.value) triggerDownload(exportAnomalies(taskId.value))
  else ElMessage.warning('请先选择具体任务再导出')
}

function exportXLSX() {
  if (!isGlobalMode.value) triggerDownload(exportAnomaliesXlsx(taskId.value))
  else ElMessage.warning('请先选择具体任务再导出')
}

function toggleMapView() {
  showMap.value = !showMap.value
}

onMounted(() => {
  if (taskId.value) {
    filterTaskId.value = taskId.value
  }
  fetchData()
})
</script>

<style scoped>
.anomaly-list-view { max-width: 1500px; margin: 0 auto; }
.filter-bar { margin-bottom: 0; }
.filter-bar :deep(.el-card__body) { padding: 10px 16px; }
.pagination-row { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; }
.total-text { font-size: 13px; color: #909399; }
.drawer-actions { display: flex; gap: 8px; }
</style>
