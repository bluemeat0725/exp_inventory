import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    // 为环境变量设置默认值
    'import.meta.env.VITE_API_URL': JSON.stringify(
      process.env.VITE_API_URL || 'http://localhost:8000'
    ),
    'import.meta.env.VITE_LOGIN_COUNTDOWN': JSON.stringify(
      process.env.VITE_LOGIN_COUNTDOWN || '0'
    ),
  },
})
