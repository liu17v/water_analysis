import { defineStore } from 'pinia'
import api from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    token: localStorage.getItem('token') || '',
  }),
  getters: {
    isLoggedIn: (state) => !!state.token && !!state.user,
    username: (state) => state.user?.username || '',
    role: (state) => state.user?.role || '',
    isAdmin: (state) => state.user?.role === 'admin',
  },
  actions: {
    async login(username, password) {
      const res = await api.login(username, password)
      this.token = res.token
      this.user = res.user
      localStorage.setItem('token', res.token)
      localStorage.setItem('user', JSON.stringify(res.user))
    },
    async register(username, password) {
      await api.register(username, password)
    },
    async fetchUser() {
      try {
        const res = await api.getMe()
        this.user = res
        localStorage.setItem('user', JSON.stringify(res))
      } catch {
        this.logout()
      }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      api.logout().catch(() => {})
    },
  },
})
