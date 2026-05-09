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
      '/api': { target: 'http://localhost:8000', timeout: 600000, proxyTimeout: 600000 },
      '/reports': { target: 'http://localhost:8000', timeout: 600000, proxyTimeout: 600000 },
      '/3d': { target: 'http://localhost:8000', timeout: 600000, proxyTimeout: 600000 },
    },
  },
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
}))
