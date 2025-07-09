import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import legacy from '@vitejs/plugin-legacy'

export default defineConfig({
  plugins: [
    react(),
    legacy({
      targets: ['defaults', 'not IE 11']
    })
  ],
  define: {
    global: 'globalThis',
  },
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: 'http://localhost:2104',
        changeOrigin: true,
        secure: false,
      }
    }
  }
}) 