import type { Restaurant, SearchFilters } from '../types/restaurant'
import { SPONSORED_HEAVY_THRESHOLD } from '../types/restaurant'

function matchesKeyword(place: Restaurant, keyword: string): boolean {
  if (!keyword.trim()) return true
  const needle = keyword.trim().toLowerCase()
  return (
    place.name.toLowerCase().includes(needle) ||
    place.category.toLowerCase().includes(needle) ||
    place.tags.some((tag) => tag.toLowerCase().includes(needle))
  )
}

function matchesRegion(place: Restaurant, region: string): boolean {
  if (!region.trim()) return true
  const needle = region.trim().toLowerCase()
  return (
    place.region.toLowerCase().includes(needle) ||
    place.address.toLowerCase().includes(needle)
  )
}

function priceRangeRank(range: Restaurant['priceRange']): number {
  switch (range) {
    case '~1만원':
      return 0
    case '1~2만원':
      return 1
    case '2~3만원':
      return 2
    case '3만원~':
      return 3
  }
}

function distanceFrom(place: Restaurant, origin?: { lat: number; lng: number }): number {
  if (!origin) return 0
  const dLat = place.lat - origin.lat
  const dLng = place.lng - origin.lng
  return Math.sqrt(dLat * dLat + dLng * dLng)
}

export function filterAndSortRestaurants(
  places: Restaurant[],
  filters: SearchFilters,
  origin?: { lat: number; lng: number },
): Restaurant[] {
  const filtered = places.filter((place) => {
    if (filters.placeType !== '전체' && place.placeType !== filters.placeType) return false
    if (filters.categories.length > 0 && !filters.categories.includes(place.category)) return false
    if (!matchesKeyword(place, filters.keyword)) return false
    if (!matchesRegion(place, filters.region)) return false
    if (filters.excludeReviewEvents && place.hasReviewEvent) return false
    if (filters.excludeSponsoredHeavy && place.sponsoredReviewRatio >= SPONSORED_HEAVY_THRESHOLD) return false
    if (filters.requirePrivateRoom && !place.hasPrivateRoom) return false
    return true
  })

  const sorted = [...filtered].sort((a, b) => {
    switch (filters.sortBy) {
      case 'rating':
        return b.rating - a.rating
      case 'reviewCount':
        return b.reviewCount - a.reviewCount
      case 'priceAsc':
        return priceRangeRank(a.priceRange) - priceRangeRank(b.priceRange)
      case 'distance':
        return distanceFrom(a, origin) - distanceFrom(b, origin)
      default:
        return 0
    }
  })

  return sorted
}
