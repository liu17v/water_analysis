<template>
  <div class="anomaly-view">
    <el-page-header @back="$router.back()" content="异常点列表" style="margin-bottom:16px" />

    <el-card>
      <div class="toolbar">
        <span>共 {{ total }} 个异常点</span>
        <el-button type="primary" size="small" @click="exportCSV">
          <el-icon><Download /></el-icon> 导出 CSV
        </el-button>
      </div>

      <el-table :data="anomalies" stripe v-loading="loading" empty-text="无异常点">
        <el-table-column prop="id" label="序号" width="80" />
        <el-table-column prop="lon" label="经度" width="140">
          <template #default="{ row }">{{ row.lon?.toFixed(6) }}</template>
        </el-table-column>
        <el-table-column prop="lat" label="纬度" width="140">
          <template #default="{ row }">{{ row.lat?.toFixed(6) }}</template>
        </el-table-column>
        <el-table-column prop="depth" label="深度 (m)" width="100" />
        <el-table-column prop="indicator" label="异常指标" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ indicatorLabel(row.indicator) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="value" label="数值" width="120">
          <template #default="{ row }">
            <span :style="{ color: getValueColor(row) }">{{ row.value?.toFixed(4) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="method" label="检测方法" width="160">
          <template #default="{ row }">
            <el-tag :type="row.method === 'threshold' ? 'warning' : 'primary'" size="small">
              {{ row.method === 'threshold' ? '阈值检测' : '孤立森林' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > pageSize"
        style="margin-top:16px;justify-content:flex-end"
        layout="total, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        v-model:current-page="currentPage"
        @current-change="fetchData"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Download } from '@element-plus/icons-vue'
import api from '../api'

const route = useRoute()
const taskId = route.params.id
const anomalies = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const loading = ref(false)

const indicatorLabels = { chl: '叶绿素', odo: '溶解氧', temp: '水温', ph: 'pH', turb: '浊度' }
function indicatorLabel(key) { return indicatorLabels[key] || key }

function getValueColor(row) {
  // Flag values outside normal range
  const ranges = { chl: [0, 20], odo: [4, 12], temp: [0, 35], ph: [6.5, 8.5], turb: [0, 10] }
  const range = ranges[row.indicator]
  if (range && (row.value < range[0] || row.value > range[1])) return '#f56c6c'
  return '#333'
}

async function fetchData() {
  loading.value = true
  try {
    const res = await api.getAnomalies(taskId, currentPage.value, pageSize.value)
    anomalies.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function exportCSV() {
  window.open(api.exportAnomalies(taskId), '_blank')
}

onMounted(fetchData)
</script>

<style scoped>
.anomaly-view { max-width: 1400px; margin: 0 auto; padding: 16px; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
