<template>
  <el-header class="app-header glass-header">
    <div class="header-left">
      <el-breadcrumb separator="›" class="glass-breadcrumb">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item v-if="breadcrumb1" :to="breadcrumb1.to">{{ breadcrumb1.label }}</el-breadcrumb-item>
        <el-breadcrumb-item v-if="breadcrumb2">{{ breadcrumb2 }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-right">
      <div class="status-dot" />
      <span class="status-text">系统运行中</span>
      <div class="header-divider" />
      <span class="header-user">
        <el-icon :size="15"><UserFilled /></el-icon>
        <span>{{ authStore.username || '管理员' }}</span>
        <span v-if="authStore.role" class="role-badge">{{ authStore.isAdmin ? '管理员' : '用户' }}</span>
      </span>
      <el-button text size="small" class="logout-btn" @click="handleLogout">
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
    '/map': { label: '地图&天气', to: '/map' },
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
.glass-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  height: 56px;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.03);
  flex-shrink: 0;
}

@media (prefers-color-scheme: dark) {
  .glass-header {
    background: rgba(30, 35, 50, 0.7);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }
}

.header-left {
  display: flex;
  align-items: center;
}

.glass-breadcrumb :deep(.el-breadcrumb__inner) {
  color: var(--text-secondary) !important;
  font-size: 13px;
}

.glass-breadcrumb :deep(.el-breadcrumb__inner:hover) {
  color: var(--primary) !important;
}

.glass-breadcrumb :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: var(--text-primary) !important;
  font-weight: 600;
}

.glass-breadcrumb :deep(.el-breadcrumb__separator) {
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 300;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #67c23a;
  box-shadow: 0 0 8px rgba(103, 194, 58, 0.5);
  animation: glassPulse 2s infinite;
}

.status-text {
  font-size: 12px;
  color: #67c23a;
  font-weight: 500;
}

.header-divider {
  width: 1px;
  height: 20px;
  background: rgba(0, 0, 0, 0.08);
  margin: 0 6px;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-primary);
  padding: 4px 12px 4px 8px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 20px;
}

.role-badge {
  font-size: 10px;
  padding: 1px 8px;
  border-radius: 10px;
  background: rgba(64, 158, 255, 0.1);
  color: var(--primary);
  font-weight: 500;
}

.logout-btn {
  color: var(--text-secondary) !important;
  border-radius: 16px !important;
  transition: all 0.2s ease !important;
}

.logout-btn:hover {
  color: #f56c6c !important;
  background: rgba(245, 108, 108, 0.08) !important;
}
</style>
