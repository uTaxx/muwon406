import type { SearchProvider } from './types'
import type { Restaurant } from '../../types/restaurant'

const WEBHOOK_URL = import.meta.env.VITE_N8N_SEARCH_WEBHOOK_URL as string | undefined

// n8n 웹훅 응답: 구글시트에서 그대로 읽어온 값이라 타입이 느슨합니다
// (문자열 "TRUE"/빈 문자열 등). 여기서 Restaurant 타입에 맞게 정규화합니다.
interface RawRow {
  id: string
  name: string
  placeType: string
  category: string
  region: string
  address: string
  lat: number | string
  lng: number | string
  rating: number | string
  reviewCount: number | string
  priceRange: string
  tags: string
  phone?: string
  openHours?: string
  thumbnail: string
  source: string
  hasReviewEvent: boolean | string
  sponsoredReviewRatio: number | string
  openedYear?: number | string
  businessRegistrationDate?: string
  businessRegistrationNumber?: string
  businessStatus?: string
  hasPrivateRoom: boolean | string
  roomCapacity?: number | string
}

function toBool(value: boolean | string | undefined): boolean {
  if (typeof value === 'boolean') return value
  return String(value).trim().toUpperCase() === 'TRUE'
}

function toNumber(value: number | string | undefined, fallback = 0): number {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

function toOptionalNumber(value: number | string | undefined): number | undefined {
  if (value === undefined || value === '') return undefined
  const n = Number(value)
  return Number.isFinite(n) ? n : undefined
}

function toOptionalString(value: string | undefined): string | undefined {
  return value && value.trim() !== '' ? value : undefined
}

function normalize(row: RawRow): Restaurant {
  let tags: string[] = []
  try {
    tags = JSON.parse(row.tags || '[]')
  } catch {
    tags = []
  }

  return {
    id: row.id,
    name: row.name,
    placeType: row.placeType as Restaurant['placeType'],
    category: row.category as Restaurant['category'],
    region: row.region,
    address: row.address,
    lat: toNumber(row.lat),
    lng: toNumber(row.lng),
    rating: toNumber(row.rating),
    reviewCount: toNumber(row.reviewCount),
    priceRange: row.priceRange as Restaurant['priceRange'],
    tags,
    phone: toOptionalString(row.phone),
    openHours: toOptionalString(row.openHours),
    thumbnail: row.thumbnail,
    source: 'live',
    hasReviewEvent: toBool(row.hasReviewEvent),
    sponsoredReviewRatio: toNumber(row.sponsoredReviewRatio),
    openedYear: toOptionalNumber(row.openedYear),
    businessRegistrationDate: toOptionalString(row.businessRegistrationDate),
    businessRegistrationNumber: toOptionalString(row.businessRegistrationNumber),
    businessStatus: toOptionalString(row.businessStatus) as Restaurant['businessStatus'],
    hasPrivateRoom: toBool(row.hasPrivateRoom),
    roomCapacity: toOptionalNumber(row.roomCapacity),
  }
}

// n8n 웹훅 하나가 검색/누적 저장을 모두 처리합니다:
// keyword/region이 있으면 카카오 실시간 검색 후 구글시트에 병합 저장하고 그 결과를 반환하고,
// 둘 다 없으면 지금까지 시트에 쌓인 전체 목록을 반환합니다 (초기 화면용).
export const liveProvider: SearchProvider = {
  name: 'live',
  async search(keyword: string, region: string) {
    if (!WEBHOOK_URL) {
      throw new Error(
        'n8n 검색 웹훅 URL이 설정되지 않았습니다. VITE_N8N_SEARCH_WEBHOOK_URL 환경변수를 설정하세요 (.env.example 참고).',
      )
    }

    const url = new URL(WEBHOOK_URL)
    if (keyword) url.searchParams.set('keyword', keyword)
    if (region) url.searchParams.set('region', region)

    const response = await fetch(url.toString())
    if (!response.ok) {
      throw new Error(`검색 요청 실패: ${response.status}`)
    }

    // 카카오 검색 결과가 0건이면 n8n 워크플로우가 빈 본문을 응답합니다.
    // JSON.parse('')는 예외를 던지므로, 결과 없음으로 취급합니다.
    const text = await response.text()
    if (!text.trim()) return []

    const data = JSON.parse(text) as { restaurants: RawRow[] }
    return (data.restaurants ?? []).map(normalize)
  },
}
