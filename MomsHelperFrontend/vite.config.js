import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  root: 'src',
  plugins: [react()],
  base: './',   // <-- это заставляет ссылки на CSS/JS быть относительными
  server: {
    host: '0.0.0.0',
    port: 3000
  },
  build: {
    outDir: '../dist',
    emptyOutDir: true
  }
})
