<template>
  <el-aside :width="isCollapse ? '72px' : '228px'" class="app-sidebar glass-sidebar">
    <div class="logo" @click="$router.push('/')">
      <div class="logo-icon">
        <el-icon :size="22"><Odometer /></el-icon>
      </div>
      <span v-show="!isCollapse" class="logo-text">水质监测系统</span>
    </div>

    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapse"
      :collapse-transition="false"
      router
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
      <el-sub-menu index="map-group">
        <template #title>
          <el-icon><MapLocation /></el-icon>
          <span>地图</span>
        </template>
        <el-menu-item index="/map/street">街道地图</el-menu-item>
        <el-menu-item index="/map/satellite">卫星地图</el-menu-item>
      </el-sub-menu>
      <el-menu-item v-if="authStore.isAdmin" index="/users">
        <el-icon><UserFilled /></el-icon>
        <span>用户管理</span>
      </el-menu-item>
    </el-menu>

    <div class="sidebar-footer">
      <div class="collapse-btn" @click="$emit('toggle')">
        <el-icon :size="14">
          <component :is="isCollapse ? 'DArrowRight' : 'DArrowLeft'" />
        </el-icon>
      </div>
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
  if (path.startsWith('/map/')) return path
  return ''
})
</script>

<style scoped>
.glass-sidebar {
  --sidebar-glass: rgba(255, 255, 255, 0.72);
  --sidebar-text: #4e5969;
  --sidebar-text-active: #409eff;
  --sidebar-radius: 0 28px 28px 0;
  transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--sidebar-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.04);
}

@media (prefers-color-scheme: dark) {
  .glass-sidebar {
    --sidebar-glass: rgba(30, 35, 50, 0.78);
    --sidebar-text: #86909c;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
  }
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 20px 16px;
  color: var(--text-primary);
  cursor: pointer;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  min-height: 64px;
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: linear-gradient(135deg, #409eff, #1a6bc4);
  color: #fff;
  flex-shrink: 0;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  white-space: nowrap;
  letter-spacing: 0.5px;
}

.el-menu {
  flex: 1;
  background: transparent !important;
  border: none !important;
  padding: 8px;
}

.el-menu :deep(.el-menu-item) {
  border-radius: 12px;
  margin: 2px 0;
  color: var(--sidebar-text);
  height: 44px;
  line-height: 44px;
  transition: all 0.2s ease;
}

.el-menu :deep(.el-menu-item:hover) {
  background: rgba(64, 158, 255, 0.06);
  color: var(--sidebar-text-active);
}

.el-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.12), rgba(64, 158, 255, 0.06));
  color: var(--sidebar-text-active);
  font-weight: 600;
  box-shadow: inset 0 0 0 1px rgba(64, 158, 255, 0.08);
}

.el-menu :deep(.el-sub-menu__title) {
  border-radius: 12px;
  margin: 2px 0;
  color: var(--sidebar-text);
  height: 44px;
  line-height: 44px;
  transition: all 0.2s ease;
}

.el-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(64, 158, 255, 0.06);
  color: var(--sidebar-text-active);
}

.el-menu :deep(.el-menu--inline .el-menu-item) {
  padding-left: 50px !important;
  height: 38px;
  line-height: 38px;
  font-size: 13px;
}

.el-menu :deep(.el-icon) {
  color: inherit;
}

.sidebar-footer {
  border-top: 1px solid rgba(0, 0, 0, 0.04);
  padding: 8px;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  border-radius: 12px;
  color: var(--sidebar-text);
  cursor: pointer;
  transition: all 0.2s ease;
}

.collapse-btn:hover {
  background: rgba(64, 158, 255, 0.08);
  color: var(--sidebar-text-active);
}
</style>
