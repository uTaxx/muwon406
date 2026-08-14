import { useEffect, useMemo, useState } from 'react'
import type { Restaurant, SearchFilters } from './types/restaurant'
import { getActiveProvider } from './services/providers'
import { useFavorites } from './hooks/useFavorites'
import { SearchBar } from './components/SearchBar'
import { CategoryFilter } from './components/CategoryFilter'
import { SortControl } from './components/SortControl'
import { RestaurantList } from './components/RestaurantList'
import { MapView } from './components/MapView'
import { FavoritesPanel } from './components/FavoritesPanel'

const DEFAULT_FILTERS: SearchFilters = {
  keyword: '',
  region: '',
  placeType: '전체',
  categories: [],
  sortBy: 'rating',
}

export default function App() {
  const [filters, setFilters] = useState<SearchFilters>(DEFAULT_FILTERS)
  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | undefined>()
  const [selected, setSelected] = useState<Restaurant | undefined>()
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false)

  const { favoriteIds, toggleFavorite } = useFavorites()
  const provider = useMemo(() => getActiveProvider(), [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(undefined)

    provider
      .search(filters)
      .then((results) => {
        if (!cancelled) setRestaurants(results)
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [filters, provider])

  const visibleRestaurants = showFavoritesOnly
    ? restaurants.filter((r) => favoriteIds.includes(r.id))
    : restaurants

  const favoritePlaces = restaurants.filter((r) => favoriteIds.includes(r.id))

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="border-b border-neutral-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6">
          <h1 className="text-xl font-bold text-neutral-900">🍽️ 맛집·카페 검색 대시보드</h1>
          <p className="mt-0.5 text-sm text-neutral-400">
            데이터 소스: <span className="font-medium text-brand-600">{provider.name}</span>
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-4 px-4 py-6 sm:px-6">
        <div className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
          <SearchBar
            keyword={filters.keyword}
            region={filters.region}
            onKeywordChange={(keyword) => setFilters((f) => ({ ...f, keyword }))}
            onRegionChange={(region) => setFilters((f) => ({ ...f, region }))}
          />
          <div className="mt-4">
            <CategoryFilter
              placeType={filters.placeType}
              categories={filters.categories}
              onPlaceTypeChange={(placeType) => setFilters((f) => ({ ...f, placeType }))}
              onCategoriesChange={(categories) => setFilters((f) => ({ ...f, categories }))}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_420px]">
          <div className="order-2 h-[420px] lg:order-1 lg:h-[calc(100vh-260px)] lg:min-h-[420px]">
            <MapView restaurants={visibleRestaurants} selectedId={selected?.id} onSelect={setSelected} />
          </div>

          <div className="order-1 space-y-4 lg:order-2">
            <div className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-neutral-700">즐겨찾기</h2>
                <label className="flex items-center gap-1.5 text-xs text-neutral-500">
                  <input
                    type="checkbox"
                    checked={showFavoritesOnly}
                    onChange={(e) => setShowFavoritesOnly(e.target.checked)}
                  />
                  찜한 곳만 보기
                </label>
              </div>
              <FavoritesPanel
                favorites={favoritePlaces}
                onSelect={setSelected}
                onRemove={toggleFavorite}
              />
            </div>

            <div className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
              <div className="mb-3">
                <SortControl
                  value={filters.sortBy}
                  onChange={(sortBy) => setFilters((f) => ({ ...f, sortBy }))}
                  resultCount={visibleRestaurants.length}
                />
              </div>
              <div className="max-h-[calc(100vh-460px)] min-h-[240px] overflow-y-auto pr-1">
                <RestaurantList
                  restaurants={visibleRestaurants}
                  favoriteIds={favoriteIds}
                  selectedId={selected?.id}
                  loading={loading}
                  error={error}
                  onToggleFavorite={toggleFavorite}
                  onSelect={setSelected}
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
