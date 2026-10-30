import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Served from https://arthunya.github.io/cerop-console/console/ on GitHub Pages.
// CEROP_BASE=/ npm run dev serves it from the root during local work.
export default defineConfig({
  base: process.env.CEROP_BASE ?? '/cerop-console/console/',
  plugins: [react()],
  build: { target: 'es2020', chunkSizeWarningLimit: 900 },
})
