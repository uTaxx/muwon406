import type { Restaurant } from '../types/restaurant'
import { SPONSORED_HEAVY_THRESHOLD } from '../types/restaurant'
import { ReviewAnalysisPanel } from './ReviewAnalysisPanel'
import { estimateOwnerChange, getYearsInBusiness } from '../utils/businessInfo'

interface RestaurantCardProps {
  restaurant: Restaurant
  isFavorite: boolean
  isSelected: boolean
  reviewSampleSize: number
  onToggleFavorite: (id: string) => void
  onSelect: (restaurant: Restaurant) => void
}

export function RestaurantCard({
  restaurant,
  isFavorite,
  isSelected,
  reviewSampleSize,
  onToggleFavorite,
  onSelect,
}: RestaurantCardProps) {
  const yearsInBusiness = getYearsInBusiness(restaurant)
  const ownerChange = estimateOwnerChange(restaurant)

  return (
    <div
      onClick={() => onSelect(restaurant)}
      className={`cursor-pointer rounded-xl border bg-white p-4 shadow-sm transition-shadow hover:shadow-md ${
        isSelected ? 'border-brand-500 ring-1 ring-brand-500' : 'border-neutral-200'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-2xl">
            {restaurant.thumbnail}
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-1.5">
              <h3 className="font-semibold text-neutral-900">{restaurant.name}</h3>
              <span className="shrink-0 rounded bg-neutral-100 px-1.5 py-0.5 text-[11px] text-neutral-500">
                {restaurant.placeType}
              </span>
            </div>
            <p className="mt-0.5 text-xs text-neutral-500">
              {restaurant.category} · {restaurant.region}
            </p>
            <p className="text-xs text-neutral-400">{restaurant.address}</p>
            {(restaurant.hasReviewEvent || restaurant.sponsoredReviewRatio >= SPONSORED_HEAVY_THRESHOLD) && (
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {restaurant.hasReviewEvent && (
                  <span className="shrink-0 rounded bg-amber-50 px-1.5 py-0.5 text-[11px] font-medium text-amber-600">
                    체험단 진행중
                  </span>
                )}
                {restaurant.sponsoredReviewRatio >= SPONSORED_HEAVY_THRESHOLD && (
                  <span className="shrink-0 rounded bg-red-50 px-1.5 py-0.5 text-[11px] font-medium text-red-500">
                    광고성 리뷰 많음
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onToggleFavorite(restaurant.id)
          }}
          aria-label="즐겨찾기"
          className={`text-xl transition-transform hover:scale-110 ${
            isFavorite ? 'text-brand-500' : 'text-neutral-300'
          }`}
        >
          {isFavorite ? '★' : '☆'}
        </button>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
        <span className="font-medium text-brand-600">
          ★ {restaurant.rating > 0 ? restaurant.rating.toFixed(1) : '평점 없음'}
        </span>
        <span className="text-neutral-500">리뷰 {restaurant.reviewCount.toLocaleString()}</span>
        <span className="text-neutral-500">{restaurant.priceRange}</span>
        {restaurant.openHours && <span className="text-neutral-400">{restaurant.openHours}</span>}
        {restaurant.sponsoredReviewRatio > 0 && (
          <span className="text-neutral-400">광고성 리뷰 추정 {restaurant.sponsoredReviewRatio}%</span>
        )}
      </div>

      {(yearsInBusiness !== undefined || restaurant.hasPrivateRoom) && (
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-neutral-500">
          {yearsInBusiness !== undefined && (
            <span>
              업력 {yearsInBusiness}년차{restaurant.openedYear ? ` (${restaurant.openedYear}년 개업)` : ''}
            </span>
          )}
          {restaurant.hasPrivateRoom && (
            <span className="rounded bg-blue-50 px-1.5 py-0.5 font-medium text-blue-600">
              회식룸 있음{restaurant.roomCapacity ? ` · 최대 ${restaurant.roomCapacity}인` : ''}
            </span>
          )}
        </div>
      )}

      {ownerChange.likely && (
        <p className="mt-1 text-[11px] text-amber-600">
          ⚠ 사업자등록일({ownerChange.registeredYear}년) 기준 주인이 바뀌었을 가능성 (실제 이력이 아닌 추정치)
        </p>
      )}

      {restaurant.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {restaurant.tags.map((tag) => (
            <span key={tag} className="rounded-full bg-neutral-100 px-2 py-0.5 text-[11px] text-neutral-500">
              #{tag}
            </span>
          ))}
        </div>
      )}

      {isSelected && <ReviewAnalysisPanel restaurant={restaurant} sampleSize={reviewSampleSize} />}
    </div>
  )
}
