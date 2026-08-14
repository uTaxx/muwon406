import { useMemo } from 'react'
import type { Restaurant } from '../types/restaurant'
import { generateReviews } from '../utils/generateReviews'

interface ReviewAnalysisPanelProps {
  restaurant: Restaurant
  sampleSize: number
}

export function ReviewAnalysisPanel({ restaurant, sampleSize }: ReviewAnalysisPanelProps) {
  const reviews = useMemo(() => generateReviews(restaurant, sampleSize), [restaurant, sampleSize])
  const sponsoredCount = reviews.filter((review) => review.isSponsored).length
  const sponsoredRatio = reviews.length > 0 ? Math.round((sponsoredCount / reviews.length) * 100) : 0

  return (
    <div className="mt-3 border-t border-neutral-100 pt-3" onClick={(e) => e.stopPropagation()}>
      <div className="mb-2 flex items-center justify-between">
        <p className="text-xs font-medium text-neutral-600">최근 리뷰 {reviews.length}개 분석 결과</p>
        <p className="text-xs text-neutral-500">
          광고성 추정 <span className="font-semibold text-red-500">{sponsoredCount}개 ({sponsoredRatio}%)</span>
        </p>
      </div>
      <ul className="max-h-72 space-y-2 overflow-y-auto pr-1">
        {reviews.map((review) => (
          <li key={review.id} className="rounded-lg bg-neutral-50 p-2.5 text-xs">
            <div className="mb-1 flex flex-wrap items-center justify-between gap-x-2 gap-y-1">
              <span className="font-medium text-neutral-700">{review.author}</span>
              <div className="flex items-center gap-1.5">
                <span className="text-neutral-400">
                  {review.dateLabel} · ★{review.rating.toFixed(1)}
                </span>
                {review.isSponsored ? (
                  <span className="shrink-0 rounded bg-red-50 px-1.5 py-0.5 font-medium text-red-500">
                    광고성
                  </span>
                ) : (
                  <span className="shrink-0 rounded bg-neutral-100 px-1.5 py-0.5 text-neutral-500">일반</span>
                )}
              </div>
            </div>
            <p className="text-neutral-600">{review.content}</p>
          </li>
        ))}
      </ul>
    </div>
  )
}
