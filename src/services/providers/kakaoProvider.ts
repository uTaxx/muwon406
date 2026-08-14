import type { SearchProvider } from './types'
import type { Restaurant, SearchFilters } from '../../types/restaurant'

const KAKAO_REST_API_KEY = import.meta.env.VITE_KAKAO_REST_API_KEY as string | undefined

interface KakaoDocument {
  id: string
  place_name: string
  category_name: string
  road_address_name: string
  address_name: string
  x: string // lng
  y: string // lat
  phone: string
  place_url: string
}

function toRestaurant(doc: KakaoDocument): Restaurant {
  const categoryTail = doc.category_name.split(' > ').pop() ?? '기타'
  return {
    id: `kakao-${doc.id}`,
    name: doc.place_name,
    placeType: doc.category_name.includes('카페') ? '카페' : '맛집',
    // 카카오 로컬 API는 세부 업종만 제공하므로 앱의 CuisineCategory와 완전히
    // 일치하지 않을 수 있습니다. 필요 시 매핑 테이블을 추가하세요.
    category: categoryTail as Restaurant['category'],
    region: doc.address_name.split(' ').slice(0, 2).join(' '),
    address: doc.road_address_name || doc.address_name,
    lat: Number(doc.y),
    lng: Number(doc.x),
    // 카카오 로컬 API는 평점/리뷰 수를 제공하지 않습니다.
    rating: 0,
    reviewCount: 0,
    priceRange: '~1만원',
    tags: [],
    phone: doc.phone || undefined,
    thumbnail: doc.category_name.includes('카페') ? '☕' : '🍽️',
    source: 'kakao',
  }
}

export const kakaoProvider: SearchProvider = {
  name: 'kakao',
  async search(filters: SearchFilters) {
    if (!KAKAO_REST_API_KEY) {
      throw new Error(
        '카카오 검색을 사용하려면 VITE_KAKAO_REST_API_KEY 환경변수를 설정하세요 (.env.example 참고).',
      )
    }

    const query = [filters.keyword, filters.region].filter(Boolean).join(' ') || '맛집'
    const url = new URL('https://dapi.kakao.com/v2/local/search/keyword.json')
    url.searchParams.set('query', query)
    url.searchParams.set('size', '15')

    const response = await fetch(url.toString(), {
      headers: { Authorization: `KakaoAK ${KAKAO_REST_API_KEY}` },
    })

    if (!response.ok) {
      throw new Error(`카카오 로컬 API 요청 실패: ${response.status}`)
    }

    const data = (await response.json()) as { documents: KakaoDocument[] }
    return data.documents.map(toRestaurant)
  },
}
