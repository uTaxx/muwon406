import { useEffect, useRef } from 'react'
import type { Restaurant } from '../types/restaurant'
import { useKakaoMapScript } from '../hooks/useKakaoMapScript'

interface MapViewProps {
  restaurants: Restaurant[]
  selectedId?: string
  onSelect: (restaurant: Restaurant) => void
}

const SEOUL_CENTER = { lat: 37.5665, lng: 126.978 }

export function MapView({ restaurants, selectedId, onSelect }: MapViewProps) {
  const status = useKakaoMapScript()
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<any>(null)
  const markersRef = useRef<any[]>([])

  useEffect(() => {
    if (status !== 'ready' || !containerRef.current || mapRef.current) return
    const kakao = window.kakao
    mapRef.current = new kakao.maps.Map(containerRef.current, {
      center: new kakao.maps.LatLng(SEOUL_CENTER.lat, SEOUL_CENTER.lng),
      level: 6,
    })
  }, [status])

  useEffect(() => {
    if (status !== 'ready' || !mapRef.current) return
    const kakao = window.kakao
    const map = mapRef.current

    markersRef.current.forEach((marker) => marker.setMap(null))
    markersRef.current = []

    if (restaurants.length === 0) return

    const bounds = new kakao.maps.LatLngBounds()

    restaurants.forEach((place) => {
      const position = new kakao.maps.LatLng(place.lat, place.lng)
      const marker = new kakao.maps.Marker({ position, map })
      kakao.maps.event.addListener(marker, 'click', () => onSelect(place))
      markersRef.current.push(marker)
      bounds.extend(position)
    })

    map.setBounds(bounds)
  }, [restaurants, status, onSelect])

  useEffect(() => {
    if (status !== 'ready' || !mapRef.current || !selectedId) return
    const target = restaurants.find((r) => r.id === selectedId)
    if (!target) return
    const kakao = window.kakao
    mapRef.current.panTo(new kakao.maps.LatLng(target.lat, target.lng))
  }, [selectedId, restaurants, status])

  if (status === 'no-key') {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-neutral-300 bg-neutral-50 p-6 text-center">
        <p className="text-sm font-medium text-neutral-500">지도가 연결되어 있지 않아요</p>
        <p className="max-w-xs text-xs text-neutral-400">
          .env 파일에 VITE_KAKAO_MAP_KEY를 설정하면 실제 지도가 표시돼요. (.env.example 참고)
        </p>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-red-200 bg-red-50 p-6 text-center text-sm text-red-500">
        지도를 불러오지 못했어요. API 키를 확인해주세요.
      </div>
    )
  }

  return <div ref={containerRef} className="h-full w-full rounded-xl bg-neutral-100" />
}
