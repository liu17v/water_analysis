<template>
  <el-header class="app-header">
    <div class="header-left">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item v-if="breadcrumb1" :to="breadcrumb1.to">{{ breadcrumb1.label }}</el-breadcrumb-item>
        <el-breadcrumb-item v-if="breadcrumb2">{{ breadcrumb2 }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-right">
      <el-tag type="success" size="small" effect="dark">系统运行中</el-tag>
      <span class="header-user">
        <el-icon><UserFilled /></el-icon>
        <span style="margin:0 4px">{{ authStore.username || '管理员' }}</span>
        <span v-if="authStore.role" class="role-tag">{{ authStore.isAdmin ? '管理员' : '用户' }}</span>
      </span>
      <el-button text type="danger" size="small" @click="handleLogout">
        <el-icon><SwitchButton /></el-icon> 退出
      </el-button>
    </div>
  </el-header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const breadcrumb1 = computed(() => {
  const path = route.path
  const map = {
    '/upload': { label: '数据上传', to: '/upload' },
    '/tasks': { label: '任务列表', to: '/tasks' },
    '/compare': { label: '数据对比', to: '/compare' },
    '/anomalies': { label: '异常管理', to: '/anomalies' },
    '/reports': { label: '智能报告', to: '/reports' },
    '/users': { label: '用户管理', to: '/users' },
  }
  if (map[path]) return map[path]
  if (path.startsWith('/task/')) return { label: '任务详情', to: null }
  return null
})

const breadcrumb2 = computed(() => {
  if (route.path.match(/\/anomalies$/)) return '异常点列表'
  if (route.path.match(/\/report$/)) return '报告生成'
  return null
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-header { background: #fff; display: flex; align-items: center; justify-content: space-between; padding: 0 24px; height: 56px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.header-right { display: flex; align-items: center; gap: 12px; }
.header-user { display: flex; align-items: center; font-size: 13px; color: #606266; }
.role-tag { font-size: 11px; color: #909399; }
</style>
