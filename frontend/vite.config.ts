import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/dsF2025/',
  server: {
    fs: {
      // Allow serving files from one level up (to access ../data)
      allow: ['..'],
    },
  },
})
