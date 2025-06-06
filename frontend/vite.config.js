import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/static',
  plugins: [vue()],
  build: {
    outDir: '../backend/static'
  }
})
