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
        <el-table-column prop="reservoir_name" label="水库名称" min-width="120" />
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
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'success'">
              <el-button type="primary" size="small" link @click="$router.push(`/task/${row.task_id}`)">详情</el-button>
              <el-button type="success" size="small" link @click="$router.push(`/task/${row.task_id}/anomalies`)">异常</el-button>
              <el-button type="info" size="small" link @click="$router.push(`/task/${row.task_id}/report`)">报告</el-button>
            </template>
            <el-button v-else-if="row.status === 'processing'" type="warning" size="small" link @click="$router.push(`/task/${row.task_id}`)">进度</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import FileDrop from '../components/FileDrop.vue'
import api from '../api'

const tasks = ref([])
const tableLoading = ref(false)

function statusLabel(s) {
  const map = { pending: '待处理', processing: '处理中', success: '已完成', failed: '失败' }
  return map[s] || s
}

async function refreshTasks() {
  tableLoading.value = true
  try {
    const res = await api.getTasks(1, 10)
    tasks.value = res.items || []
  } finally {
    tableLoading.value = false
  }
}

function onFileUploaded() { refreshTasks() }
onMounted(refreshTasks)
</script>

<style scoped>
.upload-view { max-width: 1400px; margin: 0 auto; }
</style>
