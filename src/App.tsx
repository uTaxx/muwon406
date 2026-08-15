import { useEffect, useMemo, useState } from 'react'
import type { Restaurant, SearchFilters } from './types/restaurant'
import { DEFAULT_REVIEW_SAMPLE_SIZE } from './types/restaurant'
import { getActiveProvider } from './services/providers'
import { filterAndSortRestaurants } from './utils/filterRestaurants'
import { useFavorites } from './hooks/useFavorites'
import { SearchBar } from './components/SearchBar'
import { CategoryFilter } from './components/CategoryFilter'
import { ReviewQualityFilter } from './components/ReviewQualityFilter'
import { ReviewSampleSizeControl } from './components/ReviewSampleSizeControl'
import { RoomFilter } from './components/RoomFilter'
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
  excludeReviewEvents: false,
  excludeSponsoredHeavy: false,
  requirePrivateRoom: false,
}

export default function App() {
  const [filters, setFilters] = useState<SearchFilters>(DEFAULT_FILTERS)
  const [committedQuery, setCommittedQuery] = useState({ keyword: '', region: '' })
  const [rawResults, setRawResults] = useState<Restaurant[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | undefined>()
  const [selected, setSelected] = useState<Restaurant | undefined>()
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false)
  const [reviewSampleSize, setReviewSampleSize] = useState(DEFAULT_REVIEW_SAMPLE_SIZE)

  const { favoriteIds, toggleFavorite } = useFavorites()
  const provider = useMemo(() => getActiveProvider(), [])

  // 검색 버튼(또는 Enter)을 눌러 committedQuery가 바뀔 때만 provider를 호출합니다.
  // 입력창에 글자를 치는 동안에는 호출하지 않아, 타이핑 중간의 검색어로 API가
  // 반복 호출되거나 어중간한 검색어 결과가 시트에 쌓이는 것을 막습니다. 카테고리·정렬·
  // 부가 필터는 이미 받아온 rawResults를 아래에서 다시 걸러내기만 합니다.
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(undefined)

    provider
      .search(committedQuery.keyword, committedQuery.region)
      .then((results) => {
        if (!cancelled) setRawResults(results)
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
  }, [committedQuery, provider])

  function runSearch() {
    setCommittedQuery({ keyword: filters.keyword, region: filters.region })
  }

  const restaurants = useMemo(
    () => filterAndSortRestaurants(rawResults, filters),
    [rawResults, filters],
  )

  const visibleRestaurants = showFavoritesOnly
    ? restaurants.filter((r) => favoriteIds.includes(r.id))
    : restaurants

  const favoritePlaces = restaurants.filter((r) => favoriteIds.includes(r.id))

  function toggleSelected(restaurant: Restaurant) {
    setSelected((prev) => (prev?.id === restaurant.id ? undefined : restaurant))
  }

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6">
          <h1 className="text-2xl font-extrabold tracking-tight text-stone-900">
            🍽️ 맛집·카페 검색 대시보드
          </h1>
          <p className="mt-1 text-sm text-stone-400">
            데이터 소스: <span className="font-semibold text-brand-600">{provider.name}</span>
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-4 px-4 py-6 sm:px-6">
        <div className="rounded-card border border-stone-200 bg-white p-5 shadow-soft">
          <SearchBar
            keyword={filters.keyword}
            region={filters.region}
            onKeywordChange={(keyword) => setFilters((f) => ({ ...f, keyword }))}
            onRegionChange={(region) => setFilters((f) => ({ ...f, region }))}
            onSearch={runSearch}
          />
          <div className="mt-4">
            <CategoryFilter
              placeType={filters.placeType}
              categories={filters.categories}
              onPlaceTypeChange={(placeType) => setFilters((f) => ({ ...f, placeType }))}
              onCategoriesChange={(categories) => setFilters((f) => ({ ...f, categories }))}
            />
          </div>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-stone-100 pt-3">
            <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
              <ReviewQualityFilter
                excludeReviewEvents={filters.excludeReviewEvents}
                excludeSponsoredHeavy={filters.excludeSponsoredHeavy}
                onExcludeReviewEventsChange={(excludeReviewEvents) =>
                  setFilters((f) => ({ ...f, excludeReviewEvents }))
                }
                onExcludeSponsoredHeavyChange={(excludeSponsoredHeavy) =>
                  setFilters((f) => ({ ...f, excludeSponsoredHeavy }))
                }
              />
              <RoomFilter
                requirePrivateRoom={filters.requirePrivateRoom}
                onChange={(requirePrivateRoom) => setFilters((f) => ({ ...f, requirePrivateRoom }))}
              />
            </div>
            <ReviewSampleSizeControl value={reviewSampleSize} onChange={setReviewSampleSize} />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_420px]">
          <div className="order-2 h-[420px] lg:order-1 lg:h-[calc(100vh-260px)] lg:min-h-[420px]">
            <MapView restaurants={visibleRestaurants} selectedId={selected?.id} onSelect={setSelected} />
          </div>

          <div className="order-1 space-y-4 lg:order-2">
            <div className="rounded-card border border-stone-200 bg-white p-4 shadow-soft">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-stone-700">즐겨찾기</h2>
                <label className="flex items-center gap-1.5 text-xs text-stone-500">
                  <input
                    type="checkbox"
                    className="accent-brand-500"
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

            <div className="rounded-card border border-stone-200 bg-white p-4 shadow-soft">
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
                  reviewSampleSize={reviewSampleSize}
                  loading={loading}
                  error={error}
                  onToggleFavorite={toggleFavorite}
                  onSelect={toggleSelected}
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
