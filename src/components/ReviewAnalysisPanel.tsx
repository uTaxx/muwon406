import { useEffect, useState } from 'react'
import type { Restaurant, Review } from '../types/restaurant'
import { generateReviews } from '../utils/generateReviews'
import { fetchLiveReviews, hasLiveReviews } from '../services/reviewProvider'

interface ReviewAnalysisPanelProps {
  restaurant: Restaurant
  sampleSize: number
}

export function ReviewAnalysisPanel({ restaurant, sampleSize }: ReviewAnalysisPanelProps) {
  const [reviews, setReviews] = useState<Review[]>([])
  const [loading, setLoading] = useState(hasLiveReviews)
  const [error, setError] = useState<string | undefined>()

  useEffect(() => {
    if (!hasLiveReviews) {
      setReviews(generateReviews(restaurant, sampleSize))
      return
    }

    let cancelled = false
    setLoading(true)
    setError(undefined)

    fetchLiveReviews(restaurant.name, sampleSize)
      .then((result) => {
        if (!cancelled) setReviews(result)
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
  }, [restaurant, sampleSize])

  const sponsoredCount = reviews.filter((review) => review.isSponsored).length
  const sponsoredRatio = reviews.length > 0 ? Math.round((sponsoredCount / reviews.length) * 100) : 0

  return (
    <div className="mt-3 border-t border-stone-100 pt-3" onClick={(e) => e.stopPropagation()}>
      <div className="mb-2 flex items-center justify-between">
        <p className="text-xs font-medium text-stone-600">
          {hasLiveReviews ? '블로그 후기' : '최근 리뷰'} {reviews.length}개 분석 결과
        </p>
        <p className="text-xs text-stone-500">
          광고성 추정 <span className="font-semibold text-red-500">{sponsoredCount}개 ({sponsoredRatio}%)</span>
        </p>
      </div>

      {loading && <div className="py-6 text-center text-xs text-stone-400">리뷰를 불러오는 중...</div>}

      {!loading && error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-2.5 text-xs text-red-600">{error}</div>
      )}

      {!loading && !error && reviews.length === 0 && (
        <div className="py-6 text-center text-xs text-stone-400">관련 블로그 후기를 찾지 못했어요.</div>
      )}

      {!loading && !error && reviews.length > 0 && (
        <ul className="max-h-72 space-y-2 overflow-y-auto pr-1">
          {reviews.map((review) => (
            <li key={review.id} className="rounded-2xl bg-stone-50 p-2.5 text-xs">
              <div className="mb-1 flex flex-wrap items-center justify-between gap-x-2 gap-y-1">
                <span className="font-medium text-stone-700">{review.author}</span>
                <div className="flex items-center gap-1.5">
                  <span className="text-stone-400">
                    {review.dateLabel}
                    {review.rating !== undefined && ` · ★${review.rating.toFixed(1)}`}
                  </span>
                  {review.isSponsored ? (
                    <span className="shrink-0 rounded-full bg-red-50 px-2 py-0.5 font-medium text-red-500">
                      광고성
                    </span>
                  ) : (
                    <span className="shrink-0 rounded-full bg-brand-50 px-2 py-0.5 font-medium text-brand-700">
                      일반
                    </span>
                  )}
                </div>
              </div>
              <p className="text-stone-600">{review.content}</p>
              {review.link && (
                <a
                  href={review.link}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 inline-block text-brand-600 hover:underline"
                >
                  원문 보기 ↗
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
