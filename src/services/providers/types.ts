import type { Restaurant, SearchFilters } from '../../types/restaurant'

export interface SearchProvider {
  readonly name: string
  search(filters: SearchFilters): Promise<Restaurant[]>
}
