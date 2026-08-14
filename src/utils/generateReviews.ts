import type { Restaurant, Review } from '../types/restaurant'
import { MAX_REVIEW_SAMPLE_SIZE } from '../types/restaurant'
import {
  SPONSORED_REVIEW_TEMPLATES,
  ORGANIC_REVIEW_TEMPLATES,
  REVIEWER_NICKNAMES,
  RELATIVE_DATE_LABELS,
} from '../data/reviewTemplates'
import { createSeededRandom } from './seededRandom'
import { classifyReview } from './reviewClassifier'

function pick<T>(pool: T[], random: () => number, avoid?: T): T {
  const choice = pool[Math.floor(random() * pool.length)]
  if (choice !== avoid || pool.length === 1) return choice
  return pool[Math.floor(random() * pool.length)]
}

function fillTemplate(template: string, restaurant: Restaurant): string {
  return template.replace('{name}', restaurant.name).replace('{category}', restaurant.category)
}

/**
 * 실제 블로그 리뷰를 수집하는 API 연동 전, 데모용으로 리뷰를 생성합니다.
 * restaurant.sponsoredReviewRatio를 광고성 템플릿이 뽑힐 확률로 사용해
 * 가게별 성향을 반영하고, 생성된 문장은 reviewClassifier로 다시 분류합니다.
 * 같은 가게 + 개수 조합이면 항상 같은 결과가 나오도록 시드 난수를 씁니다.
 */
export function generateReviews(restaurant: Restaurant, count: number): Review[] {
  const sampleSize = Math.min(Math.max(count, 0), MAX_REVIEW_SAMPLE_SIZE)
  const random = createSeededRandom(restaurant.id)
  const sponsoredProbability = Math.max(restaurant.sponsoredReviewRatio / 100, 0.05)

  const reviews: Review[] = []
  let lastTemplate: string | undefined
  for (let i = 0; i < sampleSize; i++) {
    const isSponsoredTemplate = random() < sponsoredProbability
    const template = isSponsoredTemplate
      ? pick(SPONSORED_REVIEW_TEMPLATES, random, lastTemplate)
      : pick(ORGANIC_REVIEW_TEMPLATES, random, lastTemplate)
    lastTemplate = template
    const content = fillTemplate(template, restaurant)
    const ratingJitter = (random() - 0.5) * 1.4
    const rating = Math.min(5, Math.max(1, restaurant.rating + ratingJitter))

    reviews.push({
      id: `${restaurant.id}-review-${i}`,
      author: `${pick(REVIEWER_NICKNAMES, random)}${Math.floor(random() * 90 + 10)}`,
      content,
      rating: Math.round(rating * 10) / 10,
      dateLabel: pick(RELATIVE_DATE_LABELS, random),
      isSponsored: classifyReview(content),
    })
  }

  return reviews
}
