import type { SearchProvider } from './types'
import { mockRestaurants } from '../../data/mockRestaurants'

export const mockProvider: SearchProvider = {
  name: 'mock',
  async search() {
    // 네트워크 호출을 흉내내기 위한 짧은 지연
    await new Promise((resolve) => setTimeout(resolve, 150))
    return mockRestaurants
  },
}
