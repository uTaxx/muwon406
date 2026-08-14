interface ReviewQualityFilterProps {
  excludeReviewEvents: boolean
  excludeSponsoredHeavy: boolean
  onExcludeReviewEventsChange: (value: boolean) => void
  onExcludeSponsoredHeavyChange: (value: boolean) => void
}

export function ReviewQualityFilter({
  excludeReviewEvents,
  excludeSponsoredHeavy,
  onExcludeReviewEventsChange,
  onExcludeSponsoredHeavyChange,
}: ReviewQualityFilterProps) {
  return (
    <div className="flex flex-wrap gap-x-5 gap-y-2">
      <label className="flex cursor-pointer items-center gap-1.5 text-xs text-neutral-600">
        <input
          type="checkbox"
          checked={excludeReviewEvents}
          onChange={(e) => onExcludeReviewEventsChange(e.target.checked)}
        />
        체험단/협찬 리뷰 이벤트 진행 중인 곳 제외
      </label>
      <label className="flex cursor-pointer items-center gap-1.5 text-xs text-neutral-600">
        <input
          type="checkbox"
          checked={excludeSponsoredHeavy}
          onChange={(e) => onExcludeSponsoredHeavyChange(e.target.checked)}
        />
        광고성 리뷰 비율 높은 곳 제외
      </label>
    </div>
  )
}
