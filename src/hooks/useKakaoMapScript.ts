import { useEffect, useState } from 'react'

declare global {
  interface Window {
    kakao: any
  }
}

const KAKAO_MAP_KEY = import.meta.env.VITE_KAKAO_MAP_KEY

let loadPromise: Promise<void> | null = null

function loadKakaoMapScript(): Promise<void> {
  if (window.kakao?.maps) return Promise.resolve()
  if (loadPromise) return loadPromise

  loadPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_MAP_KEY}&autoload=false`
    script.async = true
    script.onload = () => window.kakao.maps.load(() => resolve())
    script.onerror = () => reject(new Error('카카오맵 스크립트를 불러오지 못했습니다.'))
    document.head.appendChild(script)
  })

  return loadPromise
}

export function useKakaoMapScript() {
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'error' | 'no-key'>('idle')

  useEffect(() => {
    if (!KAKAO_MAP_KEY) {
      setStatus('no-key')
      return
    }
    setStatus('loading')
    loadKakaoMapScript()
      .then(() => setStatus('ready'))
      .catch(() => setStatus('error'))
  }, [])

  return status
}
