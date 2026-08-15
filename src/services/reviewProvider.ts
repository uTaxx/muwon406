import type { Review } from '../types/restaurant'
import { classifyReview } from '../utils/reviewClassifier'

const REVIEW_WEBHOOK_URL = import.meta.env.VITE_N8N_REVIEW_WEBHOOK_URL as string | undefined

interface RawReview {
  id: string
  author: string
  content: string
  dateLabel: string
  link?: string
}

export const hasLiveReviews = Boolean(REVIEW_WEBHOOK_URL)

// n8n 웹훅이 네이버 블로그 검색으로 실제 후기 글(제목/본문 일부/작성자/링크)을 가져옵니다.
// 광고성(협찬/체험단) 여부는 이미 있는 reviewClassifier.ts 패턴으로 이 텍스트에 그대로 적용합니다.
export async function fetchLiveReviews(restaurantName: string, count: number): Promise<Review[]> {
  if (!REVIEW_WEBHOOK_URL) {
    throw new Error(
      'n8n 리뷰 웹훅 URL이 설정되지 않았습니다. VITE_N8N_REVIEW_WEBHOOK_URL 환경변수를 설정하세요.',
    )
  }

  const url = new URL(REVIEW_WEBHOOK_URL)
  url.searchParams.set('name', restaurantName)
  url.searchParams.set('display', String(count))

  const response = await fetch(url.toString())
  if (!response.ok) {
    throw new Error(`리뷰 요청 실패: ${response.status}`)
  }

  const text = await response.text()
  if (!text.trim()) return []

  const data = JSON.parse(text) as { reviews: RawReview[] }
  return (data.reviews ?? []).map((row) => ({
    id: row.id,
    author: row.author,
    content: row.content,
    dateLabel: row.dateLabel,
    link: row.link,
    isSponsored: classifyReview(row.content),
  }))
}
