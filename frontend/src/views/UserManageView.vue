<template>
  <div class="user-manage">
    <el-page-header @back="$router.push('/')" content="用户管理" style="margin-bottom:16px" />

    <!-- Toolbar -->
    <el-card style="margin-bottom:12px">
      <el-row :gutter="12" align="middle">
        <el-col :span="6">
          <el-input v-model="search" placeholder="搜索用户名" clearable @clear="onSearch" @keyup.enter="onSearch">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon> 搜索</el-button>
          <el-button @click="resetSearch"><el-icon><Refresh /></el-icon></el-button>
        </el-col>
        <el-col :span="14" style="text-align:right">
          <el-button type="success" @click="openAddDialog">
            <el-icon><Plus /></el-icon> 添加用户
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- User table -->
    <el-card>
      <el-table :data="users" stripe v-loading="loading" border size="small">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="150" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small" effect="dark">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openEditDialog(row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-popconfirm
              :title="`确定删除用户 ${row.username}？此操作不可恢复。`"
              @confirm="handleDelete(row.id)"
            >
              <template #reference>
                <el-button size="small" text type="danger" :disabled="row.role === 'admin'">
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
        :total="total" :page-size="pageSize"
        v-model:current-page="page"
        @current-change="fetchData"
      />
    </el-card>

    <!-- Add/Edit dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '添加用户'" width="480px" destroy-on-close @closed="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width:100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="密码" :prop="isEdit ? null : 'password'">
          <el-input v-model="form.password" type="password" show-password
            :placeholder="isEdit ? '留空则不修改密码' : '请输入密码'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存修改' : '添加用户' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const users = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const search = ref('')
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editUserId = ref(null)
const formRef = ref(null)

const form = reactive({ username: '', role: 'user', password: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }, { min: 2, max: 32, message: '长度 2-32', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '至少6位', trigger: 'blur' }],
}

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (search.value) params.search = search.value
    const res = await authStore.getUsers(page.value, pageSize.value)
    users.value = (res.items || []).filter(u => !search.value || u.username.includes(search.value))
    total.value = res.total || 0
  } finally { loading.value = false }
}

function onSearch() { page.value = 1; fetchData() }
function resetSearch() { search.value = ''; onSearch() }

function openAddDialog() {
  isEdit.value = false
  editUserId.value = null
  form.username = ''
  form.role = 'user'
  form.password = ''
  dialogVisible.value = true
}

function openEditDialog(row) {
  isEdit.value = true
  editUserId.value = row.id
  form.username = row.username
  form.role = row.role
  form.password = ''
  dialogVisible.value = true
}

function resetForm() {
  if (formRef.value) formRef.value.resetFields()
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (isEdit.value) {
      const data = { username: form.username, role: form.role }
      if (form.password) data.password = form.password
      await authStore.updateUser(editUserId.value, data)
      ElMessage.success('用户信息已更新')
    } else {
      await authStore.createUser({ username: form.username, password: form.password, role: form.role })
      ElMessage.success('用户已创建')
    }
    dialogVisible.value = false
    fetchData()
  } catch { /* handled by interceptor */ }
  finally { submitting.value = false }
}

async function handleDelete(userId) {
  try {
    await authStore.deleteUser(userId)
    ElMessage.success('用户已删除')
    fetchData()
  } catch { /* handled by interceptor */ }
}

onMounted(fetchData)
</script>

<style scoped>
.user-manage { max-width: 1500px; margin: 0 auto; }
</style>
