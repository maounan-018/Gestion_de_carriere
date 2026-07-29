import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

// Front « La Courbe » — sert sur :3000, parle uniquement au backend via /api (proxy).
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    // 3000 est pris par un autre projet local (ObjectifSMART) → port assigné automatiquement.
    port: process.env.PORT ? Number(process.env.PORT) : 3001,
    strictPort: false,
    // Proxy /api → backend FastAPI (:5001 par défaut ; surchargeable via
    // VITE_PROXY_TARGET pour pointer un autre backend local, ex. :5002).
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:5001',
        changeOrigin: true,
      },
    },
  },
})
