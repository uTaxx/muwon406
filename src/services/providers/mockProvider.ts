import type { SearchProvider } from './types'
import type { SearchFilters } from '../../types/restaurant'
import { mockRestaurants } from '../../data/mockRestaurants'
import { filterAndSortRestaurants } from '../../utils/filterRestaurants'

export const mockProvider: SearchProvider = {
  name: 'mock',
  async search(filters: SearchFilters) {
    // 네트워크 호출을 흉내내기 위한 짧은 지연
    await new Promise((resolve) => setTimeout(resolve, 150))
    return filterAndSortRestaurants(mockRestaurants, filters)
  },
}
