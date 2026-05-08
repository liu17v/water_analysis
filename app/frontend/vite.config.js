import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
  ],
  base: mode === 'production' ? '/static/' : '/',
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/reports': 'http://localhost:8000',
    },
  },
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
}))
