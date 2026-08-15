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

export type DataSource = 'mock' | 'live' | 'kakao' | 'naver' | 'google'

export type BusinessStatus = '계속사업자' | '휴업자' | '폐업자'

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
  /** 개업 연도 (업력 계산용). 출처가 없으면 undefined */
  openedYear?: number
  /**
   * 사업자등록일 (YYYY-MM). 국세청 사업자등록정보 진위확인 API(공공데이터포털)로
   * 조회 가능한 값입니다. 다만 이 API는 "이전 사업자가 언제 폐업했고 새 사업자가
   * 언제 등록했는지"에 대한 이력을 제공하지 않아, 개업 연도와 함께 써서 주인
   * 변경 여부를 추정하는 용도로만 사용합니다.
   */
  businessRegistrationDate?: string
  businessRegistrationNumber?: string
  businessStatus?: BusinessStatus
  /** 회식/모임용 별도 룸 보유 여부 */
  hasPrivateRoom: boolean
  /** 룸 최대 수용 인원. hasPrivateRoom이 true일 때만 의미 있음 */
  roomCapacity?: number
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
  /** 회식용 룸이 있는 곳만 보기 */
  requirePrivateRoom: boolean
}

export const SPONSORED_HEAVY_THRESHOLD = 40

/**
 * 개업 연도와 사업자등록일(연도) 차이가 이 값 이상이면 "주인이 바뀌었을 가능성"으로
 * 추정합니다. 실제 이력 데이터가 아닌 정황상 추정치임을 UI에서 항상 명시해야 합니다.
 */
export const OWNER_CHANGE_YEAR_GAP_THRESHOLD = 2

export const DEFAULT_REVIEW_SAMPLE_SIZE = 20
export const MIN_REVIEW_SAMPLE_SIZE = 5
export const MAX_REVIEW_SAMPLE_SIZE = 50

export interface Review {
  id: string
  author: string
  content: string
  /** 실제 블로그 리뷰에는 별점이 없어 데모(mock) 데이터에서만 채워집니다 */
  rating?: number
  dateLabel: string
  /** 광고 문구 패턴 분류기가 판단한 협찬/광고성 리뷰 여부 */
  isSponsored: boolean
  /** 실제 블로그 리뷰 원문 링크 (데모 데이터에는 없음) */
  link?: string
}
