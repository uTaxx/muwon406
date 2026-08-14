export type PlaceType = '맛집' | '카페'

export type CuisineCategory =
  | '숯불구이'
  | '철판구이'
  | '한식'
  | '중식'
  | '일식'
  | '양식'
  | '분식'
  | '고기/구이'
  | '해산물'
  | '치킨'
  | '디저트카페'
  | '브런치카페'
  | '베이커리카페'
  | '스터디카페'
  | '루프탑카페'

export type PriceRange = '~1만원' | '1~2만원' | '2~3만원' | '3만원~'

export type DataSource = 'mock' | 'kakao' | 'naver' | 'google'

export interface Restaurant {
  id: string
  name: string
  placeType: PlaceType
  category: CuisineCategory
  region: string
  address: string
  lat: number
  lng: number
  rating: number
  reviewCount: number
  priceRange: PriceRange
  tags: string[]
  phone?: string
  openHours?: string
  thumbnail: string
  source: DataSource
  /** 체험단/협찬 등 리뷰 이벤트를 현재 진행 중인 업체인지 여부 */
  hasReviewEvent: boolean
  /**
   * 전체 리뷰 중 광고성(협찬/체험단 대가성) 블로그 리뷰로 추정되는 비율 (0~100).
   * 실제 블로그 본문을 분석해 얻은 값이 아니라 참고용 추정치입니다.
   */
  sponsoredReviewRatio: number
}

export type SortKey = 'rating' | 'reviewCount' | 'distance' | 'priceAsc'

export interface SearchFilters {
  keyword: string
  region: string
  placeType: PlaceType | '전체'
  categories: CuisineCategory[]
  sortBy: SortKey
  /** 리뷰 이벤트(체험단/협찬)를 진행 중인 곳 제외 */
  excludeReviewEvents: boolean
  /** 광고성 리뷰 추정 비율이 높은 곳 제외 (기준: 40% 이상) */
  excludeSponsoredHeavy: boolean
}

export const SPONSORED_HEAVY_THRESHOLD = 40
