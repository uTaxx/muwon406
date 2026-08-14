import type { SearchProvider } from './types'
import type { Restaurant, SearchFilters } from '../../types/restaurant'
import { filterAndSortRestaurants } from '../../utils/filterRestaurants'

interface RestaurantsFeed {
  updatedAt: string
  restaurants: Restaurant[]
}

let cachedFeed: RestaurantsFeed | null = null

// n8n이 주기적으로 이 저장소의 public/data/restaurants.json 파일을 커밋하면,
// GitHub Pages 배포 시 그대로 정적 파일로 포함되어 이 provider가 읽어옵니다.
export const liveProvider: SearchProvider = {
  name: 'live',
  async search(filters: SearchFilters) {
    if (!cachedFeed) {
      const response = await fetch(`${import.meta.env.BASE_URL}data/restaurants.json`)
      if (!response.ok) {
        throw new Error('데이터 파일을 불러오지 못했습니다 (public/data/restaurants.json).')
      }
      cachedFeed = (await response.json()) as RestaurantsFeed
    }

    return filterAndSortRestaurants(cachedFeed.restaurants, filters)
  },
}
