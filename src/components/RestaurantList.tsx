import type { Restaurant } from '../types/restaurant'
import { RestaurantCard } from './RestaurantCard'

interface RestaurantListProps {
  restaurants: Restaurant[]
  favoriteIds: string[]
  selectedId?: string
  reviewSampleSize: number
  loading: boolean
  error?: string
  onToggleFavorite: (id: string) => void
  onSelect: (restaurant: Restaurant) => void
}

function RestaurantGroup({
  restaurants,
  favoriteIds,
  selectedId,
  reviewSampleSize,
  onToggleFavorite,
  onSelect,
}: Omit<RestaurantListProps, 'loading' | 'error'>) {
  return (
    <div className="space-y-3">
      {restaurants.map((restaurant) => (
        <RestaurantCard
          key={restaurant.id}
          restaurant={restaurant}
          isFavorite={favoriteIds.includes(restaurant.id)}
          isSelected={restaurant.id === selectedId}
          reviewSampleSize={reviewSampleSize}
          onToggleFavorite={onToggleFavorite}
          onSelect={onSelect}
        />
      ))}
    </div>
  )
}

export function RestaurantList({
  restaurants,
  favoriteIds,
  selectedId,
  reviewSampleSize,
  loading,
  error,
  onToggleFavorite,
  onSelect,
}: RestaurantListProps) {
  if (loading) {
    return <div className="py-16 text-center text-sm text-stone-400">검색 중...</div>
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-600">{error}</div>
    )
  }

  if (restaurants.length === 0) {
    return (
      <div className="py-16 text-center text-sm text-stone-400">
        조건에 맞는 맛집/카페가 없어요. 필터를 조정해보세요.
      </div>
    )
  }

  const restaurantsOnly = restaurants.filter((r) => r.placeType === '맛집')
  const cafesOnly = restaurants.filter((r) => r.placeType === '카페')
  const isMixed = restaurantsOnly.length > 0 && cafesOnly.length > 0

  if (!isMixed) {
    return (
      <RestaurantGroup
        restaurants={restaurants}
        favoriteIds={favoriteIds}
        selectedId={selectedId}
        reviewSampleSize={reviewSampleSize}
        onToggleFavorite={onToggleFavorite}
        onSelect={onSelect}
      />
    )
  }

  return (
    <div className="space-y-6">
      <section>
        <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-stone-500">
          🍽️ 맛집 <span className="text-stone-400">{restaurantsOnly.length}곳</span>
        </h3>
        <RestaurantGroup
          restaurants={restaurantsOnly}
          favoriteIds={favoriteIds}
          selectedId={selectedId}
          reviewSampleSize={reviewSampleSize}
          onToggleFavorite={onToggleFavorite}
          onSelect={onSelect}
        />
      </section>
      <section>
        <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-stone-500">
          ☕ 카페 <span className="text-stone-400">{cafesOnly.length}곳</span>
        </h3>
        <RestaurantGroup
          restaurants={cafesOnly}
          favoriteIds={favoriteIds}
          selectedId={selectedId}
          reviewSampleSize={reviewSampleSize}
          onToggleFavorite={onToggleFavorite}
          onSelect={onSelect}
        />
      </section>
    </div>
  )
}
