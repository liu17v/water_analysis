import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('../views/UploadView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/tasks',
    name: 'TaskList',
    component: () => import('../views/TaskListView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/task/:id',
    name: 'TaskDetail',
    component: () => import('../views/TaskDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/task/:id/anomalies',
    name: 'TaskAnomalies',
    component: () => import('../views/AnomalyListView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/task/:id/report',
    name: 'TaskReport',
    component: () => import('../views/ReportView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/anomalies',
    name: 'AnomalyManage',
    component: () => import('../views/AnomalyListView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/compare',
    name: 'Compare',
    component: () => import('../views/CompareView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/reports',
    name: 'ReportManage',
    component: () => import('../views/ReportManageView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/users',
    name: 'UserManage',
    component: () => import('../views/UserManageView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
]

const router = createRouter({
  history: createWebHistory('/ui/'),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    return { path: '/login' }
  }
  if (to.meta.guest && token) {
    return { path: '/' }
  }
  if (to.meta.requiresAdmin) {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    if (user.role !== 'admin') return { path: '/' }
  }
  next()
})

export default router
