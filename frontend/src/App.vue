<template>
  <router-view v-if="isLoginPage" />
  <el-container v-else class="app-container">
    <AppSidebar :is-collapse="isCollapse" @toggle="isCollapse = !isCollapse" />
    <el-container class="app-right">
      <AppHeader />
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
import { useRoute } from 'vue-router'
import AppSidebar from './components/layout/AppSidebar.vue'
import AppHeader from './components/layout/AppHeader.vue'

const route = useRoute()
const isCollapse = ref(false)
const isLoginPage = computed(() => route.path === '/login')
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; background: #f0f2f5; }
.app-container { height: 100vh; overflow: hidden; }
.app-right { flex: 1; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
.el-menu { border-right: none !important; flex: 1; }
.app-main { flex: 1; padding: 20px; overflow-y: auto; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
