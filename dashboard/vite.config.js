import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 4297,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5297',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:5297',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
