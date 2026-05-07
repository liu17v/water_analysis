<template>
  <div class="task-list-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span style="font-size:16px;font-weight:600">任务列表</span>
          <el-button type="primary" size="small" @click="$router.push('/upload')">
            <el-icon><Plus /></el-icon> 上传数据
          </el-button>
        </div>
      </template>

      <el-table :data="tasks" stripe v-loading="tableLoading" empty-text="暂无任务，请先上传数据">
        <el-table-column prop="task_id" label="任务ID" min-width="200" show-overflow-tooltip />
        <el-table-column prop="reservoir_name" label="水库名称" min-width="120" />
        <el-table-column prop="original_filename" label="原始文件" min-width="180" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_points" label="采样点" width="90" align="right" />
        <el-table-column prop="anomaly_count" label="异常点" width="90" align="right" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'success'">
              <el-button type="primary" size="small" @click="$router.push(`/task/${row.task_id}`)">可视化</el-button>
              <el-button type="success" size="small" @click="$router.push(`/task/${row.task_id}/anomalies`)">异常</el-button>
              <el-button type="info" size="small" @click="$router.push(`/task/${row.task_id}/report`)">报告</el-button>
            </template>
            <el-button v-else-if="row.status === 'processing'" type="warning" size="small" @click="$router.push(`/task/${row.task_id}`)">查看进度</el-button>
            <el-popconfirm v-if="row.status === 'failed'" title="确认删除?" @confirm="onDelete(row.task_id)">
              <template #reference>
                <el-button type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > pageSize"
        style="margin-top:16px; justify-content:flex-end"
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
import { Plus } from '@element-plus/icons-vue'
import api from '../api'

const tasks = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const tableLoading = ref(false)

function statusLabel(s) {
  const map = { pending: '待处理', processing: '处理中', success: '已完成', failed: '失败' }
  return map[s] || s
}
function statusType(s) {
  const map = { success: 'success', processing: 'warning', failed: 'danger', pending: 'info' }
  return map[s] || 'info'
}

async function fetchData() {
  tableLoading.value = true
  try {
    const res = await api.getTasks(currentPage.value, pageSize.value)
    tasks.value = res.items || []
    total.value = res.total || 0
  } finally {
    tableLoading.value = false
  }
}

async function onDelete(taskId) {
  try {
    await api.deleteTask(taskId)
    fetchData()
  } catch {}
}

onMounted(fetchData)
</script>

<style scoped>
.task-list-view { max-width: 1400px; margin: 0 auto; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
