<template>
  <!-- Login page: no layout chrome -->
  <router-view v-if="isLoginPage" />

  <!-- Normal layout -->
  <el-container v-else class="app-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="app-aside">
      <div class="logo" @click="$router.push('/')">
        <el-icon :size="24"><Odometer /></el-icon>
        <span v-show="!isCollapse" class="logo-text">水质监测系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        background-color="#1a3a5c"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/map">
          <el-icon><MapLocation /></el-icon>
          <span>空间地图</span>
        </el-menu-item>
        <el-menu-item index="/">
          <el-icon><DataBoard /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/upload">
          <el-icon><Upload /></el-icon>
          <span>数据上传</span>
        </el-menu-item>
        <el-menu-item index="/tasks">
          <el-icon><List /></el-icon>
          <span>任务列表</span>
        </el-menu-item>
        <el-menu-item index="/compare">
          <el-icon><Sort /></el-icon>
          <span>数据对比</span>
        </el-menu-item>
        <el-menu-item index="/anomalies">
          <el-icon><WarningFilled /></el-icon>
          <span>异常管理</span>
        </el-menu-item>
        <el-menu-item index="/reports">
          <el-icon><Document /></el-icon>
          <span>智能报告</span>
        </el-menu-item>
        <el-menu-item v-if="authStore.role === 'admin'" index="/users">
          <el-icon><UserFilled /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
      </el-menu>
      <div class="collapse-btn" @click="isCollapse = !isCollapse">
        <el-icon :size="16"><component :is="isCollapse ? 'DArrowRight' : 'DArrowLeft'" /></el-icon>
      </div>
    </el-aside>

    <!-- 主体 -->
    <el-container>
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
            <span v-if="authStore.role" class="role-tag">{{ authStore.role === 'admin' ? '管理员' : '用户' }}</span>
          </span>
          <el-button text type="danger" size="small" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon> 退出
          </el-button>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Odometer, DataBoard, Upload, List, Sort, MapLocation, DArrowRight, DArrowLeft,
  UserFilled, WarningFilled, Document, SwitchButton,
} from '@element-plus/icons-vue'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isCollapse = ref(false)

const isLoginPage = computed(() => route.path === '/login')

const activeMenu = computed(() => {
  const path = route.path
  if (path === '/' || path === '/map' || path === '/upload' || path === '/tasks' || path === '/compare'
      || path === '/anomalies' || path === '/reports' || path === '/users') return path
  if (path.startsWith('/task/')) return ''
  return '/' + path.split('/')[1]
})

const breadcrumb1 = computed(() => {
  const path = route.path
  if (path === '/') return null
  if (path === '/map') return { label: '空间地图', to: '/map' }
  if (path === '/upload') return { label: '数据上传', to: '/upload' }
  if (path === '/tasks') return { label: '任务列表', to: '/tasks' }
  if (path === '/compare') return { label: '数据对比', to: '/compare' }
  if (path === '/anomalies') return { label: '异常管理', to: '/anomalies' }
  if (path === '/reports') return { label: '智能报告', to: '/reports' }
  if (path === '/users') return { label: '用户管理', to: '/users' }
  if (path.match(/^\/task\/[^/]+/)) return { label: '任务详情', to: null }
  return null
})

const breadcrumb2 = computed(() => {
  const path = route.path
  if (path.match(/\/anomalies$/)) return '异常点列表'
  if (path.match(/\/report$/)) return '报告生成'
  return null
})

async function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; background: #f0f2f5; }
.app-container { min-height: 100vh; }

.app-aside {
  background: #1a3a5c;
  transition: width 0.3s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  color: #fff;
  cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.logo-text { font-size: 16px; font-weight: 700; white-space: nowrap; }
.el-menu { border-right: none !important; flex: 1; }
.collapse-btn {
  padding: 12px;
  text-align: center;
  color: #bfcbd9;
  cursor: pointer;
  border-top: 1px solid rgba(255,255,255,0.1);
}
.collapse-btn:hover { color: #fff; background: rgba(255,255,255,0.05); }

.app-header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.header-right { display: flex; align-items: center; gap: 12px; }
.header-user { display: flex; align-items: center; font-size: 13px; color: #606266; }
.role-tag { font-size: 11px; color: #909399; }
.app-main { padding: 20px; min-height: calc(100vh - 56px); }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
