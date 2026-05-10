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
@import './styles/glass.css';

.app-container { height: 100vh; overflow: hidden; }
.app-right { flex: 1; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
.app-main { flex: 1; padding: 24px; overflow-y: auto; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
