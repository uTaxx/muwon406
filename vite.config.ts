import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// GitHub Pages 프로젝트 사이트(https://<owner>.github.io/<repo>/)는
// 저장소 이름이 서브패스가 되므로, 프로덕션 빌드에서만 base를 맞춰줍니다.
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  base: mode === 'production' ? '/muwon406/' : '/',
}))
