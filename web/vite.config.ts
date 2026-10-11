import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// base './' keeps every asset URL relative, so dist/ works from any sub-path.
export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } },
  },
  build: { target: 'es2022', chunkSizeWarningLimit: 900 },
})
