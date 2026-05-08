<template>
  <div class="report-manage">
    <el-page-header @back="$router.push('/')" content="报告管理" style="margin-bottom:16px" />

    <!-- Stats bar -->
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card-inner">
            <el-icon :size="32" color="#409eff"><Document /></el-icon>
            <div>
              <div class="stat-card-val">{{ total }}</div>
              <div class="stat-card-lbl">报告总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card-inner">
            <el-icon :size="32" color="#67c23a"><FolderOpened /></el-icon>
            <div>
              <div class="stat-card-val">{{ rows.length }}</div>
              <div class="stat-card-lbl">当前页记录</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Table -->
    <el-card>
      <el-table :data="rows" v-loading="loading" stripe border size="small" max-height="600">
        <el-table-column prop="task_id" label="任务ID" min-width="200" show-overflow-tooltip />
        <el-table-column prop="reservoir_name" label="水库名称" width="160">
          <template #default="{ row }">{{ row.reservoir_name || '未知' }}</template>
        </el-table-column>
        <el-table-column prop="total_points" label="采样点" width="90" />
        <el-table-column prop="anomaly_count" label="异常点" width="90" />
        <el-table-column prop="report_path" label="报告路径" min-width="220" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" text @click="$router.push(`/task/${row.task_id}`)">
              <el-icon><View /></el-icon> 任务详情
            </el-button>
            <el-button size="small" type="primary" text @click="previewReport(row)">
              <el-icon><View /></el-icon> 预览
            </el-button>
            <el-button size="small" type="success" text @click="openReport(row)">
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
        @current-change="loadData"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { View, Download, Delete, Document, FolderOpened } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

async function loadData() {
  loading.value = true
  try {
    const res = await api.getReports(page.value, pageSize.value)
    rows.value = res.items || []
    total.value = res.total || 0
  } finally { loading.value = false }
}

function openReport(row) {
  if (row.report_path) {
    const path = row.report_path.startsWith('/') ? row.report_path : '/' + row.report_path
    window.open(path, '_blank')
  }
}

function previewReport(row) {
  openReport(row)
}

async function handleDelete(taskId) {
  try {
    await api.deleteReport(taskId)
    ElMessage.success('报告已删除')
    loadData()
  } catch { ElMessage.error('删除失败') }
}

onMounted(() => loadData())
</script>

<style scoped>
.report-manage { max-width: 1500px; margin: 0 auto; }
.stat-card { cursor: default; }
.stat-card-inner { display: flex; align-items: center; gap: 16px; }
.stat-card-val { font-size: 24px; font-weight: 700; color: #303133; }
.stat-card-lbl { font-size: 13px; color: #909399; margin-top: 2px; }
</style>
