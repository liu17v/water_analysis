import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('token') || '')

  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const username = computed(() => user.value?.username || '')
  const role = computed(() => user.value?.role || '')
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(username, password) {
    const res = await authApi.login(username, password)
    token.value = res.token
    user.value = res.user
    localStorage.setItem('token', res.token)
    localStorage.setItem('user', JSON.stringify(res.user))
  }

  async function register(username, password) {
    await authApi.register(username, password)
  }

  async function fetchUser() {
    try {
      const res = await authApi.getMe()
      user.value = res
      localStorage.setItem('user', JSON.stringify(res))
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    authApi.logout().catch(() => {})
  }

  // Admin user management actions (for UserManageView)
  async function getUsers(page = 1, pageSize = 20) {
    return await authApi.getUsers(page, pageSize)
  }

  async function createUser(data) {
    await authApi.createUser(data)
  }

  async function updateUser(userId, data) {
    await authApi.updateUser(userId, data)
  }

  async function deleteUser(userId) {
    await authApi.deleteUser(userId)
  }

  return { user, token, isLoggedIn, username, role, isAdmin, login, register, fetchUser, logout, getUsers, createUser, updateUser, deleteUser }
})
