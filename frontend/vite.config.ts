import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,  // Listen on all addresses (needed for Docker)
    port: 5173,
    watch: {
      usePolling: true  // Needed for file watching in Docker on Windows
    }
  }
})
