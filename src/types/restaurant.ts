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
}

export type SortKey = 'rating' | 'reviewCount' | 'distance' | 'priceAsc'

export interface SearchFilters {
  keyword: string
  region: string
  placeType: PlaceType | '전체'
  categories: CuisineCategory[]
  sortBy: SortKey
}
