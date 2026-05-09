<template>
  <el-aside :width="isCollapse ? '64px' : '220px'" class="app-sidebar">
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
      <el-menu-item v-if="authStore.isAdmin" index="/users">
        <el-icon><UserFilled /></el-icon>
        <span>用户管理</span>
      </el-menu-item>
    </el-menu>
    <div class="collapse-btn" @click="$emit('toggle')">
      <el-icon :size="16">
        <component :is="isCollapse ? 'DArrowRight' : 'DArrowLeft'" />
      </el-icon>
    </div>
  </el-aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

defineProps({ isCollapse: Boolean })
defineEmits(['toggle'])
const route = useRoute()
const authStore = useAuthStore()

const activeMenu = computed(() => {
  const path = route.path
  if (['/', '/upload', '/tasks', '/compare', '/anomalies', '/reports', '/users'].includes(path)) return path
  return ''
})
</script>

<style scoped>
.app-sidebar { background: #1a3a5c; transition: width 0.3s; overflow: hidden; display: flex; flex-direction: column; }
.logo { display: flex; align-items: center; gap: 10px; padding: 16px 20px; color: #fff; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.1); }
.logo-text { font-size: 16px; font-weight: 700; white-space: nowrap; }
.collapse-btn { padding: 12px; text-align: center; color: #bfcbd9; cursor: pointer; border-top: 1px solid rgba(255,255,255,0.1); }
.collapse-btn:hover { color: #fff; background: rgba(255,255,255,0.05); }
</style>
