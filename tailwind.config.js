/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // 민트/세이지 톤 팔레트 — 참고 스타일가이드의 파스텔 그린 primary를 기준으로 구성
        brand: {
          50: '#F0FBF6',
          100: '#DEF6EC',
          200: '#BFEEDC',
          300: '#95E0C0',
          400: '#68CBA0',
          500: '#42B385',
          600: '#2F9A6E',
          700: '#257A58',
          800: '#1F6248',
          900: '#1A4F3B',
        },
      },
      fontFamily: {
        sans: [
          'Pretendard',
          '-apple-system',
          'BlinkMacSystemFont',
          'system-ui',
          'Roboto',
          'Helvetica Neue',
          'Segoe UI',
          'Apple SD Gothic Neo',
          'Malgun Gothic',
          'sans-serif',
        ],
      },
      borderRadius: {
        card: '20px',
      },
      boxShadow: {
        soft: '0 1px 2px rgba(31, 41, 32, 0.04), 0 6px 16px -4px rgba(31, 41, 32, 0.08)',
        elevated: '0 2px 4px rgba(31, 41, 32, 0.05), 0 12px 28px -6px rgba(31, 41, 32, 0.14)',
      },
    },
  },
  plugins: [],
}
