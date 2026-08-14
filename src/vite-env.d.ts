/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DATA_SOURCE?: string
  readonly VITE_KAKAO_MAP_KEY?: string
  readonly VITE_KAKAO_REST_API_KEY?: string
  readonly VITE_NAVER_CLIENT_ID?: string
  readonly VITE_NAVER_CLIENT_SECRET?: string
  readonly VITE_GOOGLE_PLACES_KEY?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
