<template>
  <div class="task-list-view">
    <!-- Search & Filter Bar -->
    <el-card class="filter-bar">
      <el-row :gutter="12" align="middle">
        <el-col :span="5">
          <el-input v-model="search" placeholder="搜索任务ID/水库/文件名" clearable @clear="onSearch" @keyup.enter="onSearch">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterStatus" placeholder="状态筛选" clearable multiple collapse-tags @change="onSearch">
            <el-option label="已完成" value="success" />
            <el-option label="处理中" value="processing" />
            <el-option label="待处理" value="pending" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-date-picker v-model="dateRange" type="daterange" range-separator="至"
            start-placeholder="开始日期" end-placeholder="结束日期" format="YYYY-MM-DD" value-format="YYYY-MM-DD"
            @change="onSearch" style="width:100%" />
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon> 搜索</el-button>
          <el-button @click="resetFilters"><el-icon><Refresh /></el-icon></el-button>
        </el-col>
        <el-col :span="5" style="text-align:right">
          <el-button-group>
            <el-button :type="viewMode === 'table' ? 'primary' : ''" size="small" @click="viewMode='table'">
              <el-icon><List /></el-icon>
            </el-button>
            <el-button :type="viewMode === 'card' ? 'primary' : ''" size="small" @click="viewMode='card'">
              <el-icon><Grid /></el-icon>
            </el-button>
          </el-button-group>
          <el-button type="primary" style="margin-left:8px" @click="$router.push('/upload')">
            <el-icon><Plus /></el-icon> 上传数据
          </el-button>
          <el-button v-if="selected.length" type="danger" style="margin-left:4px"
            @click="batchDelete" :loading="batchLoading">
            <el-icon><Delete /></el-icon> 删除({{ selected.length }})
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Table View -->
    <el-card v-if="viewMode === 'table'" style="margin-top:12px">
      <el-skeleton :loading="loading" animated>
        <template #template>
          <el-skeleton-item v-for="i in 8" :key="i" variant="text" style="height:32px;margin-bottom:6px" />
        </template>
        <el-table :data="tasks" stripe size="small"
          empty-text="暂无任务" @selection-change="onSelect" @sort-change="onSort">
          <el-table-column type="selection" width="40" />
          <el-table-column prop="task_id" label="任务ID" min-width="200" show-overflow-tooltip sortable="custom" />
          <el-table-column label="水库名称" min-width="160">
            <template #default="{ row }">
              <template v-if="editingId === row.task_id">
                <el-input v-model="editingName" size="small" style="width:120px"
                  @keyup.enter="saveEdit(row)" @keyup.escape="cancelEdit()" ref="editInput" />
                <el-button size="small" type="primary" link @click="saveEdit(row)">确定</el-button>
                <el-button size="small" link @click="cancelEdit()">取消</el-button>
              </template>
              <template v-else>
                {{ row.reservoir_name || '-' }}
                <el-button size="small" link type="primary" @click="startEdit(row)"><el-icon><Edit /></el-icon></el-button>
              </template>
            </template>
          </el-table-column>
          <el-table-column prop="original_filename" label="原始文件" min-width="160" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="total_points" label="采样点" width="80" sortable="custom" />
          <el-table-column prop="anomaly_count" label="异常点" width="80" sortable="custom" />
          <el-table-column prop="created_at" label="创建时间" width="170" sortable="custom" />
          <el-table-column label="操作" width="260" fixed="right">
            <template #default="{ row }">
              <template v-if="row.status === 'success'">
                <el-button size="small" link type="primary" @click="$router.push(`/task/${row.task_id}`)">详情</el-button>
                <el-button size="small" link type="warning" @click="$router.push(`/task/${row.task_id}/anomalies`)">异常</el-button>
                <el-button size="small" link type="info" @click="$router.push(`/task/${row.task_id}/report`)">报告</el-button>
              </template>
              <el-button v-else-if="row.status === 'processing'" size="small" link type="warning"
                @click="$router.push(`/task/${row.task_id}`)">进度</el-button>
              <el-button v-else-if="row.status === 'pending'" size="small" link type="success"
                @click="onProcess(row.task_id)">处理</el-button>
              <el-popconfirm title="确认删除?" @confirm="onDelete(row.task_id)">
                <template #reference><el-button size="small" link type="danger">删除</el-button></template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-skeleton>

      <div class="pagination-row">
        <span class="total-text">共 {{ total }} 条</span>
        <el-pagination
          v-model:current-page="page" :page-size="pageSize" :total="total"
          :page-sizes="[20, 50, 100]" layout="sizes, prev, pager, next, jumper"
          @size-change="onPageSizeChange" @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- Card View -->
    <div v-else class="card-grid">
      <el-skeleton v-if="loading" animated style="grid-column:1/-1;display:flex;gap:16px;flex-wrap:wrap">
        <el-card v-for="i in 6" :key="i" style="width:280px">
          <el-skeleton-item variant="text" style="width:40%" />
          <el-skeleton-item variant="text" style="width:60%;margin-top:8px" />
          <el-skeleton-item variant="text" style="width:80%;margin-top:8px" />
        </el-card>
      </el-skeleton>
      <template v-else>
        <el-card v-for="t in tasks" :key="t.task_id" shadow="hover" class="task-card"
          @click="$router.push(t.status === 'success' ? `/task/${t.task_id}` : `/task/${t.task_id}`)">
          <div class="card-top">
            <el-tag :type="statusType(t.status)" size="small">{{ statusLabel(t.status) }}</el-tag>
            <span class="card-id">{{ t.task_id?.substring(0, 8) }}...</span>
          </div>
          <div class="card-name">
            <template v-if="editingId === t.task_id">
              <el-input v-model="editingName" size="small" style="width:140px" @keyup.enter="saveEdit(t)" @keyup.escape="cancelEdit()" />
              <el-button size="small" type="primary" link @click="saveEdit(t)">确定</el-button>
              <el-button size="small" link @click="cancelEdit()">取消</el-button>
            </template>
            <template v-else>
              {{ t.reservoir_name || '未知水库' }}
              <el-button size="small" link type="primary" @click.stop="startEdit(t)"><el-icon><Edit /></el-icon></el-button>
            </template>
          </div>
          <div class="card-file">{{ t.original_filename || '-' }}</div>
          <el-divider style="margin:8px 0" />
          <el-row :gutter="8">
            <el-col :span="8"><div class="card-stat"><div class="card-num">{{ t.total_points }}</div><div class="card-lbl">采样点</div></div></el-col>
            <el-col :span="8"><div class="card-stat"><div class="card-num" :class="{red:t.anomaly_count>0}">{{ t.anomaly_count }}</div><div class="card-lbl">异常点</div></div></el-col>
            <el-col :span="8"><div class="card-stat"><div class="card-num small">{{ t.created_at?.substring(0,10) }}</div><div class="card-lbl">日期</div></div></el-col>
          </el-row>
        </el-card>
        <div v-if="tasks.length === 0 && !loading" class="card-empty">
          <el-empty description="暂无匹配的任务" :image-size="80" />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Search, Refresh, List, Grid, Delete, Edit } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import { useTask } from '../composables/useTask'

const { statusLabel, statusType } = useTask()

const tasks = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(true)
const batchLoading = ref(false)
const selected = ref([])
const viewMode = ref('table')

const search = ref('')
const filterStatus = ref([])
const dateRange = ref(null)
const sortField = ref('')
const sortOrder = ref('')

const editingId = ref('')
const editingName = ref('')
function startEdit(task) {
  editingId.value = task.task_id
  editingName.value = task.reservoir_name || ''
}
async function saveEdit(task) {
  try {
    await api.updateTask(task.task_id, { reservoir_name: editingName.value || '' })
    task.reservoir_name = editingName.value
    ElMessage.success('水库名称已更新')
  } catch { ElMessage.error('更新失败') }
  finally { editingId.value = '' }
}
function cancelEdit() { editingId.value = '' }

async function fetchData() {
  loading.value = true
  try {
    const extra = {}
    if (search.value) extra.search = search.value
    if (filterStatus.value.length) extra.status = filterStatus.value.join(',')
    if (dateRange.value?.length === 2) {
      extra.start_date = dateRange.value[0]
      extra.end_date = dateRange.value[1]
    }
    if (sortField.value) {
      extra.sort = sortField.value
      extra.order = sortOrder.value || 'desc'
    }
    const res = await api.getTasks(page.value, pageSize.value, extra)
    tasks.value = res.items || []
    total.value = res.total || 0
  } finally { loading.value = false }
}

function onSearch() { page.value = 1; fetchData() }
function resetFilters() {
  search.value = ''; filterStatus.value = []; dateRange.value = null
  sortField.value = ''; sortOrder.value = ''
  onSearch()
}
function onSort({ prop, order }) {
  sortField.value = prop || ''
  sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  onSearch()
}
function onSelect(rows) { selected.value = rows }
function onPageSizeChange(size) { pageSize.value = size; onSearch() }

async function onDelete(taskId) {
  try { await api.deleteTask(taskId); ElMessage.success('任务已删除'); fetchData() }
  catch { ElMessage.error('删除失败，请稍后重试') }
}

async function onProcess(taskId) {
  try {
    await api.processTask(taskId)
    ElMessage.success('任务处理已启动')
    fetchData()
  } catch { ElMessage.error('启动处理失败') }
}

async function batchDelete() {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selected.value.length} 个任务？此操作不可恢复。`, '批量删除', { type: 'warning' })
    batchLoading.value = true
    for (const t of selected.value) {
      await api.deleteTask(t.task_id).catch(() => {})
    }
    ElMessage.success('批量删除完成')
    selected.value = []
    fetchData()
  } catch { /* cancelled */ }
  finally { batchLoading.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.task-list-view { max-width: 1500px; margin: 0 auto; }
.filter-bar { margin-bottom: 0; }
.filter-bar :deep(.el-card__body) { padding: 12px 16px; }

.pagination-row { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; }
.total-text { font-size: 13px; color: #909399; }

.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-top: 12px; }
.task-card { cursor: pointer; transition: transform 0.2s; }
.task-card:hover { transform: translateY(-3px); }
.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.card-id { font-size: 12px; color: #909399; font-family: monospace; }
.card-name { font-size: 16px; font-weight: 600; color: #303133; margin-bottom: 4px; }
.card-file { font-size: 12px; color: #909399; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-stat { text-align: center; }
.card-num { font-size: 20px; font-weight: 700; color: #303133; }
.card-num.red { color: #f56c6c; }
.card-num.small { font-size: 14px; }
.card-lbl { font-size: 11px; color: #c0c4cc; }
.card-empty { grid-column: 1 / -1; }
</style>
